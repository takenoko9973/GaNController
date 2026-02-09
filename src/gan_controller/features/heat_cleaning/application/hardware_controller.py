from pydantic.dataclasses import dataclass

from gan_controller.common.calculations.vacuum import (
    calc_ext_pressure_from_voltage,
    calc_sip_pressure_from_voltage,
)
from gan_controller.common.domain.electricity import ElectricMeasurement
from gan_controller.common.domain.quantity import (
    Ampere,
    Celsius,
    Current,
    Pascal,
    Pressure,
    Quantity,
    Temperature,
)
from gan_controller.common.schemas.app_config import DevicesConfig
from gan_controller.features.heat_cleaning.infrastructure.hardware import HCDevices
from gan_controller.features.heat_cleaning.schemas.config import ProtocolConfig


@dataclass
class HCHardwareMetrics:
    ext_pressure: Quantity[Pascal]
    sip_pressure: Quantity[Pascal]
    case_temperature: Quantity[Celsius]
    hc_electricity: ElectricMeasurement
    amd_electricity: ElectricMeasurement


class HCHardwareFacade:
    _dev: HCDevices
    _config: DevicesConfig

    def __init__(self, devices: HCDevices, config: DevicesConfig) -> None:
        self._dev = devices
        self._config = config

    def setup_for_protocol(self, protocol: ProtocolConfig) -> None:
        print("Setting up hardware for protocol...")

        # プロトコルで利用するデバイスの初期化
        if protocol.condition.hc_enabled:
            self._dev.hps.set_current(Current(0.0))
            self._dev.hps.set_output(True)
        else:
            self._dev.hps.set_output(False)

        if protocol.condition.amd_enabled:
            self._dev.aps.set_current(Current(0.0))
            self._dev.aps.set_output(True)
        else:
            self._dev.aps.set_output(False)

    def set_condition(
        self,
        hc_current: Quantity[Ampere] | None,
        amd_current: Quantity[Ampere] | None,
    ) -> None:
        """電流値を設定する"""
        if hc_current:
            self._dev.hps.set_current(hc_current)
        if amd_current:
            self._dev.aps.set_current(amd_current)

    def read_metrics(self) -> HCHardwareMetrics:
        """測定値をdtoにまとめて返す"""
        ext_val = self._dev.logger.read_voltage(self._config.gm10.ext_ch)
        ext_pressure = Pressure(calc_ext_pressure_from_voltage(ext_val.base_value))

        sip_val = self._dev.logger.read_voltage(self._config.gm10.sip_ch)
        sip_pressure = Pressure(calc_sip_pressure_from_voltage(sip_val.base_value))

        if self._config.pwux.com_port >= 1:
            case_temp = self._dev.pyrometer.read_temperature()
        else:
            case_temp = Temperature(float("nan"))

        hc_elec = ElectricMeasurement(
            current=self._dev.hps.measure_current(),
            voltage=self._dev.hps.measure_voltage(),
            power=self._dev.hps.measure_power(),
        )
        amd_elec = ElectricMeasurement(
            current=self._dev.aps.measure_current(),
            voltage=self._dev.aps.measure_voltage(),
            power=self._dev.aps.measure_power(),
        )

        return HCHardwareMetrics(
            ext_pressure=ext_pressure,
            sip_pressure=sip_pressure,
            case_temperature=case_temp,
            hc_electricity=hc_elec,
            amd_electricity=amd_elec,
        )

    def emergency_stop(self) -> None:
        """安全停止"""
        self._dev.hps.set_output(False)
        self._dev.aps.set_output(False)
