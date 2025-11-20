from PySide6.QtCore import QObject, QTimer, Signal

from heater_amd_controller.logics.hardware_manager import HardwareManager, SensorData
from heater_amd_controller.models.protocol import SEQUENCE_NAMES, ProtocolConfig


class HCExecutionEngine(QObject):
    # 毎秒の更新通知 (状態テキスト, ステップ時間, トータル時間, 測定データ)
    tick_updated = Signal(str, str, str, SensorData)
    # 完了通知
    finished = Signal(str)  # 最終トータル時間
    # 停止通知
    stopped = Signal(str)

    def __init__(self, hw_manager: HardwareManager) -> None:
        super().__init__()
        self.hw_manager = hw_manager

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._on_tick)

        self._config: ProtocolConfig | None = None
        self._total_sec = 0
        self._sequence_sec = 0
        self._next_log_sec = 0
        self._sequence_idx = 0

    def start(self, config: ProtocolConfig) -> None:
        print("[HC Engine] Start")
        self.hw_manager.connect_devices()

        self._config = config  # プロトコル設定を保存
        self._total_sec = 0
        self._sequence_sec = 0
        self._sequence_idx = 0
        self._next_log_sec = 0

        self.timer.start()
        # self._on_tick()  # 初回即時更新

    def stop(self) -> None:
        print("[HC Engine] Stop")
        self.timer.stop()
        self.hw_manager.disconnect_devices()
        self._config = None

        final_total_str = self._fmt(self._total_sec)
        self.stopped.emit(final_total_str)

    def _on_tick(self) -> None:
        if not self._config:
            return

        # 測定
        data = self.hw_manager.read_all()

        # ログ判定・書き込み
        if self._total_sec >= self._next_log_sec:
            self._log_data(data)
            interval = max(1, int(self._config.step_interval))
            self._next_log_sec += interval

        # 通知 (UI更新用)
        status_text = self._get_status_text()
        step_str = self._fmt(self._sequence_sec)
        total_str = self._fmt(self._total_sec)
        self.tick_updated.emit(status_text, step_str, total_str, data)

        # 時間進行 & 遷移チェック
        self._total_sec += 1
        self._sequence_sec += 1

        self._check_sequence()

    def _check_sequence(self) -> None:
        """シーケンス遷移"""
        if self._config is None:
            return

        step_len = len(SEQUENCE_NAMES)
        current_name = SEQUENCE_NAMES[self._sequence_idx % step_len]

        sequence_duration_hours = self._config.sequence_hours.get(current_name, 0.0)
        sequence_duration_sec = max(1, int(sequence_duration_hours * 3600))

        if self._sequence_sec >= sequence_duration_sec:
            self._sequence_sec = 0
            self._sequence_idx += 1

            # 終了判定
            total_steps = step_len * self._config.repeat_count
            if self._sequence_idx >= total_steps:
                self._finish()

    def _finish(self) -> None:
        self.timer.stop()
        self.hw_manager.disconnect_devices()

        # 最終的な合計時間を通知
        final_total_str = self._fmt(self._total_sec)
        self.finished.emit(final_total_str)

        self._config = None

    def _log_data(self, data: SensorData) -> None:
        # TODO: CSV書き込みクラス等に委譲
        print(f"[Log] {self._total_sec}s: Temp={data.temperature:.1f}")

    def _get_status_text(self) -> str:
        if not self._config:
            return "停止"
        step_len = len(SEQUENCE_NAMES)
        loop = (self._sequence_idx // step_len) + 1
        name = SEQUENCE_NAMES[self._sequence_idx % step_len]
        return f"{loop}. {name}"

    def _fmt(self, sec: int) -> str:
        m, s = divmod(int(sec), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
