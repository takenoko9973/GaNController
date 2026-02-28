from gan_controller.presentation.async_runners.interfaces import IExperimentObserver, IExperimentWorkflow
from gan_controller.presentation.async_runners.manager import _ExperimentWorker


class _WorkflowCallsFinishAndRaises(IExperimentWorkflow):
    def execute(self, observer: IExperimentObserver) -> None:
        observer.on_finished()
        msg = "boom"
        raise RuntimeError(msg)


class _WorkflowRaisesOnly(IExperimentWorkflow):
    def execute(self, observer: IExperimentObserver) -> None:
        msg = "boom"
        raise RuntimeError(msg)


class _WorkflowNoOp(IExperimentWorkflow):
    def execute(self, observer: IExperimentObserver) -> None:
        pass


def test_worker_emits_finished_once_when_workflow_finishes_and_raises() -> None:
    worker = _ExperimentWorker(_WorkflowCallsFinishAndRaises())
    finished_count = 0
    errors: list[str] = []

    def _inc_finished() -> None:
        nonlocal finished_count
        finished_count += 1

    worker.finished.connect(_inc_finished)
    worker.error_occurred.connect(errors.append)
    worker.run()

    assert finished_count == 1
    assert errors == ["boom"]


def test_worker_emits_finished_once_when_workflow_raises_without_finish() -> None:
    worker = _ExperimentWorker(_WorkflowRaisesOnly())
    finished_count = 0
    errors: list[str] = []

    def _inc_finished() -> None:
        nonlocal finished_count
        finished_count += 1

    worker.finished.connect(_inc_finished)
    worker.error_occurred.connect(errors.append)
    worker.run()

    assert finished_count == 1
    assert errors == ["boom"]


def test_worker_emits_finished_once_on_normal_completion() -> None:
    worker = _ExperimentWorker(_WorkflowNoOp())
    finished_count = 0
    errors: list[str] = []

    def _inc_finished() -> None:
        nonlocal finished_count
        finished_count += 1

    worker.finished.connect(_inc_finished)
    worker.error_occurred.connect(errors.append)
    worker.run()

    assert finished_count == 1
    assert errors == []
