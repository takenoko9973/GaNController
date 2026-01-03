from dataclasses import dataclass

from PySide6.QtWidgets import QWidget

# 共通基底クラス (PageControllerなど)
from gan_controller.common.interfaces.tab_controller import ITabController
from gan_controller.features.heat_cleaning.hc_controller import HeatCleaningController
from gan_controller.features.heat_cleaning.ui.tab_widget import HeatCleaningTab
from gan_controller.features.nea_activation.nea_controller import NEAActivationController
from gan_controller.features.nea_activation.view.nea_tab_widget import NEAActivationTab

# 各機能のViewとControllerをインポート
from gan_controller.features.setting.setting_controller import SettingsController
from gan_controller.features.setting.view.tab_widget import SettingsTab


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
        hc_view = HeatCleaningTab()
        hc_ctrl = HeatCleaningController(hc_view)
        features.append(AppFeature("Heat Cleaning", hc_view, hc_ctrl))

        # NEA活性化 (NEA Activation)
        nea_view = NEAActivationTab()
        nea_ctrl = NEAActivationController(nea_view)
        features.append(AppFeature("NEA Activation", nea_view, nea_ctrl))

        # 設定 (Settings)
        setting_view = SettingsTab()
        setting_ctrl = SettingsController(setting_view)
        features.append(AppFeature("Settings", setting_view, setting_ctrl))

        return features
