from PySide6.QtCore import QObject, Slot

from heater_amd_controller.logics.hardware_manager import HardwareManager
from heater_amd_controller.logics.nea_execution_engine import NEAExecutionEngine
from heater_amd_controller.views.nea_activation.tab import NEAActivationTab


class NEAController(QObject):
    def __init__(self, view: NEAActivationTab, hw_manager: HardwareManager) -> None:
        super().__init__()
        self.view = view
        self.hw_manager = hw_manager
        self.engine = NEAExecutionEngine(hw_manager)

        self._setup_connections()

    def _setup_connections(self) -> None:
        """シグナルとスロットの接続定義"""
        # Engine からのシグナル
        self.engine.monitor_updated.connect(self.on_monitor_updated)  # モニタ更新

        # Ui (Tab) からのシグナル
        self.view.start_requested.connect(self.on_start)  # 開始信号
        self.view.stop_requested.connect(self.on_stop)  # 停止信号
        self.view.apply_laser_requested.connect(self.on_apply_laser)  # レーザーエネルギー変更

    @Slot()
    def on_start(self) -> None:
        config = self.view.get_config()
        self.view.setup_graphs()
        self.engine.start(config)
        self.view.update_status("実行中", 0, True)

    @Slot()
    def on_stop(self) -> None:
        self.engine.stop()
        self.view.update_status("停止", 0, False)

    @Slot(float)
    def on_apply_laser(self, value: float) -> None:
        print(f"Laser setting applied: {value} mW")
        self.view.append_log(f"Laser set to {value} mW")

    @Slot(float, float, float, float, float)
    def on_monitor_updated(self, time: float, qe: float, pc: float, ext: float, hv: float) -> None:
        self.view.update_graphs(time, qe, pc, ext)
        # 時間更新
        self.view.update_status("実行中", time, True)

        self.view.update_monitor(qe, pc, ext, hv)
