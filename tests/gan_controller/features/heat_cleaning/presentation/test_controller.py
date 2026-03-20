import pytest
from pytestqt.qtbot import QtBot

from gan_controller.features.heat_cleaning.presentation.controller import HeatCleaningController
from gan_controller.features.heat_cleaning.presentation.view import HeatCleaningMainView


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
