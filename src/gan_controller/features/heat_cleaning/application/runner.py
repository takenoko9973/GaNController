import datetime
import time
import traceback

import pyvisa
import pyvisa.constants

from gan_controller.core.constants import JST
from gan_controller.core.models.quantity import Current, Time
from gan_controller.features.heat_cleaning.domain.config import ProtocolConfig
from gan_controller.features.heat_cleaning.domain.interface import IHCHardwareFacade
from gan_controller.features.heat_cleaning.domain.models import HCExperimentResult, Sequence
from gan_controller.features.heat_cleaning.infrastructure.hardware import HCHardwareBackend
from gan_controller.features.heat_cleaning.infrastructure.persistence import HCLogRecorder
from gan_controller.presentation.async_runners.runner import ExperimentRunner


class HeatCleaningRunner(ExperimentRunner):
    _backend: HCHardwareBackend
    _recorder: HCLogRecorder
    _config: ProtocolConfig

    def __init__(
        self, backend: HCHardwareBackend, recorder: HCLogRecorder, config: ProtocolConfig
    ) -> None:
        super().__init__()
        self._backend = backend
        self._recorder = recorder
        self._config = config

    # =================================================================
    # Main Execution Flow
    # =================================================================

    def run(self) -> None:
        """実験開始"""
        start_time = datetime.datetime.now(JST)
        self._recorder.record_header(start_time)
        print(f"\033[32m{start_time:%Y/%m/%d %H:%M:%S} Start\033[0m")

        try:
            with self._backend as facade:
                # 初期設定 (Facade経由)
                facade.setup_for_protocol(self._config)

                # シーケンス実行ループへ
                self._execute_sequences(facade)

        except Exception as e:
            print(f"\033[31mExperiment Error: {e}\033[0m")
            print(traceback.format_exc())
            raise

        finally:
            finish_time = datetime.datetime.now(JST)
            print(f"\033[31m{finish_time:%Y/%m/%d %H:%M:%S} Finish\033[0m")

            self.finished.emit()

    def _execute_sequences(self, facade: IHCHardwareFacade) -> None:
        # シーケンスの取得
        sequences = self._config.get_sequences()
        if not sequences:
            print("No sequences found.")
            return

        # 実験開始
        total_start_time = time.perf_counter()

        # 各シーケンスを順番に実行
        for i, seq in enumerate(sequences):
            # 停止フラグが立っていたらループを抜ける
            if self.isInterruptionRequested():
                print("Experiment stopped by user.")
                break

            print(f"Starting Sequence {i + 1}: {seq.mode_name}")
            self._run_single_sequence(i + 1, seq, total_start_time, facade)

    def _run_single_sequence(
        self, seq_index: int, seq: Sequence, total_start_time: float, facade: IHCHardwareFacade
    ) -> None:
        """1つのシーケンスを実行するループ"""
        # ログ設定からインターバルを取得 (なければデフォルト10s)
        interval = self._get_interval()

        # シーケンス開始時間
        seq_start_time = time.perf_counter()
        next_target_perf = seq_start_time

        while not self.isInterruptionRequested():
            # タイミング調整
            self._wait_for_next_tick(next_target_perf)
            next_target_perf += interval  # 次の時刻更新

            # 時間計測
            now = time.perf_counter()  # sleep後の正確な時間
            seq_elapsed = now - seq_start_time
            total_elapsed = now - total_start_time

            # 処理実行
            self._control_hardware(seq, seq_elapsed, facade)
            result = self._create_result(seq_index, seq, seq_elapsed, total_elapsed, facade)

            # Result 処理
            if result:
                # 画面更新用シグナル
                self.step_result_observed.emit(result)

                # ログ書き込み
                self._recorder.record_data(result)

            # 終了判定
            if seq_elapsed >= seq.duration_sec:
                break

    def _control_hardware(
        self, seq: Sequence, seq_elapsed: float, facade: IHCHardwareFacade
    ) -> None:
        """1ステップ分の制御を行う"""
        try:
            # 目標電流値の計算
            # Conditionの設定値 (最大電流) をConfigから取得
            max_hc = (
                self._config.condition.hc_current.base_value
                if self._config.condition.hc_enabled
                else 0.0
            )
            max_amd = (
                self._config.condition.amd_current.base_value
                if self._config.condition.amd_enabled
                else 0.0
            )

            target_hc = seq.calculate_current(max_hc, seq_elapsed)
            target_amd = seq.calculate_current(max_amd, seq_elapsed)

            # ハードウェア制御 (Interface経由)
            facade.set_currents(Current(target_hc), Current(target_amd))
            time.sleep(0.1)  # 安定化時間

        except pyvisa.errors.VisaIOError as e:
            # 装置に関するエラー
            self._handle_visa_error(e)

    def _create_result(
        self,
        seq_index: int,
        seq: Sequence,
        seq_elapsed: float,
        total_elapsed: float,
        facade: IHCHardwareFacade,
    ) -> HCExperimentResult | None:
        """1ステップ分の測定を行う"""
        try:
            result = facade.read_metrics()

            # Resultにコンテキスト情報 (時間やシーケンス名) を付与
            result.sequence_index = seq_index
            result.sequence_name = seq.mode_name
            result.timestamp_step = Time(seq_elapsed)
            result.timestamp_total = Time(total_elapsed)
            return result

        except pyvisa.errors.VisaIOError as e:
            # 装置に関するエラー
            self._handle_visa_error(e)
            return None

    def _get_interval(self) -> float:
        val = self._config.condition.logging_interval.base_value
        return val if val > 0 else 10.0

    def _wait_for_next_tick(self, target_perf: float) -> None:
        sleep_duration = target_perf - time.perf_counter()
        if sleep_duration > 0:
            time.sleep(sleep_duration)

    def _handle_visa_error(self, e: pyvisa.errors.VisaIOError) -> None:
        """VISAエラーのハンドリング"""
        if e.error_code == pyvisa.constants.VI_ERROR_TMO:
            print(f"\033[33m[WARNING] Device Timeout occurred. Retrying... ({e})\033[0m")
            # タイムアウト時は続行 (呼び出し元のループが継続する)
        else:
            # それ以外は再送出
            raise e
