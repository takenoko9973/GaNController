from gan_controller.core.models.app_config import DevicesConfig
from gan_controller.core.models.electricity import ElectricMeasurement
from gan_controller.core.models.quantity import (
    Ampere,
    Current,
    Pressure,
    Quantity,
    Temperature,
)
from gan_controller.core.services.vacuum import (
    calc_ext_pressure_from_voltage,
    calc_sip_pressure_from_voltage,
)
from gan_controller.features.heat_cleaning.domain.config import ProtocolConfig
from gan_controller.features.heat_cleaning.domain.interface import IHCHardwareFacade
from gan_controller.features.heat_cleaning.domain.models import HCDevices, HCExperimentResult


class HCHardwareFacade(IHCHardwareFacade):
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

    def set_currents(
        self, hc_current: Quantity[Ampere] | None, amd_current: Quantity[Ampere] | None
    ) -> None:
        """指定された電流値を各電源に設定する"""
        # HC電源 (HPS)
        if hc_current:
            self._dev.hps.set_current(hc_current)

        # AMD電源 (APS)
        if amd_current:
            self._dev.aps.set_current(amd_current)

    def read_metrics(self) -> HCExperimentResult:
        """インターフェースの実装: 測定値を集めてResultオブジェクトを作る"""
        # 1. 圧力の計算 (電圧 -> 圧力変換)
        ext_val = self._dev.logger.read_voltage(self._config.gm10.ext_ch)
        ext_pressure = Pressure(calc_ext_pressure_from_voltage(ext_val.base_value))

        sip_val = self._dev.logger.read_voltage(self._config.gm10.sip_ch)
        sip_pressure = Pressure(calc_sip_pressure_from_voltage(sip_val.base_value))

        # 2. 温度の取得 (接続されていない場合はnan)
        if self._config.pwux.com_port >= 1:
            case_temp = self._dev.pyrometer.read_temperature()
        else:
            case_temp = Temperature(float("nan"))

        # 3. 電源情報の取得
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

        # Resultオブジェクトの生成
        # sequence_indexなどはRunner側で埋めるため、仮として初期値やNoneを入れておく
        return HCExperimentResult(
            sequence_index=0,  # Runnerが設定
            sequence_name="",  # Runnerが設定
            timestamp_step=Quantity(0.0, "s"),  # Runnerが設定
            timestamp_total=Quantity(0.0, "s"),  # Runnerが設定
            pressure_ext=ext_pressure,
            pressure_sip=sip_pressure,
            temperature_case=case_temp,
            electricity_hc=hc_elec,
            electricity_amd=amd_elec,
        )

    def emergency_stop(self) -> None:
        """インターフェースの実装: 安全停止"""
        print("HardwareAdapter: Executing Emergency Stop")
        try:
            self._dev.hps.set_output(False)
        except Exception as e:  # noqa: BLE001
            print(f"Failed to stop HPS: {e}")

        try:
            self._dev.aps.set_output(False)
        except Exception as e:  # noqa: BLE001
            print(f"Failed to stop APS: {e}")
