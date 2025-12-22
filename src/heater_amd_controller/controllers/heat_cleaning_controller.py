from PySide6.QtCore import QObject, Signal

from heater_amd_controller.controllers.handlers.protocol_handler import ProtocolHandler
from heater_amd_controller.logics.hardware_manager import HardwareManager, SensorData
from heater_amd_controller.logics.hc_execution_engine import HCExecutionEngine
from heater_amd_controller.logics.protocol_manager import ProtocolManager
from heater_amd_controller.views.heat_cleaning import HeatCleaningTab


class HeatCleaningController(QObject):
    # メッセージシグナル (メッセージ内容, 表示時間ms (0なら永続))
    status_message_requested = Signal(str, int)

    def __init__(self, view: HeatCleaningTab, manager: ProtocolManager) -> None:
        super().__init__()
        self.view = view
        self.manager = manager

        self.hw_manager = HardwareManager()

        # === 各要素からのシグナルの接続
        # Handler からのシグナル
        self.proto_handler = ProtocolHandler(view, manager)
        self.proto_handler.status_message.connect(self.status_message_requested)  # 状態メッセージ
        self.proto_handler.data_loaded.connect(self.view.update_ui_from_data)  # 記録データ表示
        self.proto_handler.refresh_protocol_list_req.connect(self.refresh_list)  # protocol一覧更新
        # Engine からのシグナル
        self.engine = HCExecutionEngine(self.hw_manager)
        self.engine.monitor_updated.connect(self._on_engine_tick)  # 記録タイミングのシグナル
        self.engine.sequence_finished.connect(self._on_engine_finished)  # 記録終了時のシグナル
        self.engine.sequence_stopped.connect(self._on_engine_stopped)  # 記録中断時のシグナル
        # Ui (Tab) からのシグナル
        self.view.protocol_selected.connect(self.proto_handler.load_protocol)  # プロトコル変更
        self.view.save_overwrite_requested.connect(self._on_save_clicked)  # 通常保存
        self.view.save_as_requested.connect(self._on_save_as_clicked)  # 名前をつけて保存
        self.view.start_requested.connect(self._start_experiment)  # 開始・停止信号
        self.view.stop_requested.connect(self._stop_experiment)  # 開始・停止信号

        # 初期化処理
        self.refresh_list()

    def refresh_list(self, select_name: str | None = None) -> None:
        """リストを更新し、指定があればそれを選択する"""
        names = self.manager.get_protocol_names()
        self.view.set_protocol_list(names)

        if select_name and select_name in names:
            target_name = select_name
        elif names:
            target_name = names[0]

        if target_name:
            self.view.select_protocol(target_name)
            self.proto_handler.load_protocol(target_name)

    def _on_save_clicked(self) -> None:
        """上書き保存 (Ctrl+S)"""
        name = self.view.get_current_protocol_name()
        data = self.view.get_current_ui_data()
        self.proto_handler.save_overwrite(name, data)

    def _on_save_as_clicked(self) -> None:
        """名前を付けて保存 (Ctrl+Shift+S)"""
        name = self.view.get_current_protocol_name()
        data = self.view.get_current_ui_data()
        self.proto_handler.save_as(name, data)

    def _start_experiment(self) -> None:
        config = self.view.get_current_ui_data()  # 現在の設定取得
        self.engine.start(config)

    def _stop_experiment(self) -> None:
        self.engine.stop()

    def _on_engine_tick(self, status: str, step_t: str, total_t: str, data: SensorData) -> None:
        # 画面更新
        self.view.update_execution_status(status, step_t, total_t, True)

        # センサー値更新
        hc_vals = (data.hc_current, data.hc_voltage, data.hc_power)
        amd_vals = (data.amd_current, data.amd_voltage, data.amd_power)
        self.view.update_sensor_values(
            hc_vals, amd_vals, data.temperature, data.pressure_ext, data.pressure_sip
        )

    def _on_engine_finished(self, total_time: str) -> None:
        self.view.update_execution_status("完了", "00:00:00", total_time, False)
        self.status_message_requested.emit("全工程完了", 0)

    def _on_engine_stopped(self, total_time: str) -> None:
        self.view.update_execution_status("停止", "00:00:00", total_time, False)
        self.status_message_requested.emit("停止しました", 3000)
