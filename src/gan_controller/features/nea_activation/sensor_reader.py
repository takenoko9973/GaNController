from gan_controller.common.domain.quantity import Current, Voltage
from gan_controller.common.domain.quantity.quantity import Quantity
from gan_controller.common.domain.quantity.unit_types import Ampere, Ohm, Pascal, Volt
from gan_controller.common.hardware.adapters.logger_adapter import ILoggerAdapter
from gan_controller.common.hardware.processing.vacuum_reader import VacuumSensorReader
from gan_controller.common.schemas.app_config import AppConfig


class NEASensorReader:
    """NEA活性化用のセンサー読み取りサービス"""

    # HVの読み取り値を10000倍することで正しいV単位になる
    HV_READING_CORRECTION_FACTOR = 10000.0

    def __init__(self, adapter: ILoggerAdapter, config: AppConfig) -> None:
        self._adapter = adapter
        self._config = config

        self._vacuum_reader = VacuumSensorReader(adapter, config.devices.gm10)

    def read_ext(self) -> Quantity[Pascal]:
        return self._vacuum_reader.read_ext_pressure()

    def read_sip(self) -> Quantity[Pascal]:
        return self._vacuum_reader.read_sip_pressure()

    # === NEA固有の機能 ===
    def read_hv(self) -> Quantity[Volt]:
        """High Voltage読み取り"""
        target_ch = self._config.devices.gm10.hv_ch
        value = self._adapter.read_voltage(target_ch)

        # HVの仕様上、値が 1e4 分少ないため補正
        corrected_value = value.si_value * self.HV_READING_CORRECTION_FACTOR
        return Voltage(corrected_value)

    def read_photocurrent_integrated(
        self, shunt_r: Quantity[Ohm], n: int, interval: float
    ) -> tuple[Quantity[Volt], Quantity[Ampere]]:
        """pcの値を積算 (生の値も返す)"""
        current_volt = self._adapter.read_integrated_voltage(
            self._config.devices.gm10.pc_ch, n, interval
        )
        current_val = current_volt.si_value / shunt_r.si_value
        return current_volt, Current(current_val)
