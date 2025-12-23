import datetime
import time

from PySide6.QtCore import QObject, QTimer, Signal, SignalInstance, Slot

from heater_amd_controller.logics.hardware_manager import HardwareManager, SensorData
from heater_amd_controller.logics.hc_logger import HCLogger
from heater_amd_controller.models.protocol_config import ProtocolConfig
from heater_amd_controller.models.sequence import Sequence, SequenceMode
from heater_amd_controller.utils.log_file import LogManager

TZ = datetime.timezone(datetime.timedelta(hours=8))


class HCExecutionEngine(QObject):
    """Heat Cleaning 実行エンジン"""

    TIMER_INTERVAL_MS = 1000
    MIN_STEP_DURATION_SEC = 1  # ステップの最低継続時間

    # 毎秒の更新通知 (状態テキスト, ステップ時間, トータル時間, 測定データ)
    monitor_updated = Signal(str, float, float, SensorData)
    graph_updated = Signal(float, SensorData)  # グラフ更新
    # 終了シグナル (最終トータル時間)
    sequence_finished = Signal(float)
    sequence_stopped = Signal(float)
    # ログファイル生成シグナル (ログファイル名)
    log_initialized = Signal(str)

    def __init__(self, hw_manager: HardwareManager) -> None:
        super().__init__()
        self.hw_manager = hw_manager

        # タイマーセットアップ
        self.timer = QTimer(self)
        self.timer.setInterval(self.TIMER_INTERVAL_MS)
        self.timer.timeout.connect(self._on_tick)

        self._config: ProtocolConfig | None = None
        self._sequence_objects: list[Sequence] = []

        self._logger: HCLogger | None = None

        self._start_time: float = 0.0  # プロトコル開始時刻
        self._seq_start_time: float = 0.0  # 現在のステップ開始時刻

        self._next_log_sec = 0
        self._sequence_idx = 0
        self._current_loop = 1

    # ================================================
    # 公開操作メソッド
    # ================================================

    def start(self, protocol_config: ProtocolConfig) -> None:
        print("[HC Engine] Start")
        start_time = datetime.datetime.now(TZ)

        self.hw_manager.connect_devices()

        self._config = protocol_config  # プロトコル設定を保存
        self._sequence_objects = self._create_sequence_objects(protocol_config)

        if not self._sequence_objects:
            # もし有効なステップが一つもない場合は即終了
            self._finish(0)
            return

        # ログ準備
        try:
            log_manager = LogManager()
            date_dir = log_manager.get_date_directory(date_update=protocol_config.log_date_update)
            log_file = date_dir.create_logfile(
                protocol_config.name, major_update=protocol_config.log_major_update
            )

            self._logger = HCLogger(log_file, protocol_config)
            self._logger.write_header(start_time, self._sequence_objects)
            self.log_initialized.emit(log_file.path.stem)

        except Exception as e:  # noqa: BLE001
            print(f"Log creation failed: {e}")
            self.stop()
            return

        now = time.monotonic()
        self._start_time = now
        self._seq_start_time = now

        self._next_log_sec = 0
        self._sequence_idx = 0
        self._current_loop = 1

        self.timer.start()
        self._on_tick()  # 初回即時更新

    def stop(self) -> None:
        print("[HC Engine] Stop")

        current_total_sec = 0
        if self._start_time > 0:
            current_total_sec = time.monotonic() - self._start_time

        self._end_session(self.sequence_stopped, current_total_sec)

    def _create_sequence_objects(self, protocol_config: ProtocolConfig) -> list[Sequence]:
        """設定からSequenceのリスト作成"""
        objects = []

        for mode in SequenceMode:
            # 設定時間 (hour) -> 秒
            hours = protocol_config.sequence_hours.get(mode.value, 0.0)
            duration_sec = int(hours * 3600)

            if duration_sec <= 0:  # 0秒以下ならスキップ
                continue

            # クラスを取得、インスタンス化
            seq_obj = Sequence.create(mode, duration_sec, 0.33)
            if seq_obj:
                objects.append(seq_obj)

        return objects

    # ================================================
    # 公開プロパティ
    # ================================================

    @property
    def current_sequence(self) -> Sequence | None:
        """現在のシーケンスをを取得"""
        if 0 <= self._sequence_idx < len(self._sequence_objects):
            return self._sequence_objects[self._sequence_idx]

        return None

    # ================================================
    # 内部メソッド
    # ================================================

    @Slot()
    def _on_tick(self) -> None:
        """tick毎の処理"""
        if not self._config or not self.current_sequence:
            return

        # 経過時間
        now = time.monotonic()
        total_elapsed_sec = now - self._start_time
        seq_elapsed_sec = now - self._seq_start_time

        # ログ間隔判定
        is_log_interval = total_elapsed_sec >= self._next_log_sec
        if is_log_interval:
            # 次のログ保存時刻を更新
            interval = max(1, int(self._config.step_interval))
            self._next_log_sec += interval

        # ================= tick毎の処理パイプライン =================

        # 1. 電流値設定
        if is_log_interval:
            self._set_current(seq_elapsed_sec)

        # 2. 測定
        data = self.hw_manager.read_all()

        # 3. ログ処理
        if is_log_interval:
            self._write_log(data, total_elapsed_sec)
            self.graph_updated.emit(total_elapsed_sec, data)

        # 4. 通知 (UI更新用)
        self._emit_status_update(data, seq_elapsed_sec, total_elapsed_sec)

        # シーケンス進行判定
        if seq_elapsed_sec >= self.current_sequence.duration_second:
            # ステップ終了時も最後に値をセット
            self._set_current(self.current_sequence.duration_second)
            self._advance_step(total_elapsed_sec)

    def _set_current(self, seq_elapsed_sec: float) -> None:
        """指定時間での電流値設定"""
        if not self._config or not self.current_sequence:
            return

        # 現在のシーケンスに基づいて、設定電流値を計算
        if self._config.hc_enabled:
            hc_target = self.current_sequence.current(self._config.hc_current, seq_elapsed_sec)
            self.hw_manager.set_hc_current(hc_target)

        if self._config.amd_enabled:
            amd_target = self.current_sequence.current(self._config.amd_current, seq_elapsed_sec)
            self.hw_manager.set_amd_current(amd_target)

    def _emit_status_update(
        self, data: SensorData, seq_elapsed: float, total_elapsed: float
    ) -> None:
        """UI更新用シグナル発信"""
        if not self._config or not self.current_sequence:
            return

        # ステータス文字列作成: "1. Rising"
        ong_loop_len = len(self._sequence_objects)
        seq_num = ong_loop_len * (self._current_loop - 1) + self._sequence_idx + 1
        seq_name = self.current_sequence.mode_name
        status_text = f"{seq_num}. {seq_name}"

        self.monitor_updated.emit(status_text, seq_elapsed, total_elapsed, data)

    def _advance_step(self, total_elapsed: float) -> None:
        """次のステップへ進む"""
        self._sequence_idx += 1

        # リストの最後まで行ったらループ処理
        if self._sequence_idx >= len(self._sequence_objects):
            self._sequence_idx = 0
            self._current_loop += 1

        self._seq_start_time = time.monotonic()

        if self.is_finished():
            self._finish(total_elapsed)

    def is_finished(self) -> bool:
        """完了判定"""
        if not self._config or not self._sequence_objects:
            return True

        # ループ回数が設定を超えたら終了
        return self._current_loop > self._config.repeat_count

    # ================================================
    # 終了・ヘルパー
    # ================================================

    def _finish(self, final_total_sec: float) -> None:
        print("[HC Engine] Finish")
        # 最終ログ
        data = self.hw_manager.read_all()
        self._write_log(data, final_total_sec)

        self._end_session(self.sequence_finished, final_total_sec)

    def _write_log(self, data: SensorData, elapsed_time: float) -> None:
        """ログ保存処理"""
        if self._logger:
            self._logger.write_record(elapsed_time, data)
            print(f"[Log] {elapsed_time:.1f}s: Temp={data.temperature:.1f}")

    def _end_session(self, signal_to_emit: SignalInstance, total_sec: float) -> None:
        """停止・完了の後処理"""
        # 後処理
        self.timer.stop()  # タイマー停止
        self.hw_manager.disconnect_devices()  # 装置切断
        # 設定破棄
        self._config = None
        self._sequence_objects = []

        self._logger = None

        # 指定されたシグナルを発信 (stop or finish)
        signal_to_emit.emit(total_sec)
