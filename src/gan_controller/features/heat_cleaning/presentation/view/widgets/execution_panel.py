from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLayout, QPushButton, QVBoxLayout, QWidget


class HCExecutionPanel(QGroupBox):
    """実行制御およびモニタリング表示用ウィジェット"""

    # === 要素
    start_button: QPushButton
    stop_button: QPushButton

    # === シグナル
    start_requested = Signal()
    stop_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("実行制御", parent)

        layout = QVBoxLayout(self)
        layout.addLayout(self._create_control_section())  # 制御

        self._connect_signal()

    def _create_control_section(self) -> QLayout:
        control_layout = QHBoxLayout()

        self.start_button = QPushButton("開始")
        self.stop_button = QPushButton("停止")

        self.start_button.setMinimumHeight(40)
        self.stop_button.setMinimumHeight(40)

        # 初期状態: 停止中なので「停止」ボタンは無効化
        self.stop_button.setEnabled(False)

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)

        return control_layout

    def _connect_signal(self) -> None:
        """シグナル設定"""
        # クリック時のシグナル接続
        self.start_button.clicked.connect(self.start_requested.emit)
        self.stop_button.clicked.connect(self.stop_requested.emit)
