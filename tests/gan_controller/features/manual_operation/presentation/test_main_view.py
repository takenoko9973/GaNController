from pytestqt.qtbot import QtBot

from gan_controller.core.domain.app_config import GM10Config
from gan_controller.core.domain.quantity import Voltage
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


def test_gm10_voltage_and_vacuum_pressure_display_in_order_and_update(qtbot: QtBot) -> None:
    view = ManualOperationMainView()
    qtbot.addWidget(view)

    view.set_gm10_channel_config(GM10Config(ext_ch=1, sip_ch=2))
    view.update_gm10_values({"ext": Voltage(8.0), "sip": Voltage(4.0)})

    view.adjustSize()
    view.show()
    qtbot.wait(10)

    assert view.gm10_pressure_labels["ext"].text() == "1.00e-02 Pa"
    assert view.gm10_pressure_labels["sip"].text() == "5.00e-05 Pa"
    assert view.gm10_value_labels["ext"].text() == "8 V"
    assert view.gm10_value_labels["sip"].text() == "4 V"
    assert view.gm10_value_labels["ext"].x() < view.gm10_pressure_labels["ext"].x()
    assert view.gm10_value_labels["sip"].x() < view.gm10_pressure_labels["sip"].x()

    view.set_gm10_channel_config(GM10Config(ext_ch=0, sip_ch=2))
    view.update_gm10_values({"ext": Voltage(9.0), "sip": Voltage(6.0)})

    assert view.gm10_pressure_labels["ext"].text() == "--"
    assert view.gm10_value_labels["ext"].text() == "--"
    assert view.gm10_pressure_labels["sip"].text() == "5.00e-04 Pa"
    assert view.gm10_value_labels["sip"].text() == "6 V"
