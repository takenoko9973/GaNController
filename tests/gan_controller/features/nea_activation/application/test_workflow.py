import datetime
import queue
from types import SimpleNamespace

import pytest

from gan_controller.core.domain.quantity import Current, Resistance, Time, Value, Voltage
from gan_controller.core.domain.result import ExperimentResult
from gan_controller.features.nea_activation.application.workflow import NEAActivationWorkflow
from gan_controller.features.nea_activation.domain.config import NEAConfig, NEAControlConfig
from gan_controller.presentation.async_runners.interfaces import IExperimentObserver


class _DummyObserver(IExperimentObserver):
    def __init__(self) -> None:
        self.finished_calls = 0

    def on_step_completed(self, result: ExperimentResult) -> None:
        pass

    def on_error(self, message: str) -> None:
        pass

    def on_finished(self) -> None:
        self.finished_calls += 1

    def is_interruption_requested(self) -> bool:
        return False

    def on_message(self, message: str) -> None:
        pass


class _DummyRecorder:
    def __init__(self) -> None:
        self.header_called = False

    def record_header(self, _start_time: datetime.datetime) -> None:
        self.header_called = True

    def record_data(self, result: object, comment: str = "") -> None:
        pass


class _DummyFacade:
    def __init__(self) -> None:
        self.setup_called = False
        self.applied_controls: list[NEAControlConfig] = []

    def __enter__(self) -> "_DummyFacade":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        pass

    def setup_devices(self) -> None:
        self.setup_called = True

    def apply_control_params(self, params: NEAControlConfig) -> None:
        self.applied_controls.append(params)


class _DummyBackend:
    def __init__(self, facade: _DummyFacade) -> None:
        self._facade = facade

    def __enter__(self) -> "_DummyBackend":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        pass

    def get_facade(self) -> _DummyFacade:
        return self._facade


def test_execute_initializes_facade_before_measurement_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = NEAConfig()
    facade = _DummyFacade()
    backend = _DummyBackend(facade)
    recorder = _DummyRecorder()
    workflow = NEAActivationWorkflow(backend, recorder, config, queue.Queue())

    loop_called = False

    def _fake_measurement_loop(current_facade: _DummyFacade) -> None:
        nonlocal loop_called
        loop_called = True
        assert current_facade.setup_called is True
        assert current_facade.applied_controls == [config.control]

    monkeypatch.setattr(workflow, "_measurement_loop", _fake_measurement_loop)

    observer = _DummyObserver()
    workflow.execute(observer)

    assert recorder.header_called is True
    assert loop_called is True
    assert observer.finished_calls == 1


class _MeasurementFacade:
    def __init__(self) -> None:
        self.emission_calls: list[bool] = []
        self.photocurrent_reads = 0
        self.last_dark_voltage = None
        self.last_dark_current = None

    def set_laser_emission(self, enable: bool) -> None:
        self.emission_calls.append(enable)

    def read_photocurrent(
        self, _shunt_r: object, _count: int, _interval: float
    ) -> tuple[Voltage, Current]:
        self.photocurrent_reads += 1
        return Voltage(12.0, "m"), Current(1.2e-6)

    def read_metrics(self, **kwargs: object) -> SimpleNamespace:
        self.last_dark_voltage = kwargs["dark_pc_voltage"]
        self.last_dark_current = kwargs["dark_pc"]
        return SimpleNamespace(quantum_efficiency=1.0, photocurrent=2.0, ext_pressure=3.0)

    def apply_control_params(self, _params: NEAControlConfig) -> None:
        pass

    def setup_devices(self) -> None:
        pass


def test_execute_single_measurement_fixed_background_skips_laser_control(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = NEAConfig()
    config.condition.is_fixed_background = True
    config.condition.fixed_background_volt = Voltage(1.5, "m")
    config.condition.shunt_resistance = Resistance(10, "k")
    config.condition.stabilization_time = Time(0)
    config.condition.integration_count = Value(1)
    config.condition.integration_interval = Time(0.1)

    facade = _MeasurementFacade()
    recorder = _DummyRecorder()
    workflow = NEAActivationWorkflow(_DummyBackend(_DummyFacade()), recorder, config, queue.Queue())
    workflow._observer = _DummyObserver()  # noqa: SLF001

    monkeypatch.setattr(workflow, "_notify_result", lambda _result: None)

    success = workflow._execute_single_measurement(facade, start_perf=0.0)  # noqa: SLF001

    assert success is True
    assert facade.emission_calls == []
    assert facade.photocurrent_reads == 1
    assert facade.last_dark_voltage == config.condition.fixed_background_volt
