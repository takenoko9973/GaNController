from PySide6.QtWidgets import QWidget

from .layouts import NEAMainLayout


class NEAActivationTab(QWidget):
    main_layout: NEAMainLayout

    def __init__(self) -> None:
        super().__init__()

        # self.model = ExperimentAModel()
        # self.controller = ExperimentAController(self.model)

        self.main_layout = NEAMainLayout()
        self.setLayout(self.main_layout)
