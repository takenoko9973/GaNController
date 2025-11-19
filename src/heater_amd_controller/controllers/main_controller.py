class MainController:
    def __init__(self, view) -> None:
        self.view = view

        # シグナル接続
        # view.ui.pushButton_run.clicked.connect(self.on_run_clicked)

    # def on_run_clicked(self):
    #     result = self.model.compute_value()
    #     self.view.ui.label_output.setText(str(result))
