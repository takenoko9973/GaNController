import time

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from heater_amd_controller.logics.hardware_manager import HardwareManager
from heater_amd_controller.models.nea_config import NEAConfig


class NEAExecutionEngine(QObject):
    """NEA実行エンジン"""

    # シグナル
    monitor_updated = Signal(float, float, float, float, float)  # time, QE, Current, EXT, SIP
    finished = Signal()

    def __init__(self, hw_manager: HardwareManager) -> None:
        super().__init__()
        self.hw_manager = hw_manager
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_tick)
        self.timer.setInterval(1000)  # 1秒更新

        self._config: NEAConfig | None = None
        self._start_time = 0.0

    def start(self, config: NEAConfig) -> None:
        self._config = config
        self._start_time = time.monotonic()
        self.timer.start()
        print("NEA Engine Started")

    def stop(self) -> None:
        self.timer.stop()
        print("NEA Engine Stopped")
        self.finished.emit()

    @Slot()
    def _on_tick(self) -> None:
        if not self._config:
            return

        elapsed = time.monotonic() - self._start_time

        # 1. ハードウェアからデータ取得 (HardwareManager経由)
        # 現在は電圧値などが生で来ると仮定。なければStub
        # data = self.hw_manager.read_nea_data() # 仮メソッド
        # HC用の read_all を流用しつつ、NEA特有の値があれば追加実装が必要
        # ここではシミュレーション値を使用

        raw_data = self.hw_manager.read_all()  # 既存メソッド
        voltage = raw_data.hc_voltage  # 仮: GM10電圧の代わりにこれを使用(要修正)

        # 2. 計算 (nea_activation.pyのロジック)
        # Photocurrent (A) = Voltage (V) / Resistance (Ω)
        photocurrent = voltage / self._config.resistance

        # QE (%) = (Photocurrent / LaserEnergy) * (1240 / lambda) ... 簡易式
        # 例: lambda=532nm と仮定
        qe = (photocurrent / self._config.laser_power_energy) * (1240 / 532) * 100

        # 3. 通知
        self.monitor_updated.emit(
            elapsed, qe, photocurrent, raw_data.pressure_ext, raw_data.pressure_sip
        )
