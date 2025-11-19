from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class ConfigTab(QWidget):
    """ハードウェア接続設定やアプリケーション全体の基本設定を行うタブ"""

    def __init__(self) -> None:
        super().__init__()
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # --- 1. ハードウェア接続設定 ---
        hw_group = QGroupBox("ハードウェア接続設定")
        hw_form = QFormLayout()

        # COMポート設定など
        self.port_combo = QComboBox()
        self.port_combo.addItems(["COM1", "COM3", "COM4"])
        hw_form.addRow("コントローラー COMポート:", self.port_combo)

        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "115200"])
        hw_form.addRow("ボーレート:", self.baud_combo)

        hw_form.addRow("タイムアウト (ms):", QSpinBox(value=1000))

        connect_btn = QPushButton("接続テスト")
        hw_form.addRow("", connect_btn)

        hw_group.setLayout(hw_form)
        layout.addWidget(hw_group)

        # --- 2. 保存パス設定 ---
        path_group = QGroupBox("データ保存設定")
        path_form = QFormLayout()

        self.save_dir_edit = QLineEdit("C:/Data/Experiment")
        browse_btn = QPushButton("参照...")
        # 横並びにする
        path_box = QWidget()
        path_box_layout = QFormLayout(path_box)  # 簡易的に
        # 本来は HBoxLayout ですが省略

        path_form.addRow("ルート保存先:", self.save_dir_edit)
        path_form.addRow(browse_btn)

        path_group.setLayout(path_form)
        layout.addWidget(path_group)

        # 上に詰める
        layout.addStretch()
