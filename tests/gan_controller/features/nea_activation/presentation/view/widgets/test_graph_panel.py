import pytest
from pytestqt.qtbot import QtBot

from gan_controller.core.domain.electricity import ElectricMeasurement
from gan_controller.core.domain.quantity import Current, Power, Pressure, Time, Value, Voltage
from gan_controller.features.nea_activation.domain.models import NEAExperimentResult
from gan_controller.features.nea_activation.presentation.view.widgets.graph_panel import (
    NEAGraphPanel,
)


def _make_result(minute: float, qe_percent: float) -> NEAExperimentResult:
    return NEAExperimentResult(
        timestamp=Time(minute * 60.0),
        laser_power_sv=Power(10.0, "m"),
        laser_power_pv=Power(3.0, "m"),
        ext_pressure=Pressure(1.0e-3),
        sip_pressure=Pressure(1.0e-3),
        extraction_voltage=Voltage(100.0),
        photocurrent=Current(1.0e-9),
        photocurrent_voltage=Voltage(1.0, "m"),
        bright_pc=Current(2.0e-9),
        bright_pc_voltage=Voltage(2.0, "m"),
        dark_pc=Current(1.0e-9),
        dark_pc_voltage=Voltage(1.0, "m"),
        quantum_efficiency=Value(qe_percent, "%"),
        amd_electricity=ElectricMeasurement(
            current=Current(0.1),
            voltage=Voltage(1.0),
            power=Power(0.1),
        ),
    )


def _set_qe_mode(panel: NEAGraphPanel, mode: str) -> None:
    index = panel.qe_axis_mode_combo.findData(mode)
    assert index >= 0
    panel.qe_axis_mode_combo.setCurrentIndex(index)


def test_initial_qe_axis_mode_is_normal(qtbot: QtBot) -> None:
    panel = NEAGraphPanel()
    qtbot.addWidget(panel)

    assert panel.qe_axis_mode_combo.currentData() == panel.QE_AXIS_MODE_NORMAL
    assert panel.qe_fixed_max_spin.isEnabled() is False


def test_visible_max_mode_uses_values_within_time_window(qtbot: QtBot) -> None:
    panel = NEAGraphPanel()
    qtbot.addWidget(panel)

    panel.append_data(_make_result(1.0, 8.0))
    panel.append_data(_make_result(10.0, 2.0))

    panel.time_window_spin.setValue(5)
    _set_qe_mode(panel, panel.QE_AXIS_MODE_VISIBLE_MAX)

    y_min, y_max = panel.graph_qe.ax_left.get_ylim()
    assert y_min == pytest.approx(0.0)
    assert y_max == pytest.approx(2.0)


def test_fixed_max_mode_initializes_from_visible_max_and_updates_on_input(qtbot: QtBot) -> None:
    panel = NEAGraphPanel()
    qtbot.addWidget(panel)

    panel.append_data(_make_result(1.0, 4.0))
    panel.append_data(_make_result(3.0, 6.0))

    _set_qe_mode(panel, panel.QE_AXIS_MODE_FIXED_MAX)

    assert panel.qe_fixed_max_spin.isEnabled() is True
    assert panel.qe_fixed_max_spin.value() == pytest.approx(6.0)
    assert panel.graph_qe.ax_left.get_ylim()[1] == pytest.approx(6.0)

    panel.qe_fixed_max_spin.setValue(9.5)
    assert panel.graph_qe.ax_left.get_ylim()[1] == pytest.approx(9.5)


def test_switching_back_to_normal_restores_autoscale(qtbot: QtBot) -> None:
    panel = NEAGraphPanel()
    qtbot.addWidget(panel)

    panel.append_data(_make_result(1.0, 2.0))
    panel.append_data(_make_result(2.0, 3.0))

    _set_qe_mode(panel, panel.QE_AXIS_MODE_FIXED_MAX)
    panel.qe_fixed_max_spin.setValue(50.0)
    assert panel.graph_qe.ax_left.get_ylim()[1] == pytest.approx(50.0)

    _set_qe_mode(panel, panel.QE_AXIS_MODE_NORMAL)

    restored_max = panel.graph_qe.ax_left.get_ylim()[1]
    assert restored_max != pytest.approx(50.0)
    assert restored_max < 10.0


def test_visible_max_mode_falls_back_when_no_valid_qe_exists(qtbot: QtBot) -> None:
    panel = NEAGraphPanel()
    qtbot.addWidget(panel)

    panel.append_data(_make_result(1.0, -1.0))
    _set_qe_mode(panel, panel.QE_AXIS_MODE_VISIBLE_MAX)

    y_min, y_max = panel.graph_qe.ax_left.get_ylim()
    assert y_min == pytest.approx(0.0)
    assert y_max == pytest.approx(panel.QE_SAFE_FALLBACK_MAX)
