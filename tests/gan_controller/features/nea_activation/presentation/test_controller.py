import pytest
from pytestqt.qtbot import QtBot

from gan_controller.core.domain.app_config import AppConfig, CommonConfig, DevicesConfig
from gan_controller.features.nea_activation.domain.config import NEAConfig
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
        lambda message, _timeout_ms: status_messages.append(message)
    )

    controller.on_error("E1")

    assert shown_errors == ["Error occurred: E1"]
    assert status_messages == ["E1"]


def test_experiment_start_failure_reports_error_and_returns_idle(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    view = NEAActivationMainView()
    qtbot.addWidget(view)
    controller = NEAActivationController(view)

    shown_errors: list[str] = []
    status_messages: list[str] = []

    view.show_error = shown_errors.append  # type: ignore[method-assign]
    controller.status_message_requested.connect(
        lambda message, _timeout_ms: status_messages.append(message)
    )

    def _raise_on_create_recorder(*_args: object, **_kwargs: object) -> None:
        msg = "recorder error"
        raise RuntimeError(msg)

    monkeypatch.setattr(controller, "_create_recorder", _raise_on_create_recorder)

    controller.experiment_start()

    assert controller._state == NEAActivationState.IDLE  # noqa: SLF001
    assert len(shown_errors) == 1
    assert shown_errors[0].startswith("実験開始準備エラー:")
    assert status_messages[-1].startswith("実験開始準備エラー:")


def test_experiment_start_fixed_background_disables_laser_connection(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    view = NEAActivationMainView()
    qtbot.addWidget(view)
    controller = NEAActivationController(view)

    captured: dict[str, object] = {}

    class _FakeRealBackend:
        def __init__(self, devices: object, connect_laser: bool = True) -> None:
            captured["devices"] = devices
            captured["connect_laser"] = connect_laser

    nea_config = NEAConfig()
    nea_config.condition.is_fixed_background = True

    monkeypatch.setattr(
        "gan_controller.features.nea_activation.presentation.controller.AppConfig.load",
        lambda: AppConfig(common=CommonConfig(is_simulation_mode=False), devices=DevicesConfig()),
    )
    monkeypatch.setattr(
        "gan_controller.features.nea_activation.presentation.controller.RealNEAHardwareBackend",
        _FakeRealBackend,
    )
    monkeypatch.setattr(
        controller._view, "get_full_config", lambda: nea_config  # noqa: SLF001
    )
    monkeypatch.setattr(controller, "_create_recorder", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(controller._runner_manager, "start_workflow", lambda _workflow: None)  # noqa: SLF001

    controller.experiment_start()

    assert captured["connect_laser"] is False
