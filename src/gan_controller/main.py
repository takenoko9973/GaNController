import os
import signal
import sys

from PySide6.QtWidgets import QApplication

from gan_controller.ui.app_feature import FeatureFactory
from gan_controller.ui.main_window import MainWindow


def run_app(argv: list[str]) -> QApplication:
    app = QApplication(argv)
    app.setStyle("Fusion")

    # フォントサイズ固定
    font = app.font()
    font.setPointSize(9)
    app.setFont(font)

    # Ctrl+C で終了できるように (Pyside6 では Ctrl+C で終了できない)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    features = FeatureFactory.create_features()
    window = MainWindow(features)
    window.show()

    return app.exec()


def main() -> None:
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    os.environ["QT_SCALE_FACTOR"] = "1"

    sys.exit(run_app(sys.argv))


if __name__ == "__main__":
    main()
