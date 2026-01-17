from abc import ABC, abstractmethod
from contextlib import ExitStack
from dataclasses import dataclass
from typing import Any

import pyvisa

# ドライバのインポート
from gan_controller.common.hardware.adapters.logger_adapter import (
    GM10Adapter,
    ILoggerAdapter,
    MockLoggerAdapter,
)
from gan_controller.common.hardware.adapters.power_supply_adapter import (
    IPowerSupplyAdapter,
    MockPowerSupplyAdapter,
    PFR100L50Adapter,
)
from gan_controller.common.hardware.adapters.pyrometer_adapter import (
    IPyrometerAdapter,
    MockPyrometerAdapter,
    PWUXAdapter,
)
from gan_controller.common.hardware.drivers import GM10, PFR100L50, PWUX
from gan_controller.common.schemas.app_config import AppConfig


@dataclass
class HCDevices:
    """HeatCleaningで使用するデバイス群を保持するコンテナ"""

    logger: ILoggerAdapter
    hps: IPowerSupplyAdapter
    aps: IPowerSupplyAdapter
    pyrometer: IPyrometerAdapter


# =================================================================
#  Factory Definitions (Abstract Factory Pattern)
# =================================================================


class AbstractHCDeviceFactory(ABC):
    """デバイス生成の抽象ファクトリー"""

    @abstractmethod
    def create_devices(self, config: AppConfig) -> tuple[HCDevices, Any]:
        """デバイス群を生成して返す。

        Returns:
            tuple[HCDevices, Any]:
                - 作成されたデバイスコンテナ
                - 管理が必要なリソースオブジェクト(例: pyvisa.ResourceManager)。不要ならNone。

        """


class SimulationHCDeviceFactory(AbstractHCDeviceFactory):
    """シミュレーション用 (Mock) デバイスファクトリー"""

    def create_devices(self, config: AppConfig) -> tuple[HCDevices, Any]:  # noqa: ARG002
        print("--- SIMULATION MODE ---")
        # Mockアダプタを生成
        devices = HCDevices(
            logger=MockLoggerAdapter(),
            hps=MockPowerSupplyAdapter(),
            aps=MockPowerSupplyAdapter(),
            pyrometer=MockPyrometerAdapter(),
        )
        return devices, None  # リソースマネージャは不要


class RealHCDeviceFactory(AbstractHCDeviceFactory):
    """実機用デバイスファクトリー"""

    def create_devices(self, config: AppConfig) -> tuple[HCDevices, Any]:
        # 実機接続用のResourceManagerを作成
        rm = pyvisa.ResourceManager()

        # 失敗した場合、デバイスとの接続を切るスタックを作成
        with ExitStack() as stack:
            stack.callback(rm.close)

            try:
                # Logger (GM10)
                gm10 = GM10(rm, config.devices.gm10.visa)
                logger_adapter = GM10Adapter(gm10)
                stack.callback(logger_adapter.close)

                # Power Supply (HC/PFR100L50)
                hps = PFR100L50(rm, config.devices.aps.visa)
                hps_adapter = PFR100L50Adapter(hps)
                stack.callback(hps_adapter.close)

                # Power Supply (AMD/PFR100L50)
                aps = PFR100L50(rm, config.devices.aps.visa)
                aps_adapter = PFR100L50Adapter(aps)
                stack.callback(aps_adapter.close)

                # Pyrometer (PWUX)
                if config.devices.pwux.com_port <= 0:
                    pyrometer = PWUX(rm, f"COM{config.devices.pwux.com_port}")
                    pyrometer_adapter = PWUXAdapter(pyrometer)
                    stack.callback(pyrometer_adapter.close)
                else:
                    pyrometer_adapter = MockPyrometerAdapter()

                # 成功したら、スタックをすべて削除
                stack.pop_all()

                return HCDevices(
                    logger=logger_adapter,
                    hps=hps_adapter,
                    aps=aps_adapter,
                    pyrometer=pyrometer_adapter,
                ), rm

            except Exception as e:
                print(f"[CRITICAL] Device creation failed: {e}")
                # withから出ると、スタックされた処理が実行される
                raise


# =================================================================
#  Device Manager (Context Manager)
# =================================================================


class HCDeviceManager:
    """デバイスの接続と終了を管理するコンテキストマネージャ"""

    def __init__(self, config: AppConfig, factory: AbstractHCDeviceFactory) -> None:
        self.config = config
        self._factory = factory

        self._devices: HCDevices | None = None
        self._resource_manager: pyvisa.ResourceManager | None = None

    def __enter__(self) -> HCDevices:
        """実験開始時の処理: Factoryを使用してデバイスを生成"""
        self._devices, self._resource_manager = self._factory.create_devices(self.config)
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
