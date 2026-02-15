from abc import ABC, abstractmethod
from contextlib import ExitStack

import pyvisa

from gan_controller.core.models.app_config import DevicesConfig
from gan_controller.features.heat_cleaning.domain.models import HCDevices
from gan_controller.infrastructure.hardware.adapters.logger_adapter import (
    GM10Adapter,
    MockLoggerAdapter,
)
from gan_controller.infrastructure.hardware.adapters.power_supply_adapter import (
    MockPowerSupplyAdapter,
    PFR100L50Adapter,
)
from gan_controller.infrastructure.hardware.adapters.pyrometer_adapter import (
    MockPyrometerAdapter,
    PWUXAdapter,
)
from gan_controller.infrastructure.hardware.drivers import GM10, PFR100L50, PWUX

from .facade import (
    HCHardwareFacade,
)


# --- Abstract Base Class (Strategy Interface) ---
class HCHardwareBackend(ABC):
    """ハードウェアの生成・接続・破棄を担う基底クラス"""

    def __init__(self, config: DevicesConfig) -> None:
        self._config = config
        self._devices: HCDevices | None = None
        self._rm: pyvisa.ResourceManager | None = None

    @abstractmethod
    def _connect_devices(self) -> tuple[HCDevices, pyvisa.ResourceManager | None]:
        """具体的な接続処理 (サブクラスで実装)"""

    def __enter__(self) -> HCHardwareFacade:
        """デバイスと接続してFacadeを返す"""
        #  デバイス接続
        self._devices, self._rm = self._connect_devices()

        # Facadeの生成
        return HCHardwareFacade(self._devices, self._config)

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001, C901
        """コンテキスト出口: 切断処理 (Managerの役割)"""
        # デバイスのクローズ処理
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

        # VISAリソースマネージャの破棄
        if self._rm:
            try:
                self._rm.close()
            except Exception as e:  # noqa: BLE001
                print(f"Error closing ResourceManager: {e}")


# --- Concrete Strategies ---


class RealHCHardwareBackend(HCHardwareBackend):
    """実機用バックエンド"""

    def __init__(self, config: DevicesConfig, use_pyrometer: bool = True) -> None:
        super().__init__(config)
        self._use_pyrometer = use_pyrometer

    def _connect_devices(self) -> tuple[HCDevices, pyvisa.ResourceManager]:
        print("Connecting to Real Hardware...")
        rm = pyvisa.ResourceManager()

        # 失敗した場合、デバイスとの接続を切るスタックを作成
        with ExitStack() as stack:
            stack.callback(rm.close)

            try:
                # Logger (GM10)
                gm10 = GM10(rm, self._config.gm10.visa)
                logger_adapter = GM10Adapter(gm10)
                stack.callback(logger_adapter.close)

                # Power Supply (HC/PFR100L50)
                hps = PFR100L50(rm, self._config.hps.visa)
                hps_adapter = PFR100L50Adapter(hps)
                stack.callback(hps_adapter.close)
                hps_adapter.set_voltage(self._config.hps.v_limit)
                hps_adapter.set_ovp(self._config.hps.ovp)
                hps_adapter.set_ocp(self._config.hps.ocp)
                hps_adapter.set_output(False)  # 安全のため、強制OFF

                # Power Supply (AMD/PFR100L50)
                aps = PFR100L50(rm, self._config.aps.visa)
                aps_adapter = PFR100L50Adapter(aps)
                stack.callback(aps_adapter.close)
                aps_adapter.set_voltage(self._config.aps.v_limit)
                aps_adapter.set_ovp(self._config.aps.ovp)
                aps_adapter.set_ocp(self._config.aps.ocp)
                aps_adapter.set_output(False)  # 安全のため、強制OFF

                # Pyrometer (PWUX)
                if self._use_pyrometer and self._config.pwux.com_port > 0:
                    pyrometer = PWUX(rm, f"COM{self._config.pwux.com_port}")
                    pyrometer_adapter = PWUXAdapter(pyrometer)
                    stack.callback(pyrometer_adapter.close)
                else:
                    print("Pyrometer initialization skipped.")
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


class SimulationHCHardwareBackend(HCHardwareBackend):
    """シミュレーション用バックエンド"""

    def _connect_devices(self) -> tuple[HCDevices, pyvisa.ResourceManager | None]:
        print("Initializing Simulation Hardware...")

        # Mockアダプタを生成
        devices = HCDevices(
            logger=MockLoggerAdapter(),
            hps=MockPowerSupplyAdapter(),
            aps=MockPowerSupplyAdapter(),
            pyrometer=MockPyrometerAdapter(),
        )
        return devices, None
