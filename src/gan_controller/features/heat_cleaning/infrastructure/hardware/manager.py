from typing import TYPE_CHECKING

from gan_controller.common.schemas.app_config import DevicesConfig
from gan_controller.features.heat_cleaning.infrastructure.hardware import HCDevices

from .factory import IHeatCleaningDeviceFactory

if TYPE_CHECKING:
    import pyvisa


class HCDeviceManager:
    """デバイスの接続と終了を管理するコンテキストマネージャ"""

    _factory: IHeatCleaningDeviceFactory
    _config: DevicesConfig

    def __init__(self, factory: IHeatCleaningDeviceFactory, config: DevicesConfig) -> None:
        self._factory = factory
        self._config = config

        self._devices: HCDevices | None = None
        self._resource_manager: pyvisa.ResourceManager | None = None

    def __enter__(self) -> HCDevices:
        """実験開始時の処理: Factoryを使用してデバイスを生成"""
        self._devices, self._resource_manager = self._factory.create_devices(self._config)
        return self._devices

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001, C901
        """実験終了時の処理: 各デバイスの切断とリソース解放"""
        if self._devices:
            # 各デバイスのクローズ (エラーがあっても続行)
            if self._devices.pyrometer:
                try:
                    self._devices.pyrometer.close()
                except Exception as e:  # noqa: BLE001
                    print(f"Error closing pyrometer: {e}")

            if self._devices.aps:
                try:
                    self._devices.aps.close()
                except Exception as e:  # noqa: BLE001
                    print(f"Error closing APS: {e}")

            if self._devices.hps:
                try:
                    self._devices.hps.close()
                except Exception as e:  # noqa: BLE001
                    print(f"Error closing HPS: {e}")

            if self._devices.logger:
                try:
                    self._devices.logger.close()
                except Exception as e:  # noqa: BLE001
                    print(f"Error closing logger: {e}")

        # VISA ResourceManagerのクローズ
        if self._resource_manager:
            try:
                self._resource_manager.close()
            except Exception as e:  # noqa: BLE001
                print(f"Error closing ResourceManager: {e}")
