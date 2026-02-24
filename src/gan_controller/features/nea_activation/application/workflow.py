import datetime
import queue
import time

import pyvisa
import pyvisa.constants

from gan_controller.core.constants import JST
from gan_controller.features.nea_activation.domain.config import NEAConfig, NEAControlConfig
from gan_controller.features.nea_activation.domain.interface import INEAHardwareFacade
from gan_controller.features.nea_activation.domain.models import NEAExperimentResult
from gan_controller.features.nea_activation.infrastructure.hardware.backend import (
    NEAHardwareBackend,
)
from gan_controller.features.nea_activation.infrastructure.persistence.recorder import (
    NEALogRecorder,
)
from gan_controller.presentation.async_runners.interfaces import (
    IExperimentObserver,
    IExperimentWorkflow,
)


class NEAActivationWorkflow(IExperimentWorkflow):
    _backend: NEAHardwareBackend
    _recorder: NEALogRecorder
    _config: NEAConfig

    _request_queue: queue.Queue  # スレッド通信用キュー

    def __init__(
        self,
        backend: NEAHardwareBackend,
        recorder: NEALogRecorder,
        config: NEAConfig,
        request_queue: queue.Queue,  # パラメータ更新用
    ) -> None:
        self._backend = backend
        self._recorder = recorder
        self._config = config

        self._request_queue = request_queue

        self._observer: IExperimentObserver | None = None

    def execute(self, observer: IExperimentObserver) -> None:
        """メインループ"""
        self._observer = observer

        try:
            start_time = datetime.datetime.now(JST)
            self._recorder.record_header(start_time)
            print(f"\033[32m{start_time:%Y/%m/%d %H:%M:%S} Experiment start\033[0m")

            # backendのコンテキスト管理
            with self._backend, self._backend.get_facade() as facade:
                self._measurement_loop(facade)

        finally:
            finish_time = datetime.datetime.now(JST)
            print(f"\033[31m{finish_time:%Y/%m/%d %H:%M:%S} Finish\033[0m")

            self._observer.on_finished()

    def _measurement_loop(self, facade: INEAHardwareFacade) -> None:
        """計測ループ"""
        start_perf = time.perf_counter()  # 開始時間 (高分解能)

        # メインループ
        while not self._should_stop():
            try:
                # 1ステップ分実行
                success = self._execute_single_measurement(facade, start_perf)
                if not success:
                    break

            except pyvisa.errors.VisaIOError as e:
                self._handle_visa_error(e)

    # =================================================================
    # Observer ヘルパーメソッド
    # =================================================================

    def _should_stop(self) -> bool:
        """中断要求が来ているかチェック"""
        # Observerがなければ強制停止
        if self._observer is None:
            return True

        return self._observer.is_interruption_requested()

    def _notify_message(self, message: str) -> None:
        """メッセージ通知"""
        if self._observer:
            self._observer.on_message(message)

    def _notify_result(self, result: NEAExperimentResult) -> None:
        """結果通知"""
        if self._observer:
            self._observer.on_step_completed(result)

    # =================================================================
    # 内部ロジック
    # =================================================================

    def _execute_single_measurement(self, facade: INEAHardwareFacade, start_perf: float) -> bool:
        """
        1回分の測定サイクルを実行

        Returns:
            bool: 測定が完了したらTrue, 中断されたらFalse

        """
        elapsed_perf = time.perf_counter() - start_perf
        self._process_pending_requests(facade, elapsed_perf)  # 設定に変更があるか確認

        print("\033[32m" + f"{elapsed_perf:.1f}[s]\t" + "\033[0m")

        cond = self._config.condition
        stabilization_time = cond.stabilization_time.base_value
        shunt_r = cond.shunt_resistance
        count = int(cond.integration_count.base_value)
        interval = cond.integration_interval.base_value

        # 出力状態測定 (Bright)
        facade.set_laser_emission(True)  # レーザー出力開始
        # 安定するまで待機
        if not self._wait_interruptable(stabilization_time):
            return False  # 待機中に中断されたら終了
        bright_pc_volt, bright_pc = facade.read_photocurrent(shunt_r, count, interval)

        # バックグラウンド測定 (Dark)
        facade.set_laser_emission(False)
        if not self._wait_interruptable(stabilization_time):
            return False
        dark_pc_volt, dark_pc = facade.read_photocurrent(shunt_r, count, interval)

        result = facade.read_metrics(
            control_config=self._config.control,
            condition_config=self._config.condition,
            timestamp=elapsed_perf,
            bright_pc=bright_pc,
            bright_pc_voltage=bright_pc_volt,
            dark_pc=dark_pc,
            dark_pc_voltage=dark_pc_volt,
        )

        qe = result.quantum_efficiency
        pc = result.photocurrent
        print(f"{qe:.3e}, {pc:.3e}, {result.ext_pressure:.2e} (EXT)")

        self._recorder.record_data(result, "")
        self._notify_result(result)

        return True

    def _process_pending_requests(self, facade: INEAHardwareFacade, elapsed_perf: float) -> None:
        latest_config = self._get_latest_config_from_queue()

        if latest_config is not None:
            amd_current = latest_config.amd_output_current
            laser_power = latest_config.laser_power_sv
            msg = (
                f"[{elapsed_perf:.1f}s] Parameters Updated: AMD = {amd_current},"
                f"Laser = {laser_power}"
            )
            print(msg)

            facade.apply_control_params(latest_config)
            self._config.control = latest_config

            self._notify_message(msg)

    # =================================================================

    def _wait_interruptable(self, duration_sec: float) -> bool:
        """
        指定時間待機する。中断フラグが立ったら即座に終了する。

        Args:
            duration_sec (float): 待機する秒数

        Returns:
            bool: 待機が完了した場合はTrue、中断された場合はFalse

        """
        check_interval = 0.1  # チェック間隔 [s]
        start_perf = time.perf_counter()

        while True:
            # 経過時間をチェック
            elapsed = time.perf_counter() - start_perf
            remaining = duration_sec - elapsed

            if remaining <= 0:
                return True  # 待機完了

            # 中断フラグチェック
            if self._should_stop():
                return False  # 中断された

            # 次のチェックまでのスリープ (残り時間とインターバルの短い方)
            time.sleep(min(check_interval, remaining))

    def _handle_visa_error(self, e: pyvisa.errors.VisaIOError) -> None:
        """VISAエラーのハンドリング"""
        if e.error_code == pyvisa.constants.VI_ERROR_TMO:
            print(f"\033[33m[WARNING] Device Timeout occurred. Retrying... ({e})\033[0m")
            # タイムアウト時は続行 (呼び出し元のループが継続する)
        else:
            # それ以外は再送出
            raise e

    # =================================================================

    def _get_latest_config_from_queue(self) -> NEAControlConfig | None:
        """キューから最新の設定を取り出す"""
        if self._request_queue.empty():
            return None

        latest_params = None
        while not self._request_queue.empty():
            try:
                latest_params = self._request_queue.get_nowait()
            except queue.Empty:
                break

        return latest_params
