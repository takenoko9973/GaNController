from dataclasses import dataclass

from PySide6.QtWidgets import QWidget

from gan_controller.features.heat_cleaning.presentation.controller import HeatCleaningController
from gan_controller.features.heat_cleaning.presentation.view import HeatCleaningMainView
from gan_controller.features.nea_activation.presentation.controller import NEAActivationController
from gan_controller.features.nea_activation.presentation.view import NEAActivationMainView

# 各機能のViewとControllerをインポート
from gan_controller.features.setting.controller import SettingsController
from gan_controller.features.setting.view import SettingMainView

# 共通基底クラス (PageControllerなど)
from gan_controller.presentation.components.tab_controller import ITabController


@dataclass
class AppFeature:
    """1つの機能(タブ)を構成する要素"""

    title: str
    view: QWidget
    controller: ITabController


class FeatureFactory:
    """機能の生成と配線を担当するクラス"""

    @staticmethod
    def create_features() -> list[AppFeature]:
        """アプリケーションで使用する全機能を生成してリストで返す"""
        features = []

        # 加熱洗浄 (Heat Cleaning)
        hc_view = HeatCleaningMainView()
        hc_ctrl = HeatCleaningController(hc_view)
        features.append(AppFeature("Heat Cleaning", hc_view, hc_ctrl))

        # NEA活性化 (NEA Activation)
        nea_view = NEAActivationMainView()
        nea_ctrl = NEAActivationController(nea_view)
        features.append(AppFeature("NEA Activation", nea_view, nea_ctrl))

        # 設定 (Settings)
        setting_view = SettingMainView()
        setting_ctrl = SettingsController(setting_view)
        features.append(AppFeature("Settings", setting_view, setting_ctrl))

        return features
