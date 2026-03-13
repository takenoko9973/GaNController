from typing import Never

import pytest
from pytestqt.qtbot import QtBot

from gan_controller.core.domain.app_config import AppConfig, CommonConfig, DevicesConfig
from gan_controller.features.manual_operation.presentation.controller import (
    ManualOperationController,
)
from gan_controller.features.manual_operation.presentation.view import ManualOperationMainView


class _StubPwuxHandler:
    def __init__(self) -> None:
        self._is_connected = False
        self.connect_calls: list[AppConfig] = []
        self.disconnect_calls = 0

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def connect(self, app_config: AppConfig) -> None:
        self.connect_calls.append(app_config)
        self._is_connected = True

    def disconnect(self) -> None:
        self.disconnect_calls += 1
        self._is_connected = False

    def read_temperature(self) -> Never:
        msg = "read_temperature should not be called in this test"
        raise AssertionError(msg)

    def set_pointer(self, _enable: bool) -> None:
        msg = "set_pointer should not be called in this test"
        raise AssertionError(msg)


class _FailingPwuxHandler(_StubPwuxHandler):
    def connect(self, _app_config: AppConfig) -> None:
        msg = "connect failed"
        raise RuntimeError(msg)


def _stub_app_config() -> AppConfig:
    return AppConfig(common=CommonConfig(is_simulation_mode=True), devices=DevicesConfig())


def test_connect_pwux_success_updates_view(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    view = ManualOperationMainView()
    qtbot.addWidget(view)

    monkeypatch.setattr(
        "gan_controller.features.manual_operation.presentation.controller.PwuxHandler",
        _StubPwuxHandler,
    )
    monkeypatch.setattr(
        "gan_controller.features.manual_operation.presentation.controller.AppConfig.load",
        _stub_app_config,
    )

    controller = ManualOperationController(view)

    connected_states: list[bool] = []
    view.set_pwux_connected = connected_states.append  # type: ignore[method-assign]

    controller.connect_pwux()

    assert connected_states == [True]
    assert controller._pwux.connect_calls  # noqa: SLF001


def test_connect_pwux_failure_reports_error_and_disconnects(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    view = ManualOperationMainView()
    qtbot.addWidget(view)

    monkeypatch.setattr(
        "gan_controller.features.manual_operation.presentation.controller.PwuxHandler",
        _FailingPwuxHandler,
    )
    monkeypatch.setattr(
        "gan_controller.features.manual_operation.presentation.controller.AppConfig.load",
        _stub_app_config,
    )

    controller = ManualOperationController(view)

    errors: list[str] = []
    view.show_error = errors.append  # type: ignore[method-assign]

    controller.connect_pwux()

    assert errors
    assert controller._pwux.disconnect_calls == 1  # noqa: SLF001


def test_try_switch_from_cancels_when_user_declines(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    view = ManualOperationMainView()
    qtbot.addWidget(view)
    controller = ManualOperationController(view)

    monkeypatch.setattr(controller, "_has_active_connections", lambda: True)
    monkeypatch.setattr(view, "confirm_disconnect_all", lambda: False)

    disconnect_calls: list[bool] = []
    monkeypatch.setattr(controller, "disconnect_all", lambda: disconnect_calls.append(True))

    assert controller.try_switch_from() is False
    assert disconnect_calls == []


def test_try_switch_from_disconnects_when_user_accepts(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    view = ManualOperationMainView()
    qtbot.addWidget(view)
    controller = ManualOperationController(view)

    monkeypatch.setattr(controller, "_has_active_connections", lambda: True)
    monkeypatch.setattr(view, "confirm_disconnect_all", lambda: True)

    disconnect_calls: list[bool] = []
    monkeypatch.setattr(controller, "disconnect_all", lambda: disconnect_calls.append(True))

    assert controller.try_switch_from() is True
    assert disconnect_calls == [True]


def test_on_close_disconnects_all(qtbot: QtBot, monkeypatch: pytest.MonkeyPatch) -> None:
    view = ManualOperationMainView()
    qtbot.addWidget(view)
    controller = ManualOperationController(view)

    disconnect_calls: list[bool] = []
    monkeypatch.setattr(controller, "disconnect_all", lambda: disconnect_calls.append(True))

    controller.on_close()

    assert disconnect_calls == [True]
