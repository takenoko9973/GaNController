from gan_controller.common.adapters.logger_adapter import ILoggerAdapter
from gan_controller.common.services.vacuum_reader import VacuumSensorReader
from gan_controller.common.types.quantity.quantity import Quantity
from gan_controller.features.setting.model.app_config import AppConfig


class NEASensorReader:
    """NEA活性化用のセンサー読み取りサービス"""

    def __init__(self, adapter: ILoggerAdapter, config: AppConfig) -> None:
        self._adapter = adapter
        self._config = config

        self._vacuum_reader = VacuumSensorReader(adapter, config.devices.gm10)

    def read_ext(self) -> Quantity:
        return self._vacuum_reader.read_ext_pressure()

    def read_sip(self) -> Quantity:
        return self._vacuum_reader.read_sip_pressure()

    # === NEA固有の機能 ===
    def read_hv(self) -> Quantity:
        """High Voltage読み取り"""
        value = self._adapter.read_voltage(self._config.devices.gm10.hv_ch, "V")
        return Quantity(value.value_as() * 1e4, "V")  # なぜか 1e4 分少ないため、補正

    def read_photocurrent_integrated(self, shunt_r: Quantity, n: int, interval: float) -> Quantity:
        """pcの値を積算"""
        value = self._adapter.read_integrated_voltage(
            self._config.devices.gm10.pc_ch, "mV", n, interval
        )
        current_val = value.value_as("") / shunt_r.value_as("")
        return Quantity(current_val, "A")
