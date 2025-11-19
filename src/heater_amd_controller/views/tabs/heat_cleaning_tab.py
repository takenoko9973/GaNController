from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from heater_amd_controller.models.protocol import SEQUENCE_NAMES, ProtocolConfig
from heater_amd_controller.views.widgets.checkable_spinbox import CheckableSpinBox


class HeatCleaningTab(QWidget):
    protocol_changed = Signal(str)
    save_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.init_ui()

    def init_ui(self) -> None:
        # メインのレイアウト (左右分割)
        main_layout = QHBoxLayout(self)

        # --- 1. 左側のコントロールパネル ---
        left_panel_layout = QVBoxLayout()
        left_panel_layout.addLayout(self.create_protocol_selector_layout())
        left_panel_layout.addWidget(self.create_sequence_group())

        settings_layout = QHBoxLayout()
        settings_layout.addWidget(self.create_log_settings_group())
        left_panel_layout.addLayout(settings_layout)

        # --- 2. 右側の表示エリア ---
        right_panel_layout = QVBoxLayout()
        graph_placeholder_1 = QWidget()
        graph_placeholder_1.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        graph_placeholder_1.setMinimumHeight(200)

        graph_placeholder_2 = QWidget()
        graph_placeholder_2.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        graph_placeholder_2.setMinimumHeight(200)

        log_display = QTextEdit()
        log_display.setReadOnly(True)
        log_display.setPlaceholderText("Log...")

        right_panel_layout.addWidget(QLabel("グラフ 1 (プレースホルダー)"))
        right_panel_layout.addWidget(graph_placeholder_1)
        right_panel_layout.addWidget(QLabel("グラフ 2 (プレースホルダー)"))
        right_panel_layout.addWidget(graph_placeholder_2)
        right_panel_layout.addWidget(QLabel("Log"))
        right_panel_layout.addWidget(log_display)

        # --- レイアウトの統合 ---
        left_widget = QWidget()
        left_widget.setLayout(left_panel_layout)
        left_widget.setFixedWidth(450)

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

        self.protocol_combo.currentTextChanged.connect(self.protocol_changed.emit)
        self.save_button.clicked.connect(self.save_requested.emit)

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
        for i, section_name in enumerate(SEQUENCE_NAMES):
            col = 1 + i
            double_spin_box = QDoubleSpinBox(minimum=0, decimals=1, singleStep=0.5)

            layout.addWidget(QLabel(section_name), col, 0)
            layout.addWidget(double_spin_box, col, 1)

            self.sequence_time_spins[section_name] = double_spin_box

        return layout

    def _create_settings_layout(self) -> QHBoxLayout:
        # === シーケンス設定
        setting_layout = QHBoxLayout()
        setting_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        config_layout1 = QGridLayout()
        self.sequence_repeat_spin = QDoubleSpinBox(value=1, minimum=1, decimals=0)
        self.step_interval_spin = QDoubleSpinBox(value=10, minimum=0, decimals=0, suffix="s")
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
        group_box = QGroupBox("Log設定")
        main_layout = QHBoxLayout()

        # 右側 (Log設定のチェックボックス)
        log_checks_layout = QVBoxLayout()
        log_checks_layout.addWidget(QCheckBox("日付フォルダ更新"))
        log_checks_layout.addWidget(QCheckBox("メジャー番号更新"))
        log_checks_layout.addStretch()

        main_layout.addLayout(log_checks_layout)

        group_box.setLayout(main_layout)
        return group_box

    def set_protocol_list(self, names: list[str]) -> None:
        """プロトコル名のリストを受け取ってプルダウンを更新する"""
        current = self.protocol_combo.currentText()

        self.protocol_combo.blockSignals(True)  # イベント無効化  # noqa: FBT003

        self.protocol_combo.clear()
        self.protocol_combo.addItems(names)
        self.protocol_combo.setCurrentText(current)  # 可能なら選択維持

        self.protocol_combo.blockSignals(False)  # noqa: FBT003

    def select_protocol(self, name: str) -> None:
        """指定した名前をコンボボックスで選択する (Controllerから呼ぶ)"""
        self.protocol_combo.blockSignals(True)  # noqa: FBT003
        self.protocol_combo.setCurrentText(name)
        self.protocol_combo.blockSignals(False)  # noqa: FBT003

    def update_ui_from_data(self, data: ProtocolConfig) -> None:
        """データを受け取って、全入力欄に反映"""
        for step_name, time_value in data.sequence_times.items():
            if step_name in self.sequence_time_spins:
                self.sequence_time_spins[step_name].setValue(time_value)

        # HC, AMD設定
        self.hc_checked_spin.set_data(data.hc_enabled, data.hc_current)
        self.amd_checked_spin.set_data(data.amd_enabled, data.amd_current)

        # その他設定
        self.sequence_repeat_spin.setValue(data.repeat_count)
        self.step_interval_spin.setValue(data.step_interval)

    def get_current_protocol_name(self) -> str:
        """現在のプロトコルの名前を取得"""
        return self.protocol_combo.currentText()

    def get_current_ui_data(self) -> ProtocolConfig:
        """現在の画面の入力値を取得 (保存用)"""
        sequence_times = {}
        for step_name, spin_widget in self.sequence_time_spins.items():
            sequence_times[step_name] = spin_widget.value()

        return ProtocolConfig(
            name=self.protocol_combo.currentText(),
            sequence_times=sequence_times,
            repeat_count=int(self.sequence_repeat_spin.value()),
            step_interval=int(self.step_interval_spin.value()),
            hc_enabled=self.hc_checked_spin.is_checked(),
            hc_current=self.hc_checked_spin.value(),
            amd_enabled=self.amd_checked_spin.is_checked(),
            amd_current=self.amd_checked_spin.value(),
        )
