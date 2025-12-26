from PySide6.QtWidgets import QMainWindow, QStatusBar, QTabWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("GaN Controller")
        self.resize(950, 850)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def show_status_message(self, message: str, timeout: int = 5000) -> None:
        """ステータスバーにメッセージを表示する (デフォルト5秒で消える)"""
        self.status_bar.showMessage(message, timeout)
