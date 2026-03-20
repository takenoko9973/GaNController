from pytestqt.qtbot import QtBot

from gan_controller.presentation.components.widgets.log_setting_panel import CommonLogSettingPanel


def test_show_emits_preview_refresh_requested(qtbot: QtBot) -> None:
    panel = CommonLogSettingPanel()
    qtbot.addWidget(panel)
    panel._preview_refresh_timer.stop()  # noqa: SLF001

    calls: list[bool] = []
    panel.preview_refresh_requested.connect(lambda: calls.append(True))

    panel.show()
    qtbot.waitUntil(lambda: len(calls) >= 1)

    assert calls


def test_reenable_emits_preview_refresh_requested(qtbot: QtBot) -> None:
    panel = CommonLogSettingPanel()
    qtbot.addWidget(panel)
    panel._preview_refresh_timer.stop()  # noqa: SLF001

    calls: list[bool] = []
    panel.preview_refresh_requested.connect(lambda: calls.append(True))

    panel.show()
    qtbot.waitUntil(lambda: len(calls) >= 1)
    calls.clear()

    panel.setEnabled(False)
    qtbot.wait(10)
    panel.setEnabled(True)
    qtbot.waitUntil(lambda: len(calls) >= 1)

    assert len(calls) == 1


def test_disabled_widget_skips_preview_refresh_emit(qtbot: QtBot) -> None:
    panel = CommonLogSettingPanel()
    qtbot.addWidget(panel)
    panel._preview_refresh_timer.stop()  # noqa: SLF001

    calls: list[bool] = []
    panel.preview_refresh_requested.connect(lambda: calls.append(True))

    panel.show()
    qtbot.waitUntil(lambda: len(calls) >= 1)
    calls.clear()

    panel.setEnabled(False)
    panel._emit_preview_refresh_if_needed()  # noqa: SLF001

    assert calls == []
