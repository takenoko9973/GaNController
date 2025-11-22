import time

from PySide6.QtCore import QObject, QTimer, Signal, SignalInstance

from heater_amd_controller.logics.hardware_manager import HardwareManager, SensorData
from heater_amd_controller.models.protocol import SEQUENCE_NAMES, ProtocolConfig


class HCExecutionEngine(QObject):
    TIMER_INTERVAL_MS = 1000
    MIN_STEP_DURATION_SEC = 1  # ステップの最低継続時間

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
        self.timer.setInterval(self.TIMER_INTERVAL_MS)
        self.timer.timeout.connect(self._on_tick)

        self._config: ProtocolConfig | None = None

        self._start_time: float = 0.0  # プロトコル開始時刻
        self._seq_start_time: float = 0.0  # 現在のステップ開始時刻

        self._next_log_sec = 0
        self._sequence_idx = 0

    # ==== 公開操作メソッド

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

    # ==== 公開プロパティ

    @property
    def current_step_name(self) -> str:
        """現在のステップ名を取得"""
        return SEQUENCE_NAMES[self._sequence_idx % len(SEQUENCE_NAMES)]

    @property
    def current_loop_count(self) -> int:
        """現在のループ回数を取得"""
        return (self._sequence_idx // len(SEQUENCE_NAMES)) + 1

    # ==== 内部メソッド

    def _on_tick(self) -> None:
        if not self._config:
            return

        # 経過時間
        now = time.monotonic()
        seq_elapsed_sec = now - self._seq_start_time
        total_elapsed_sec = now - self._start_time

        # 測定
        data = self.hw_manager.read_all()
        self._handle_logging(data, total_elapsed_sec)

        # 通知 (UI更新用)
        self._emit_status_update(data, seq_elapsed_sec, total_elapsed_sec)

        self._check_sequence_transition(seq_elapsed_sec, total_elapsed_sec)

    def _handle_logging(self, data: SensorData, total_elapsed: float) -> None:
        """指定間隔でのログ書き込み判定"""
        if not self._config:
            return

        if total_elapsed >= self._next_log_sec:
            self._write_log(data, total_elapsed)

            interval = max(1, int(self._config.step_interval))
            self._next_log_sec += interval

    def _emit_status_update(
        self, data: SensorData, seq_elapsed: float, total_elapsed: float
    ) -> None:
        """UI更新用シグナル発信"""
        if not self._config:
            return

        # ステータス文字列作成: "1. Rising"
        status_text = f"{self._sequence_idx + 1}. {self.current_step_name}"
        self.tick_updated.emit(
            status_text, self._time_fmt(seq_elapsed), self._time_fmt(total_elapsed), data
        )

    def _check_sequence_transition(
        self, current_seq_elapsed: float, current_total_elapsed: float
    ) -> None:
        """シーケンス遷移"""
        if self._config is None:
            return

        target_hours = self._config.sequence_hours.get(self.current_step_name, 0.0)
        target_sec = max(self.MIN_STEP_DURATION_SEC, int(target_hours * 3600))

        if current_seq_elapsed >= target_sec:
            self._sequence_idx += 1
            self._seq_start_time = time.monotonic()

            # 終了判定
            if self.is_finished():
                self._finish(current_total_elapsed)

    def is_finished(self) -> bool:
        """完了判定"""
        if not self._config:
            return True

        total_steps = len(SEQUENCE_NAMES) * self._config.repeat_count
        return self._sequence_idx >= total_steps

    # === 終了・ヘルパー

    def _finish(self, final_total_sec: float) -> None:
        print("[HC Engine] Finish")
        # 最終ログ
        data = self.hw_manager.read_all()
        self._write_log(data, final_total_sec)

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

    def _write_log(self, data: SensorData, elapsed_time: float) -> None:
        # TODO: CSV書き込みクラス等に委譲
        print(f"[Log] {elapsed_time:.1f}s: Temp={data.temperature:.1f}")

    @staticmethod
    def _time_fmt(sec: float) -> str:
        m, s = divmod(int(sec), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
