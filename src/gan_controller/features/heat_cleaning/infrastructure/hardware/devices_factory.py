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
from gan_controller.common.schemas.app_config import DevicesConfig


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
    def create_devices(
        self, config: DevicesConfig, use_pyrometer: bool = True
    ) -> tuple[HCDevices, Any]:
        """デバイス群を生成して返す。

        Returns:
            tuple[HCDevices, Any]:
                - 作成されたデバイスコンテナ
                - 管理が必要なリソースオブジェクト(例: pyvisa.ResourceManager)。不要ならNone。

        """


class SimulationHCDeviceFactory(AbstractHCDeviceFactory):
    """シミュレーション用 (Mock) デバイスファクトリー"""

    def create_devices(
        self,
        config: DevicesConfig,  # noqa: ARG002
        use_pyrometer: bool = True,  # noqa: ARG002
    ) -> tuple[HCDevices, Any]:
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

    def create_devices(
        self, config: DevicesConfig, use_pyrometer: bool = True
    ) -> tuple[HCDevices, Any]:
        # 実機接続用のResourceManagerを作成
        rm = pyvisa.ResourceManager()

        # 失敗した場合、デバイスとの接続を切るスタックを作成
        with ExitStack() as stack:
            stack.callback(rm.close)

            try:
                # Logger (GM10)
                gm10 = GM10(rm, config.gm10.visa)
                logger_adapter = GM10Adapter(gm10)
                stack.callback(logger_adapter.close)

                # Power Supply (HC/PFR100L50)
                hps = PFR100L50(rm, config.hps.visa)
                hps_adapter = PFR100L50Adapter(hps)
                stack.callback(hps_adapter.close)
                hps_adapter.set_voltage(config.hps.v_limit)
                hps_adapter.set_ovp(config.hps.ovp)
                hps_adapter.set_ocp(config.hps.ocp)
                hps_adapter.set_output(False)  # 安全のため、強制OFF

                # Power Supply (AMD/PFR100L50)
                aps = PFR100L50(rm, config.aps.visa)
                aps_adapter = PFR100L50Adapter(aps)
                stack.callback(aps_adapter.close)
                aps_adapter.set_voltage(config.aps.v_limit)
                aps_adapter.set_ovp(config.aps.ovp)
                aps_adapter.set_ocp(config.aps.ocp)
                aps_adapter.set_output(False)  # 安全のため、強制OFF

                # Pyrometer (PWUX)
                if use_pyrometer and config.pwux.com_port > 0:
                    pyrometer = PWUX(rm, f"COM{config.pwux.com_port}")
                    pyrometer_adapter = PWUXAdapter(pyrometer)
                    stack.callback(pyrometer_adapter.close)
                else:
                    if not use_pyrometer:
                        print("Pyrometer initialization skipped (Disabled by user).")
                    else:
                        print("Pyrometer initialization skipped (Invalid COM port).")

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

    _factory: AbstractHCDeviceFactory
    _config: DevicesConfig

    def __init__(self, factory: AbstractHCDeviceFactory, config: DevicesConfig) -> None:
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
