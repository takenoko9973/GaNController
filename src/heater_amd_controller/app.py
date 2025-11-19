from PySide6.QtWidgets import QApplication

from heater_amd_controller.views.main_window import MainWindowView


class Application:
    def __init__(self, argv: list[str]) -> None:
        # インスタンス変数として参照を保持する
        self.app = QApplication(argv)
        self.window = MainWindowView()

    def run(self) -> int:
        self.window.show()
        # self.app が GC されない限り、イベントループは回り続ける
        return self.app.exec()


def create_app(argv: list[str]) -> Application:
    """QApplication を初期化し、メインウィンドウを起動する"""
    return Application(argv)
