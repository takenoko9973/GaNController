from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from .layouts import NEAActMainLayout


class NEAActivationTab(QWidget):
    """NEA 活性化タブの見た目制御"""

    # === 要素
    _main_layout: NEAActMainLayout

    # === シグナル
    experiment_start = Signal()
    experiment_stop = Signal()
    setting_apply = Signal()

    def __init__(self) -> None:
        super().__init__()

        # View
        self._main_layout = NEAActMainLayout()
        self.setLayout(self._main_layout)

        self._init_connect()

    def _init_connect(self) -> None:
        self._main_layout.execution_panel.start_button.clicked.connect(self.experiment_start.emit)
        self._main_layout.execution_panel.stop_button.clicked.connect(self.experiment_stop.emit)
        self._main_layout.execution_panel.apply_button.clicked.connect(self.setting_apply.emit)
