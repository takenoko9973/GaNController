import sys

from PySide6.QtWidgets import QMainWindow, QStatusBar, QTabWidget, QVBoxLayout, QWidget

from heater_amd_controller.views.config import ConfigTab
from heater_amd_controller.views.heat_cleaning import HeatCleaningTab


class MainWindowView(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("実験制御アプリケーション")
        self.resize(1100, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)  # 余白を少し詰める

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # ==================

        self.tabs = QTabWidget()

        self.sequence_tab = HeatCleaningTab()
        self.config_tab = ConfigTab()

        self.tabs.addTab(self.sequence_tab, "Heat Cleaning")
        self.tabs.addTab(self.config_tab, "Config")

        # ==================

        main_layout.addWidget(self.tabs)

    def show_status_message(self, message: str, timeout: int = 5000) -> None:
        """ステータスバーにメッセージを表示する (デフォルト5秒で消える)"""
        self.status_bar.showMessage(message, timeout)


# テスト実行用
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MainWindowView()
    window.show()
    sys.exit(app.exec())
