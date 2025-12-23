from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from heater_amd_controller.logics.hardware_manager import SensorData
from heater_amd_controller.models.protocol_config import ProtocolConfig
from heater_amd_controller.models.sequence import SequenceMode
from heater_amd_controller.views.widgets.checkable_spinbox import CheckableSpinBox
from heater_amd_controller.views.widgets.graph_widget import AxisScale, DualAxisGraph

from .execution_panel import HCExecutionPanel


class HeatCleaningTab(QWidget):
    """Heat Cleaning 制御用タブ"""

    # シグナル
    protocol_selected = Signal(str)  # プロトコル変更時の読み込み用
    save_overwrite_requested = Signal()  # 通常保存
    save_as_requested = Signal()  # 名前をつけて保存
    start_requested = Signal()  # 開始信号
    stop_requested = Signal()  # 停止信号

    # ショートカット
    shortcut_save: QShortcut
    shortcut_save_as: QShortcut

    # UIウィジェット (左パネル)
    protocol_combo: QComboBox
    save_button: QPushButton
    # 右パネル
    graph_power: DualAxisGraph
    graph_pressure: DualAxisGraph

    # シーケンス設定用
    sequence_time_spins: dict[str, QDoubleSpinBox]
    sequence_repeat_spin: QDoubleSpinBox
    step_interval_spin: QDoubleSpinBox
    hc_checked_spin: CheckableSpinBox
    amd_checked_spin: CheckableSpinBox

    # ログ設定用
    chk_date_update: QCheckBox
    chk_major_update: QCheckBox
    comment_edit: QLineEdit

    # 実行制御グループ
    execution_panel: HCExecutionPanel

    def __init__(self) -> None:
        super().__init__()
        self._init_shortcuts()
        self.init_ui()

    def _init_shortcuts(self) -> None:
        """ショートカットキーの設定"""
        # Ctrl+S -> 上書き保存
        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.activated.connect(self.save_overwrite_requested.emit)

        # Ctrl+Shift+S -> 名前を付けて保存
        self.shortcut_save_as = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        self.shortcut_save_as.activated.connect(self.save_as_requested.emit)

    def init_ui(self) -> None:
        # メインのレイアウト (左右分割)
        main_layout = QHBoxLayout(self)

        # --- 左側のコントロールパネル ---
        left_panel_layout = QVBoxLayout()
        left_panel_layout.addLayout(self.create_protocol_selector_layout())
        left_panel_layout.addSpacing(10)
        left_panel_layout.addWidget(self.create_sequence_group())
        left_panel_layout.addSpacing(10)
        left_panel_layout.addWidget(self.create_log_settings_group())
        left_panel_layout.addSpacing(10)

        self._execution_panel = HCExecutionPanel()
        # シグナル連鎖
        self._execution_panel.start_requested.connect(self.start_requested.emit)
        self._execution_panel.stop_requested.connect(self.stop_requested.emit)
        left_panel_layout.addWidget(self._execution_panel)

        left_panel_layout.addStretch()

        # --- 右側の表示エリア ---
        right_panel_layout = QVBoxLayout()

        self.graph_power = DualAxisGraph(
            "Power",
            "Time (h)",
            "Temperature (°C)",
            "Power (W)",
        )
        self.graph_power.setMinimumWidth(500)
        self.graph_power.setMinimumHeight(300)

        self.graph_pressure = DualAxisGraph(
            "Pressure",
            "Time (h)",
            "Temperature (°C)",
            "Pressure (Pa)",
            right_scale=AxisScale.LOG,
        )
        self.graph_pressure.setMinimumWidth(500)
        self.graph_pressure.setMinimumHeight(300)

        log_display = QTextEdit()
        log_display.setReadOnly(True)
        log_display.setPlaceholderText("Log...")

        right_panel_layout.addWidget(self.graph_power)
        right_panel_layout.addSpacing(10)
        right_panel_layout.addWidget(self.graph_pressure)
        right_panel_layout.addSpacing(10)
        right_panel_layout.addWidget(QLabel("Log"))
        right_panel_layout.addWidget(log_display)

        # --- レイアウトの統合 ---
        left_widget = QWidget()  # 横幅固定用
        left_widget.setLayout(left_panel_layout)
        left_widget.setFixedWidth(400)

        main_layout.addWidget(left_widget)
        main_layout.addLayout(right_panel_layout)

    def create_protocol_selector_layout(self) -> QHBoxLayout:
        """プロトコル選択エリアのレイアウトを作成 (グループ外)"""
        layout = QHBoxLayout()

        self.protocol_combo = QComboBox()
        self.save_button = QPushButton("保存")
        layout.addWidget(QLabel("プロトコル"))
        layout.addWidget(self.protocol_combo)
        layout.addStretch()
        layout.addWidget(self.save_button)

        self.protocol_combo.currentTextChanged.connect(self.protocol_selected.emit)
        self.save_button.clicked.connect(self.save_overwrite_requested.emit)

        return layout

    def create_sequence_group(self) -> QWidget:
        group_box = QGroupBox("シーケンス")
        main_v_layout = QVBoxLayout()

        sequence_layout = self._create_sequence_grid_layout()
        setting_layout = self._create_settings_layout()

        main_v_layout.addLayout(sequence_layout)
        main_v_layout.addSpacing(20)
        main_v_layout.addLayout(setting_layout)

        group_box.setLayout(main_v_layout)
        return group_box

    def _create_sequence_grid_layout(self) -> QGridLayout:
        # === 各シーケンス時間
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setColumnStretch(1, 1)

        self.sequence_time_spins: dict[str, QDoubleSpinBox] = {}

        layout.addWidget(QLabel("時間 (hour)"), 0, 1)
        for i, section_mode in enumerate(SequenceMode):
            col = 1 + i
            double_spin_box = QDoubleSpinBox(minimum=0, decimals=3, singleStep=0.5)

            layout.addWidget(QLabel(section_mode.value), col, 0)
            layout.addWidget(double_spin_box, col, 1)

            self.sequence_time_spins[section_mode.value] = double_spin_box

        return layout

    def _create_settings_layout(self) -> QHBoxLayout:
        """シーケンス設定"""
        setting_layout = QHBoxLayout()
        setting_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        config_layout1 = QGridLayout()
        self.sequence_repeat_spin = QDoubleSpinBox(value=1, minimum=1, decimals=0)
        self.step_interval_spin = QDoubleSpinBox(value=10, minimum=1, decimals=0, suffix="s")
        config_layout1.addWidget(QLabel("繰り返し回数"), 0, 0)
        config_layout1.addWidget(self.sequence_repeat_spin, 0, 1)
        config_layout1.addWidget(QLabel("ステップ間隔"), 1, 0)
        config_layout1.addWidget(self.step_interval_spin, 1, 1)

        config_layout2 = QGridLayout()
        self.hc_checked_spin = CheckableSpinBox("HC 電流", minimum=0, decimals=1, suffix="A")
        self.amd_checked_spin = CheckableSpinBox("AMD 電流", minimum=0, decimals=1, suffix="A")
        config_layout2.addWidget(self.hc_checked_spin, 0, 0, 1, 2)
        config_layout2.addWidget(self.amd_checked_spin, 1, 0, 1, 2)

        setting_layout.addLayout(config_layout1)
        setting_layout.addSpacing(20)
        setting_layout.addLayout(config_layout2)

        return setting_layout

    def create_log_settings_group(self) -> QWidget:
        """Log設定グループ"""
        group_box = QGroupBox("Log設定")
        main_layout = QVBoxLayout()

        # 右側 (Log設定のチェックボックス)
        checks_layout = QHBoxLayout()
        self.chk_date_update = QCheckBox("日付フォルダ更新")
        self.chk_major_update = QCheckBox("メジャー番号更新")
        checks_layout.addWidget(self.chk_date_update)
        checks_layout.addWidget(self.chk_major_update)
        checks_layout.addStretch()

        comment_layout = QHBoxLayout()
        comment_layout.addWidget(QLabel("コメント:"))
        self.comment_edit = QLineEdit()
        self.comment_edit.setPlaceholderText("Comment... (don't save for protocol config)")
        comment_layout.addWidget(self.comment_edit)

        main_layout.addLayout(checks_layout)
        main_layout.addLayout(comment_layout)

        group_box.setLayout(main_layout)
        return group_box

    def set_protocol_list(self, names: list[str]) -> None:
        """プロトコル名のリストを受け取ってプルダウンを更新する"""
        current = self.protocol_combo.currentText()

        self.protocol_combo.blockSignals(True)  # イベント無効化

        self.protocol_combo.clear()
        self.protocol_combo.addItems(names)
        self.protocol_combo.setCurrentText(current)  # 可能なら選択維持

        self.protocol_combo.blockSignals(False)

    def select_protocol(self, name: str) -> None:
        """指定した名前をコンボボックスで選択する (Controllerから呼ぶ)"""
        self.protocol_combo.blockSignals(True)
        self.protocol_combo.setCurrentText(name)
        self.protocol_combo.blockSignals(False)

    def update_ui_from_data(self, data: ProtocolConfig) -> None:
        """データを受け取って、全入力欄に反映"""
        for step_name, time_value in data.sequence_hours.items():
            if step_name in self.sequence_time_spins:
                self.sequence_time_spins[step_name].setValue(time_value)

        # HC, AMD設定
        self.hc_checked_spin.set_data(data.hc_enabled, data.hc_current)
        self.amd_checked_spin.set_data(data.amd_enabled, data.amd_current)

        # その他設定
        self.sequence_repeat_spin.setValue(data.repeat_count)
        self.step_interval_spin.setValue(data.step_interval)

        # ログ設定
        self.chk_date_update.setChecked(data.log_date_update)
        self.chk_major_update.setChecked(data.log_major_update)

    def get_current_protocol_name(self) -> str:
        """現在のプロトコルの名前を取得"""
        return self.protocol_combo.currentText()

    def get_current_ui_data(self) -> ProtocolConfig:
        """現在の画面の入力値を取得"""
        sequence_times = {}
        for step_name, spin_widget in self.sequence_time_spins.items():
            sequence_times[step_name] = spin_widget.value()

        return ProtocolConfig(
            name=self.protocol_combo.currentText(),
            sequence_hours=sequence_times,
            repeat_count=int(self.sequence_repeat_spin.value()),
            step_interval=int(self.step_interval_spin.value()),
            # HC, AMD設定
            hc_enabled=self.hc_checked_spin.is_checked(),
            hc_current=self.hc_checked_spin.value(),
            amd_enabled=self.amd_checked_spin.is_checked(),
            amd_current=self.amd_checked_spin.value(),
            # Log設定
            log_date_update=self.chk_date_update.isChecked(),
            log_major_update=self.chk_major_update.isChecked(),
            comment=self.comment_edit.text(),
        )

    # ============================================================

    def update_execution_status(
        self, status_text: str, step_time: str, total_time: str, is_running: bool
    ) -> None:
        self._execution_panel.update_status(status_text, step_time, total_time, is_running)

    def update_sensor_values(self, data: SensorData) -> None:
        hc_vals = (data.hc_current, data.hc_voltage, data.hc_power)
        amd_vals = (data.amd_current, data.amd_voltage, data.amd_power)

        self._execution_panel.update_sensor_values(
            hc_vals, amd_vals, data.temperature, data.pressure_ext, data.pressure_sip
        )

    # ============================================================

    def update_graph_titles(self, filename: str) -> None:
        """ログファイル名をタイトルに設定"""
        # どのグラフかわかるようにSuffixをつける
        self.graph_power.set_title(f"{filename}_power")
        self.graph_pressure.set_title(f"{filename}_pressure")

    def setup_graphs(self, config: ProtocolConfig) -> None:
        """実行設定に基づいてグラフのラインを再構築する"""
        # === Graph 1: Power & Temp ===
        self.graph_power.clear_lines()
        self.graph_power.clear_data()

        self.graph_power.add_line("TC", "TC (℃)", "red")

        # HC (有効な場合のみ追加)
        if config.hc_enabled:
            label = f"Heater({config.hc_current:.1f}A) (W)"
            self.graph_power.add_line("HC", label, "orange", is_right_axis=True)

        # AMD (有効な場合のみ追加)
        if config.amd_enabled:
            label = f"AMD({config.amd_current:.1f}A) (W)"
            self.graph_power.add_line("AMD", label, "gold", is_right_axis=True)

        # === Graph 2: Pressure & Temp ===
        self.graph_pressure.clear_lines()
        self.graph_pressure.clear_data()
        self.graph_pressure.add_line("TC", "TC (℃)", "red")
        self.graph_pressure.add_line("EXT", "EXT (Pa)", "green", is_right_axis=True)
        self.graph_pressure.add_line("SIP", "SIP (Pa)", "purple", is_right_axis=True)

        # 再描画
        self.graph_power.canvas.draw()
        self.graph_pressure.canvas.draw()

    def update_graphs(self, time_sec: float, data: SensorData) -> None:
        """グラフのみ更新 (ログ間隔で呼ばれる)"""
        time_hour = time_sec / 3600
        hc_vals = (data.hc_current, data.hc_voltage, data.hc_power)
        amd_vals = (data.amd_current, data.amd_voltage, data.amd_power)

        # Graph 1: Power & Temp
        self.graph_power.update_point(
            time_hour,
            {
                "TC": data.temperature,
                "HC": hc_vals[2],
                "AMD": amd_vals[2],
            },
        )

        # Graph 2: Pressure & Temp
        self.graph_pressure.update_point(
            time_hour,
            {
                "TC": data.temperature,
                "EXT": data.pressure_ext,
                "SIP": data.pressure_sip,
            },
        )
