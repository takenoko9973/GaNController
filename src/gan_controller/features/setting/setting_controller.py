from PySide6.QtCore import QObject, Slot

from gan_controller.common.services.global_messenger import GlobalMessenger
from gan_controller.features.setting.model.app_config import AppConfig
from gan_controller.features.setting.view.tab_widget import SettingsTab


class SettingsController(QObject):
    _view: SettingsTab
    _config: AppConfig

    def __init__(self, view: SettingsTab) -> None:
        super().__init__()

        self._view = view
        self._attach_view()

        self._on_load_requested()

    def _attach_view(self) -> None:
        self._view.load_requested.connect(self._on_load_requested)
        self._view.save_requested.connect(self._on_save_requested)

    def get_config(self) -> AppConfig:
        return self._config.model_copy(deep=True)

    @Slot()
    def _on_load_requested(self) -> None:
        """設定読み込み"""
        self._config = AppConfig.load()
        self._view.set_config(self._config)

        messenger = GlobalMessenger()
        messenger.show_status("設定を読み込みました", 5000)

    @Slot()
    def _on_save_requested(self) -> None:
        """設定を保存する"""
        config = self._view.create_config_from_ui()
        config.save()
        self._config = config

        messenger = GlobalMessenger()
        messenger.show_status("設定を保存しました", 5000)
