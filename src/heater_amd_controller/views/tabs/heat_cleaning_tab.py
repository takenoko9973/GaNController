from PySide6.QtCore import Qt
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

from heater_amd_controller.views.widgets.checkable_spinbox import CheckableSpinBox


class HeatCleaningTab(QWidget):
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

        combo_protocol = QComboBox()
        combo_protocol.addItems(["プロトコルA", "プロトコルB", "新しいプロトコル..."])
        layout.addWidget(QLabel("プロトコル"))
        layout.addWidget(combo_protocol)
        layout.addStretch()
        layout.addWidget(QPushButton("保存"))

        return layout

    def create_sequence_group(self) -> QWidget:
        group_box = QGroupBox("シーケンス")
        main_v_layout = QVBoxLayout()

        # =================================================

        # === 各シーケンス時間
        sequence_layout = QGridLayout()
        sequence_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sequence_layout.setColumnStretch(1, 1)

        self.sequence_time_spins = {}
        sequence_names = ["Rising", "HeatCleaning", "Decrease", "Wait"]

        sequence_layout.addWidget(QLabel("時間 (hour)"), 0, 1)
        for i, section_name in enumerate(sequence_names):
            col = 1 + i
            double_spin_box = QDoubleSpinBox(minimum=0, decimals=1)

            sequence_layout.addWidget(QLabel(section_name), col, 0)
            sequence_layout.addWidget(double_spin_box, col, 1)

            self.sequence_time_spins[section_name] = double_spin_box

        # === シーケンス設定
        config_layout = QHBoxLayout()
        config_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        config_layout1 = QGridLayout()
        self.sequence_time_spin = QDoubleSpinBox(value=1, minimum=1, decimals=0)
        self.step_time_spin = QDoubleSpinBox(value=10, minimum=0, decimals=0, suffix="s")
        config_layout1.addWidget(QLabel("繰り返し回数"), 0, 0)
        config_layout1.addWidget(self.sequence_time_spin, 0, 1)
        config_layout1.addWidget(QLabel("ステップ間隔"), 1, 0)
        config_layout1.addWidget(self.step_time_spin, 1, 1)

        config_layout2 = QGridLayout()
        self.hc_current_spin = CheckableSpinBox("HC 電流", minimum=0, decimals=1, suffix="A")
        self.amd_current_spin = CheckableSpinBox("AMD 電流", minimum=0, decimals=1, suffix="A")
        config_layout2.addWidget(self.hc_current_spin, 0, 0, 1, 2)
        config_layout2.addWidget(self.amd_current_spin, 1, 0, 1, 2)

        config_layout.addLayout(config_layout1)
        config_layout.addSpacing(20)
        config_layout.addLayout(config_layout2)

        # =================================================

        main_v_layout.addLayout(sequence_layout)
        main_v_layout.addSpacing(20)
        main_v_layout.addLayout(config_layout)

        group_box.setLayout(main_v_layout)
        return group_box

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
