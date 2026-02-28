from pytestqt.qtbot import QtBot

from gan_controller.features.nea_activation.domain.models import NEAActivationState
from gan_controller.features.nea_activation.presentation.controller import NEAActivationController
from gan_controller.features.nea_activation.presentation.view import NEAActivationMainView


def test_on_error_shows_message_and_emits_status(qtbot: QtBot) -> None:
    view = NEAActivationMainView()
    qtbot.addWidget(view)
    controller = NEAActivationController(view)

    shown_errors: list[str] = []
    status_messages: list[str] = []

    view.show_error = shown_errors.append  # type: ignore[method-assign]
    controller.status_message_requested.connect(
        lambda message, timeout_ms: status_messages.append(message)
    )

    controller.on_error("E1")

    assert shown_errors == ["Error occurred: E1"]
    assert status_messages == ["E1"]


def test_experiment_start_failure_reports_error_and_returns_idle(
    qtbot: QtBot, monkeypatch
) -> None:
    view = NEAActivationMainView()
    qtbot.addWidget(view)
    controller = NEAActivationController(view)

    shown_errors: list[str] = []
    status_messages: list[str] = []

    view.show_error = shown_errors.append  # type: ignore[method-assign]
    controller.status_message_requested.connect(
        lambda message, timeout_ms: status_messages.append(message)
    )

    def _raise_on_create_recorder(*args, **kwargs) -> None:  # noqa: ANN002, ANN003
        msg = "recorder error"
        raise RuntimeError(msg)

    monkeypatch.setattr(controller, "_create_recorder", _raise_on_create_recorder)

    controller.experiment_start()

    assert controller._state == NEAActivationState.IDLE  # noqa: SLF001
    assert len(shown_errors) == 1
    assert shown_errors[0].startswith("実験開始準備エラー:")
    assert status_messages[-1].startswith("実験開始準備エラー:")
