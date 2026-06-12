from pytestqt.qtbot import QtBot

from gan_controller.features.heat_cleaning.presentation.view.widgets.execution_panel import (
    HCExecutionPanel,
)


def test_delay_input_defaults(qtbot: QtBot) -> None:
    panel = HCExecutionPanel()
    qtbot.addWidget(panel)

    delay_input = panel.delay_start_spinbox

    assert delay_input.isChecked() is False
    assert delay_input.value() == 0.0
    assert delay_input.spin_box.decimals() == 1
    assert delay_input.spin_box.suffix() == " h"
    assert delay_input.spin_box.singleStep() == 0.1
