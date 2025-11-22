import time

from PySide6.QtCore import QObject, QTimer, Signal, SignalInstance

from heater_amd_controller.logics.hardware_manager import HardwareManager, SensorData
from heater_amd_controller.models.protocol import SEQUENCE_NAMES, ProtocolConfig


class HCExecutionEngine(QObject):
    # ===== シグナル
    # 毎秒の更新通知 (状態テキスト, ステップ時間, トータル時間, 測定データ)
    tick_updated = Signal(str, str, str, SensorData)

    # 終了シグナル (最終トータル時間)
    finished = Signal(str)
    stopped = Signal(str)

    def __init__(self, hw_manager: HardwareManager) -> None:
        super().__init__()
        self.hw_manager = hw_manager

        # タイマーセットアップ
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._on_tick)

        self._config: ProtocolConfig | None = None

        self._start_time: float = 0.0  # プロトコル開始時刻
        self._seq_start_time: float = 0.0  # 現在のステップ開始時刻

        self._next_log_sec = 0
        self._sequence_idx = 0

    def start(self, config: ProtocolConfig) -> None:
        print("[HC Engine] Start")
        self.hw_manager.connect_devices()

        self._config = config  # プロトコル設定を保存

        now = time.monotonic()
        self._start_time = now
        self._seq_start_time = now

        self._next_log_sec = 0
        self._sequence_idx = 0

        self.timer.start()
        self._on_tick()  # 初回即時更新

    def stop(self) -> None:
        print("[HC Engine] Stop")

        current_total_sec = 0
        if self._start_time > 0:
            current_total_sec = time.monotonic() - self._start_time

        self._end_session(self.stopped, current_total_sec)

    def _finish(self, final_total_sec: float) -> None:
        print("[HC Engine] Finish")
        # 最終ログ
        data = self.hw_manager.read_all()
        self._log_data(data, final_total_sec)

        self._end_session(self.finished, final_total_sec)

    def _end_session(self, signal_to_emit: SignalInstance, total_sec: float) -> None:
        """停止・完了の後処理"""
        # 後処理
        self.timer.stop()  # タイマー停止
        self.hw_manager.disconnect_devices()  # 装置切断
        self._config = None  # 設定破棄

        # 指定されたシグナルを発信 (stop or finish)
        time_str = self._time_fmt(total_sec)
        signal_to_emit.emit(time_str)

    def _on_tick(self) -> None:
        if not self._config:
            return

        # 経過時間
        now = time.monotonic()
        total_elapsed_sec = now - self._start_time
        seq_elapsed_sec = now - self._seq_start_time

        # 測定
        data = self.hw_manager.read_all()

        # ログ判定・書き込み
        if total_elapsed_sec >= self._next_log_sec:
            self._log_data(data, total_elapsed_sec)
            interval = max(1, int(self._config.step_interval))
            self._next_log_sec += interval

        # 通知 (UI更新用)
        status_text = self._get_status_text()
        step_str = self._time_fmt(seq_elapsed_sec)
        total_str = self._time_fmt(total_elapsed_sec)
        self.tick_updated.emit(status_text, step_str, total_str, data)

        self._check_sequence(seq_elapsed_sec, total_elapsed_sec)

    def _check_sequence(self, current_seq_elapsed: float, current_total_elapsed: float) -> None:
        """シーケンス遷移"""
        if self._config is None:
            return

        step_len = len(SEQUENCE_NAMES)
        current_name = SEQUENCE_NAMES[self._sequence_idx % step_len]

        sequence_duration_hours = self._config.sequence_hours.get(current_name, 0.0)
        sequence_duration_sec = max(10, int(sequence_duration_hours * 3600))

        if current_seq_elapsed >= sequence_duration_sec:
            self._sequence_idx += 1
            self._seq_start_time = time.monotonic()

            # 終了判定
            total_steps = step_len * self._config.repeat_count
            if self._sequence_idx >= total_steps:
                self._finish(current_total_elapsed)

    def _log_data(self, data: SensorData, elapsed_time: float) -> None:
        # TODO: CSV書き込みクラス等に委譲
        print(f"[Log] {elapsed_time:.1f}s: Temp={data.temperature:.1f}")

    def _get_status_text(self) -> str:
        """現在のシーケンスとシーケンス番号を取得"""
        if not self._config:
            return "停止"

        step_len = len(SEQUENCE_NAMES)
        name = SEQUENCE_NAMES[self._sequence_idx % step_len]

        return f"{self._sequence_idx + 1}. {name}"

    def _time_fmt(self, sec: float) -> str:
        m, s = divmod(int(sec), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
