from gan_controller.core.domain.app_config import DevicesConfig
from gan_controller.core.domain.quantity import Celsius, Quantity, Volt, Watt
from gan_controller.features.manual_operation.domain.interface import IManualHardwareFacade
from gan_controller.features.manual_operation.domain.models import ManualDevices


class ManualHardwareFacade(IManualHardwareFacade):
    def __init__(self, devices: ManualDevices, config: DevicesConfig) -> None:
        self._dev = devices
        self._config = config

    def setup_devices(self) -> None:
        target_ch = self._config.ibeam.beam_ch
        self._dev.laser.set_channel_enable(target_ch, True)
        self._dev.laser.set_emission(False)

    def read_gm10_values(self) -> dict[str, Quantity[Volt]]:
        gm10 = self._config.gm10
        return {
            "ext": self._dev.logger.read_voltage(gm10.ext_ch),
            "sip": self._dev.logger.read_voltage(gm10.sip_ch),
            "hv": self._dev.logger.read_voltage(gm10.hv_ch),
            "pc": self._dev.logger.read_voltage(gm10.pc_ch),
            "tc": self._dev.logger.read_voltage(gm10.tc_ch),
        }

    def read_pwux_temperature(self) -> Quantity[Celsius]:
        return self._dev.pyrometer.read_temperature()

    def set_pwux_pointer(self, enable: bool) -> None:
        self._dev.pyrometer.set_pointer(enable)

    def set_laser_power(self, power: Quantity[Watt]) -> None:
        target_ch = self._config.ibeam.beam_ch
        self._dev.laser.set_channel_power(target_ch, power)

    def set_laser_emission(self, enable: bool) -> None:
        self._dev.laser.set_emission(enable)

    def emergency_stop(self) -> None:
        target_ch = self._config.ibeam.beam_ch
        try:
            self._dev.laser.set_emission(False)
        except Exception as e:  # noqa: BLE001
            print(f"Failed to stop laser emission: {e}")

        try:
            self._dev.laser.set_channel_enable(target_ch, False)
        except Exception as e:  # noqa: BLE001
            print(f"Failed to disable laser channel: {e}")
