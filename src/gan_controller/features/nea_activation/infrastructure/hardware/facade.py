from gan_controller.common.calculations.physics import calculate_quantum_efficiency
from gan_controller.common.domain.electricity import ElectricMeasurement
from gan_controller.common.domain.quantity import Current, Time, Value
from gan_controller.common.domain.quantity.factory import Voltage
from gan_controller.common.domain.quantity.quantity import Quantity
from gan_controller.common.domain.quantity.unit_types import Ampere, Ohm, Volt
from gan_controller.common.hardware.processing.vacuum_reader import VacuumSensorReader
from gan_controller.common.schemas.app_config import DevicesConfig
from gan_controller.features.nea_activation.domain.config import (
    NEAConditionConfig,
    NEAControlConfig,
)
from gan_controller.features.nea_activation.domain.interface import INEAHardwareFacade
from gan_controller.features.nea_activation.domain.models import NEADevices, NEARunnerResult


class NEAHardwareFacade(INEAHardwareFacade):
    HV_READING_CORRECTION_FACTOR = 10000.0

    def __init__(self, devices: NEADevices, config: DevicesConfig) -> None:
        self._dev = devices
        self._config = config
        self._vacuum_reader = VacuumSensorReader(self._dev.logger, self._config.gm10)

    def setup_devices(self) -> None:
        """初期設定"""
        # レーザーの静的設定
        target_ch = self._config.ibeam.beam_ch
        self._dev.laser.set_channel_enable(target_ch, True)

        # 電源(AMD)の静的設定
        aps_config = self._config.aps
        self._dev.aps.set_voltage(aps_config.v_limit)
        self._dev.aps.set_ovp(aps_config.ovp)
        self._dev.aps.set_ocp(aps_config.ocp)

    def apply_control_params(self, params: NEAControlConfig) -> None:
        """パラメータの適用"""
        # レーザー制御
        self._dev.laser.set_channel_power(self._config.ibeam.beam_ch, params.laser_power_sv)

        # AMD電源の制御
        if params.amd_enable:
            self._dev.aps.set_current(params.amd_output_current)
            self._dev.aps.set_output(True)
        else:
            self._dev.aps.set_output(False)

    def set_laser_emission(self, enable: bool) -> None:
        self._dev.laser.set_emission(enable)

    def read_photocurrent(
        self, shunt_r: Quantity[Ohm], count: int, interval: float
    ) -> tuple[Quantity[Volt], Quantity[Ampere]]:
        """Photocurrentの電圧と電流を取得"""
        current_volt = self._dev.logger.read_integrated_voltage(
            self._config.gm10.pc_ch, count, interval
        )
        current_val = current_volt.base_value / shunt_r.base_value
        return current_volt, Current(current_val)

    def read_metrics(
        self,
        control_config: NEAControlConfig,
        condition_config: NEAConditionConfig,
        timestamp: float,
        bright_pc: Quantity[Ampere],
        bright_pc_voltage: Quantity[Volt],
        dark_pc: Quantity[Ampere],
        dark_pc_voltage: Quantity[Volt],
    ) -> NEARunnerResult:
        """各種センサー読み取りとResult生成"""
        # --- 計算 ---
        wavelength_nm = condition_config.laser_wavelength.value_as("n")
        laser_pv_watt = control_config.laser_power_pv.base_value

        pc_val = bright_pc.base_value - dark_pc.base_value
        pc_v_val = bright_pc_voltage.base_value - dark_pc_voltage.base_value

        qe_val = calculate_quantum_efficiency(
            current_amp=pc_val, laser_power_watt=laser_pv_watt, wavelength_nm=wavelength_nm
        )

        # --- センサー読み取り ---
        ext_pressure = self._vacuum_reader.read_ext_pressure()
        sip_pressure = self._vacuum_reader.read_sip_pressure()

        # HV読み取り (補正含む)
        hv_raw = self._dev.logger.read_voltage(self._config.gm10.hv_ch)
        extraction_voltage = Voltage(hv_raw.base_value * self.HV_READING_CORRECTION_FACTOR)

        # AMD電源の読み取り
        electricity = ElectricMeasurement(
            voltage=self._dev.aps.measure_voltage(),
            current=self._dev.aps.measure_current(),
            power=self._dev.aps.measure_power(),
        )

        return NEARunnerResult(
            timestamp=Time(timestamp),
            laser_power_sv=control_config.laser_power_sv,
            laser_power_pv=control_config.laser_power_pv,
            ext_pressure=ext_pressure,
            sip_pressure=sip_pressure,
            extraction_voltage=extraction_voltage,
            photocurrent=Current(pc_val),
            photocurrent_voltage=Voltage(pc_v_val),
            bright_pc=bright_pc,
            bright_pc_voltage=bright_pc_voltage,
            dark_pc=dark_pc,
            dark_pc_voltage=dark_pc_voltage,
            quantum_efficiency=Value(qe_val, "%"),
            amd_electricity=electricity,
        )

    def emergency_stop(self) -> None:
        """安全終了処理"""
        print("HardwareFacade: Executing Emergency Stop")
        try:
            self._dev.laser.set_emission(False)
        except Exception as e:  # noqa: BLE001
            print(f"Failed to stop laser: {e}")

        try:
            self._dev.aps.set_output(False)
        except Exception as e:  # noqa: BLE001
            print(f"Failed to stop APS: {e}")
