from pytestqt.qtbot import QtBot

from gan_controller.core.services.physics import calculate_quantum_efficiency
from gan_controller.features.manual_operation.presentation.view import ManualOperationMainView


def test_qe_calculator_default_value_is_zero(qtbot: QtBot) -> None:
    view = ManualOperationMainView()
    qtbot.addWidget(view)

    assert view.qe_value_label.text() == "0 %"


def test_qe_calculator_updates_automatically(qtbot: QtBot) -> None:
    view = ManualOperationMainView()
    qtbot.addWidget(view)

    view.qe_pc_spin.setValue(2.0)
    view.qe_laser_power_spin.setValue(5.0)
    view.qe_wavelength_spin.setValue(406.0)

    expected = calculate_quantum_efficiency(
        current_amp=2e-9,
        laser_power_watt=5.0e-3,
        wavelength_nm=406.0,
    )

    assert view.qe_value_label.text() == f"{expected:.4g} %"
