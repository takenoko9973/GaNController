import datetime
import queue
import time
import traceback
from collections.abc import Callable

import pyvisa
import pyvisa.constants

from gan_controller.common.application.runner import BaseRunner
from gan_controller.common.domain.quantity import Current, Quantity, Temperature
from gan_controller.common.schemas.app_config import AppConfig
from gan_controller.features.heat_cleaning.application.hardware_controller import (
    HCHardwareFacade,
    HCHardwareMetrics,
)
from gan_controller.features.heat_cleaning.domain import Sequence
from gan_controller.features.heat_cleaning.infrastructure.hardware import (
    HCDeviceManager,
    HCDevices,
    RealHCDeviceFactory,
    SimulationHCDeviceFactory,
)
from gan_controller.features.heat_cleaning.schemas.config import ProtocolConfig
from gan_controller.features.heat_cleaning.schemas.result import HCRunnerResult


class HeatCleaningRunner(BaseRunner):
    app_config: AppConfig  # 全体設定
    protocol_config: ProtocolConfig  # 実験条件

    _request_queue: queue.Queue

    def __init__(self, app_config: AppConfig, protocol_config: ProtocolConfig) -> None:
        super().__init__()
        self.app_config = app_config  # VISAアドレスなど
        self.protocol_config = protocol_config  # 実験条件

        # データが生成されたときに呼ぶ関数リスト
        # 引数は HCRunnerResult, 戻り値は None
        self._on_step_callbacks: list[Callable[[HCRunnerResult], None]] = []

        self._request_queue = queue.Queue()  # スレッド通信用キュー

    def add_on_step_listener(self, callback: Callable[[HCRunnerResult], None]) -> None:
        """リスナー (記録係や表示係) を登録する"""
        self._on_step_callbacks.append(callback)

    # =================================================================

    def run(self) -> None:
        """実験開始"""
        tz = self.app_config.common.get_tz()
        try:
            # 設定に基づいて適切なFactoryを選択する
            is_simulation = getattr(self.app_config.common, "is_simulation_mode", False)
            factory = SimulationHCDeviceFactory() if is_simulation else RealHCDeviceFactory()

            start_time = datetime.datetime.now(tz)
            print(f"\033[32m{start_time:%Y/%m/%d %H:%M:%S} Experiment start\033[0m")

            with HCDeviceManager(factory, self.app_config.devices) as dev:
                facade = HCHardwareFacade(dev, self.app_config.devices)
                facade.setup_for_protocol(self.protocol_config)

                self._measurement_loop(facade)

        except Exception as e:
            # エラー発生時はログ出力などを行う
            print(f"Experiment Error: {e}")
            raise  # Workerスレッド側でキャッチさせるために再送出

        finally:
            finish_time = datetime.datetime.now(tz)
            print(f"\033[31m{finish_time:%Y/%m/%d %H:%M:%S} Finish\033[0m")

    # =================================================================
    # Measurement Logic
    # =================================================================

    def _measurement_loop(self, facade: HCHardwareFacade) -> None:
        """計測ループ"""
        sequences = self.protocol_config.get_sequences()
        if not sequences:
            print("No sequences found.")
            return

        print("Start Heat Cleaning measurement...")

        # 制御・ログ書き込み間隔
        interval = self.protocol_config.condition.logging_interval.base_value

        start_perf = time.perf_counter()  # 開始時間 (高分解能)
        next_target_perf = start_perf

        try:
            # メインループ
            while not self._stop:
                # タイミング調整
                current_perf = time.perf_counter()
                sleep_duration = next_target_perf - current_perf
                if sleep_duration > 0:
                    time.sleep(sleep_duration)

                next_target_perf += interval  # 次の測定時間

                # =======================================================

                total_elapsed = time.perf_counter() - start_perf

                result = self._process_step(facade, total_elapsed)

                if result is not None:
                    # 送信
                    if self.emit_result is not None:
                        self.emit_result(result)

                    # Resultを送信
                    for callback in self._on_step_callbacks:
                        callback(result)

        except Exception as e:
            print(f"\033[31m[ERROR] Measurement loop failed: {e}\033[0m")
            print(traceback.format_exc())
            raise

        finally:
            facade.emergency_stop()

    def _process_step(
        self, facade: HCHardwareFacade, total_elapsed: float
    ) -> HCRunnerResult | None:
        try:
            current_seq, seq_index, seq_elapsed = self._get_current_sequence_state(total_elapsed)
            if current_seq is not None:
                # 電流値設定
                self._control_devices(facade, current_seq, seq_elapsed)
            else:
                # 終了した場合
                print("All sequences finished.")
                self._stop = True

            time.sleep(0.1)  # 電流変化後の安定化用

            # 測定
            metrics = facade.read_metrics()
            return self._create_result(metrics, total_elapsed, seq_elapsed, current_seq, seq_index)

        except pyvisa.errors.VisaIOError as e:
            # 装置に関するエラー
            self._handle_visa_error(e)
            return None

    def _get_current_sequence_state(
        self, total_elapsed: float
    ) -> tuple[Sequence | None, int, float]:
        """現在の経過時間から、該当するシーケンスとその中での経過時間を返す

        Returns:
            (Sequenceオブジェクト, シーケンス番号, シーケンス内経過時間[s])

        """
        sequences = self.protocol_config.get_sequences()
        if not sequences:
            return None, -1, 0.0

        # シーケンスごとの累積時間
        accumulated_time = 0.0

        for i, seq in enumerate(sequences):
            duration = seq.duration_sec

            # まだこのシーケンスの範囲内か
            if total_elapsed < (accumulated_time + duration):
                seq_elapsed = total_elapsed - accumulated_time
                return seq, i, seq_elapsed

            accumulated_time += duration

        # 全シーケンス時間を超えている場合
        return None, -1, 0.0

    def _control_devices(self, facade: HCHardwareFacade, seq: Sequence, seq_elapsed: float) -> None:
        """シーケンス定義に従ってデバイス(電源)を制御"""
        hc_target_current = None
        amd_target_current = None

        # HC電源の制御
        if self.protocol_config.condition.hc_enabled:
            # 現在の目標電流値を計算
            hc_max_current = self.protocol_config.condition.hc_current
            hc_target_current = Current(seq.current(hc_max_current.base_value, seq_elapsed))

        # AMD電源の制御
        if self.protocol_config.condition.amd_enabled:
            amd_max_current = self.protocol_config.condition.amd_current
            amd_target_current = Current(seq.current(amd_max_current.base_value, seq_elapsed))

        facade.set_condition(hc_target_current, amd_target_current)

    def _create_result(
        self,
        metrics: HCHardwareMetrics,
        total_elapsed: float,
        seq_elapsed: float,
        current_seq: Sequence | None,
        current_idx: int,
    ) -> HCRunnerResult:
        seq_name = current_seq.mode_name if current_seq else "Finish"

        # ケース温度 (無効化の場合はnan)
        if not self.protocol_config.log.record_pyrometer:
            metrics.case_temperature = Temperature(float("nan"))

        return HCRunnerResult(
            current_sequence_index=current_idx + 1,
            current_sequence_name=seq_name,
            step_timestamp=Quantity(seq_elapsed, "s"),
            total_timestamp=Quantity(total_elapsed, "s"),
            ext_pressure=metrics.ext_pressure,
            sip_pressure=metrics.sip_pressure,
            case_temperature=metrics.case_temperature,
            hc_electricity=metrics.hc_electricity,
            amd_electricity=metrics.amd_electricity,
        )

    def _handle_visa_error(self, e: pyvisa.errors.VisaIOError) -> None:
        """VISAエラーのハンドリング"""
        if e.error_code == pyvisa.constants.VI_ERROR_TMO:
            print(f"\033[33m[WARNING] Device Timeout occurred. Retrying... ({e})\033[0m")
            # タイムアウト時は続行 (呼び出し元のループが継続する)
        else:
            # それ以外は再送出
            raise e

    def _finalize_safety(self, devices: HCDevices) -> None:
        """終了処理"""
        print("Executing safety cleanup...")

        try:
            devices.hps.set_output(False)
        except Exception as cleanup_err:  # noqa: BLE001
            print(f"Failed to stop HPS: {cleanup_err}")

        try:
            devices.aps.set_output(False)
        except Exception as cleanup_err:  # noqa: BLE001
            print(f"Failed to stop APS: {cleanup_err}")
