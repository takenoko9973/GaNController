from gan_controller.common.calculations.vacuum import (
    calc_ext_pressure_from_voltage,
    calc_sip_pressure_from_voltage,
)
from gan_controller.common.domain.quantity import Pressure, Quantity
from gan_controller.common.domain.quantity.unit_types import Pascal
from gan_controller.common.hardware.adapters.logger_adapter import ILoggerAdapter
from gan_controller.features.setting.model.app_config import GM10Config


class VacuumSensorReader:
    """システム共通の真空計読み取りサービス"""

    def __init__(self, adapter: ILoggerAdapter, config: GM10Config) -> None:
        self._adapter = adapter
        self._config = config  # GM10設定(ch番号, unit)を保持

    def read_ext_pressure(self) -> Quantity[Pascal]:
        """EXT真空計の値を読み取る"""
        val_q = self._adapter.read_voltage(self._config.ext_ch, "V")

        pressure_val = calc_ext_pressure_from_voltage(val_q.si_value)
        return Pressure(pressure_val)

    def read_sip_pressure(self) -> Quantity[Pascal]:
        """SIP真空計の値を読み取る"""
        val_q = self._adapter.read_voltage(self._config.sip_ch, "V")

        pressure_val = calc_sip_pressure_from_voltage(val_q.si_value)
        return Pressure(pressure_val)
