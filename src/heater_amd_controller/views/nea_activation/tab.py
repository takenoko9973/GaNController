from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from heater_amd_controller.models.nea_config import NEAConfig
from heater_amd_controller.views.nea_activation.execution_panel import NEAExecutionPanel
from heater_amd_controller.views.nea_activation.setting_widget import NEASettingsGroup
from heater_amd_controller.views.widgets.graph_widget import AxisScale, DualAxisGraph


class GraphKey:
    """グラフのライン識別用キー定数"""

    QE_PERCENT = "QE"
    PHOTOCURRENT = "PC"
    EXT_PRES = "EXT"


class NEAActivationTab(QWidget):
    """NEA Activation 制御用タブ"""

    # シグナル
    start_requested = Signal()  # 開始信号
    stop_requested = Signal()  # 停止信号
    apply_laser_requested = Signal(float, float)  # Controllerへ中継

    def __init__(self) -> None:
        super().__init__()
        self.init_ui()

    def init_ui(self) -> None:
        main_layout = QHBoxLayout(self)

        # --- 左パネル (設定・操作) ---
        left_layout = QVBoxLayout()

        # 1. パラメータ設定
        self.settings_group = NEASettingsGroup()
        self.settings_group.apply_laser_requested.connect(self.apply_laser_requested.emit)
        left_layout.addWidget(self.settings_group)

        left_layout.addSpacing(10)

        # 2. ログ設定 (簡易版)
        self.log_group = self._create_log_group()
        left_layout.addWidget(self.log_group)

        left_layout.addSpacing(10)

        # 3. 実行制御
        self.execution_panel = NEAExecutionPanel()
        self.execution_panel.start_requested.connect(self.start_requested.emit)
        self.execution_panel.stop_requested.connect(self.stop_requested.emit)
        left_layout.addWidget(self.execution_panel)

        left_layout.addStretch()

        # --- 右パネル (グラフ) ---
        right_layout = QVBoxLayout()

        # グラフ1: QE
        self.graph_qe = DualAxisGraph(
            "Quantum Efficiency",
            "Time (s)",
            "QE (%)",
            "Pressure (Pa)",
            right_scale=AxisScale.LOG,
        )
        self.graph_qe.setMinimumWidth(500)
        self.graph_qe.setMinimumHeight(300)

        # グラフ2: Photocurrent
        self.graph_pc = DualAxisGraph(
            "Photocurrent",
            "Time (s)",
            "Photocurrent (A)",
            "Pressure (Pa)",
            right_scale=AxisScale.LOG,
        )
        self.graph_pc.setMinimumWidth(500)
        self.graph_pc.setMinimumHeight(300)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(100)

        right_layout.addWidget(self.graph_qe)
        right_layout.addWidget(self.graph_pc)
        right_layout.addWidget(QLabel("Log:"))
        right_layout.addWidget(self.log_display)

        # レイアウト統合
        container_left = QWidget()
        container_left.setLayout(left_layout)
        container_left.setFixedWidth(400)

        main_layout.addWidget(container_left)
        main_layout.addLayout(right_layout)

    def _create_log_group(self) -> QGroupBox:
        gb = QGroupBox("ログ設定")
        vbox = QVBoxLayout(gb)
        self.chk_date = QCheckBox("日付フォルダ更新")
        self.chk_major = QCheckBox("メジャー番号更新")
        hbox = QHBoxLayout()
        hbox.addWidget(self.chk_date)
        hbox.addWidget(self.chk_major)
        vbox.addLayout(hbox)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(QLabel("コメント:"))
        self.edit_comment = QLineEdit()
        hbox2.addWidget(self.edit_comment)
        vbox.addLayout(hbox2)
        return gb

    def get_config(self) -> NEAConfig:
        """現在のUIから設定オブジェクトを生成"""
        params = self.settings_group.get_config_subset()
        return NEAConfig(
            **params,
            log_date_update=self.chk_date.isChecked(),
            log_major_update=self.chk_major.isChecked(),
            comment=self.edit_comment.text(),
        )

    # --- 更新用メソッド ---

    @Slot(str, float, bool)
    def update_status(self, status: str, time_sec: float, is_running: bool) -> None:
        """ステータスと時間の更新"""
        self.execution_panel.update_status(status, time_sec, is_running)

    @Slot(float, float, float, float)
    def update_monitor(self, qe: float, current: float, ext: float, hv: float) -> None:
        """モニタリング値の更新"""
        self.execution_panel.update_monitor_values(qe, current, ext, hv)

    def append_log(self, text: str) -> None:
        self.log_display.append(text)

    def setup_graphs(self) -> None:
        self.graph_qe.clear_lines()
        self.graph_qe.clear_data()
        self.graph_qe.add_line(GraphKey.QE_PERCENT, "QE (%)", "green")
        self.graph_qe.add_line(GraphKey.EXT_PRES, "Pressure(EXT)", "black", is_right_axis=True)

        self.graph_pc.clear_lines()
        self.graph_pc.clear_data()
        self.graph_pc.add_line(GraphKey.PHOTOCURRENT, "Photocurrent (A)", "red")
        self.graph_pc.add_line(GraphKey.EXT_PRES, "Pressure(EXT)", "black", is_right_axis=True)

    def update_graphs(self, time_sec: float, qe: float, pc: float, ext: float) -> None:
        self.graph_qe.update_point(
            time_sec,
            {GraphKey.QE_PERCENT: qe, GraphKey.EXT_PRES: ext},
        )
        self.graph_pc.update_point(
            time_sec,
            {GraphKey.PHOTOCURRENT: pc, GraphKey.EXT_PRES: ext},
        )
