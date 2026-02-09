import datetime
import time
import traceback
from collections.abc import Callable

import pyvisa
import pyvisa.constants

from gan_controller.common.application.runner import BaseRunner
from gan_controller.common.domain.quantity import Current, Time
from gan_controller.common.schemas.app_config import AppConfig
from gan_controller.features.heat_cleaning.domain.config import ProtocolConfig
from gan_controller.features.heat_cleaning.domain.interface import IHeatCleaningHardware
from gan_controller.features.heat_cleaning.domain.models import HCExperimentResult, Sequence


class HeatCleaningRunner(BaseRunner):
    _hw: IHeatCleaningHardware
    _config: ProtocolConfig

    def __init__(self, hardware: IHeatCleaningHardware, config: ProtocolConfig) -> None:
        super().__init__()
        self._hw = hardware
        self._config = config

        # データ生成時のコールバック (引数: ExperimentResult)
        self._on_step_callbacks: list[Callable[[HCExperimentResult], None]] = []

    def add_on_step_listener(self, callback: Callable[[HCExperimentResult], None]) -> None:
        """リスナー (記録係や表示係) を登録する"""
        self._on_step_callbacks.append(callback)

    # =================================================================
    # Main Execution Flow
    # =================================================================

    def run(self) -> None:
        """実験開始"""
        app_config = AppConfig.load()
        tz = app_config.common.get_tz()
        print(f"Experiment started at {datetime.datetime.now(tz)}")

        try:
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
                if self._stop:
                    print("Experiment stopped by user.")
                    break

                print(f"Starting Sequence {i + 1}: {seq.mode_name}")
                self._run_single_sequence(i + 1, seq, total_start_time)

        except Exception as e:
            print(f"\033[31mExperiment Error: {e}\033[0m")
            print(traceback.format_exc())
            raise

        finally:
            self._hw.emergency_stop()  # 装置の停止処理

            finish_time = datetime.datetime.now(tz)
            print(f"\033[31m{finish_time:%Y/%m/%d %H:%M:%S} Finish\033[0m")

    def _run_single_sequence(self, seq_index: int, seq: Sequence, total_start_time: float) -> None:
        """1つのシーケンスを実行するループ"""
        # ログ設定からインターバルを取得 (なければデフォルト10s)
        interval = self._config.condition.logging_interval.base_value
        if interval <= 0:
            interval = 10

        # シーケンス開始時間
        seq_start_time = time.perf_counter()
        next_target_perf = seq_start_time

        while not self._stop:
            # --- タイミング調整 ---
            now = time.perf_counter()
            sleep_duration = next_target_perf - now  # 測定予定時間と現在時間との差分を計算
            if sleep_duration > 0:
                time.sleep(sleep_duration)  # 予定時間まで待機

            # 次の時刻更新
            next_target_perf += interval

            # --- 時間計測 ---
            now = time.perf_counter()  # sleep後の正確な時間
            seq_elapsed = now - seq_start_time
            total_elapsed = now - total_start_time

            # シーケンス終了判定
            # (最後に1回だけdurationを超えた状態で実行して、次のシーケンスへ行く)
            is_seq_finished = seq_elapsed >= seq.duration_sec

            # --- 処理実行 ---
            result = self._process_step(
                seq_index=seq_index, seq=seq, seq_elapsed=seq_elapsed, total_elapsed=total_elapsed
            )

            # --- 通知 ---
            if result:
                # 画面更新用シグナル (BaseRunnerの機能を使用する場合)
                if self.emit_result is not None:
                    self.emit_result(result)

                # ログ記録用コールバック
                for callback in self._on_step_callbacks:
                    callback(result)

            if is_seq_finished:
                break

    def _process_step(
        self, seq_index: int, seq: Sequence, seq_elapsed: float, total_elapsed: float
    ) -> HCExperimentResult | None:
        """1ステップ分の制御と測定を行う"""
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
            self._hw.set_currents(Current(target_hc), Current(target_amd))
            time.sleep(0.1)  # 安定化時間

            # 測定
            result = self._hw.read_metrics()

            # Resultにコンテキスト情報 (時間やシーケンス名) を付与
            result.sequence_index = seq_index
            result.sequence_name = seq.mode_name
            result.timestamp_step = Time(seq_elapsed)
            result.timestamp_total = Time(total_elapsed)

        except pyvisa.errors.VisaIOError as e:
            # 装置に関するエラー
            self._handle_visa_error(e)
            return None

        else:
            return result

    def _handle_visa_error(self, e: pyvisa.errors.VisaIOError) -> None:
        """VISAエラーのハンドリング"""
        if e.error_code == pyvisa.constants.VI_ERROR_TMO:
            print(f"\033[33m[WARNING] Device Timeout occurred. Retrying... ({e})\033[0m")
            # タイムアウト時は続行 (呼び出し元のループが継続する)
        else:
            # それ以外は再送出
            raise e
