import pytest
from pytestqt.qtbot import QtBot

from gan_controller.features.heat_cleaning.domain.models import HeatCleaningState
from gan_controller.features.heat_cleaning.presentation.controller import HeatCleaningController
from gan_controller.features.heat_cleaning.presentation.view import HeatCleaningMainView


def _disable_log_preview(monkeypatch: pytest.MonkeyPatch) -> None:
    def _spy_update_log_preview(_self: HeatCleaningController) -> None:
        return

    monkeypatch.setattr(HeatCleaningController, "_update_log_preview", _spy_update_log_preview)


def test_preview_refresh_signal_triggers_log_preview_update(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = {"count": 0}

    def _spy_update_log_preview(_self: HeatCleaningController) -> None:
        calls["count"] += 1

    monkeypatch.setattr(HeatCleaningController, "_update_log_preview", _spy_update_log_preview)

    view = HeatCleaningMainView()
    qtbot.addWidget(view)
    controller = HeatCleaningController(view)

    baseline = calls["count"]
    view.log_setting_panel.preview_refresh_requested.emit()

    assert controller is not None
    assert calls["count"] == baseline + 1


def test_start_without_delay_starts_experiment_immediately(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    _disable_log_preview(monkeypatch)
    view = HeatCleaningMainView()
    qtbot.addWidget(view)
    controller = HeatCleaningController(view)
    calls = {"count": 0}

    def _spy_start() -> None:
        calls["count"] += 1

    monkeypatch.setattr(controller, "_start_experiment_now", _spy_start)
    view.execution_panel.delay_start_spinbox.setChecked(False)
    view.execution_panel.delay_start_spinbox.setValue(0.1)

    controller.experiment_start()

    assert calls["count"] == 1
    assert controller._state == HeatCleaningState.IDLE  # noqa: SLF001


def test_start_with_delay_enters_delay_without_starting_runner(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    _disable_log_preview(monkeypatch)
    view = HeatCleaningMainView()
    qtbot.addWidget(view)
    controller = HeatCleaningController(view)
    calls = {"count": 0}

    def _spy_start() -> None:
        calls["count"] += 1

    monkeypatch.setattr(controller, "_start_experiment_now", _spy_start)
    view.execution_panel.delay_start_spinbox.setChecked(True)
    view.execution_panel.delay_start_spinbox.setValue(0.1)

    controller.experiment_start()

    assert controller._state == HeatCleaningState.DELAYING  # noqa: SLF001
    assert calls["count"] == 0
    assert controller._runner_manager.is_running() is False  # noqa: SLF001

    controller.experiment_stop()


def test_delay_status_reports_remaining_seconds(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    _disable_log_preview(monkeypatch)
    view = HeatCleaningMainView()
    qtbot.addWidget(view)
    controller = HeatCleaningController(view)
    messages: list[str] = []

    controller.status_message_requested.connect(lambda message, _timeout: messages.append(message))
    monkeypatch.setattr(controller, "_remaining_delay_seconds", lambda: 123)

    controller._update_delay_status()  # noqa: SLF001

    assert messages == ["遅延実行まで残り 123 秒"]


def test_delay_timer_expiry_starts_experiment(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    _disable_log_preview(monkeypatch)
    view = HeatCleaningMainView()
    qtbot.addWidget(view)
    controller = HeatCleaningController(view)
    calls = {"count": 0}

    def _spy_start() -> None:
        calls["count"] += 1

    monkeypatch.setattr(controller, "_start_experiment_now", _spy_start)
    monkeypatch.setattr(controller, "_remaining_delay_seconds", lambda: 0)
    controller.set_state(HeatCleaningState.DELAYING)
    controller._delay_timer.start()  # noqa: SLF001

    controller._on_delay_timer_timeout()  # noqa: SLF001

    assert calls["count"] == 1
    assert controller._delay_timer.isActive() is False  # noqa: SLF001


def test_stop_during_delay_cancels_without_starting_runner(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    _disable_log_preview(monkeypatch)
    view = HeatCleaningMainView()
    qtbot.addWidget(view)
    controller = HeatCleaningController(view)
    calls = {"count": 0}

    def _spy_start() -> None:
        calls["count"] += 1

    monkeypatch.setattr(controller, "_start_experiment_now", _spy_start)
    view.execution_panel.delay_start_spinbox.setChecked(True)
    view.execution_panel.delay_start_spinbox.setValue(0.1)

    controller.experiment_start()
    controller.experiment_stop()

    assert controller._state == HeatCleaningState.IDLE  # noqa: SLF001
    assert calls["count"] == 0
    assert controller._runner_manager.is_running() is False  # noqa: SLF001
