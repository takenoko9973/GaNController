import datetime
import queue

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

    def record_header(self, start_time: datetime.datetime) -> None:
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


def test_execute_initializes_facade_before_measurement_loop(monkeypatch) -> None:
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
