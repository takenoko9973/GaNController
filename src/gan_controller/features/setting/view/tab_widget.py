from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from gan_controller.features.setting.model.app_config import (
    AppConfig,
    CommonConfig,
    DevicesConfig,
    GM10Config,
    IBeamConfig,
    PFR100l50Config,
)
from gan_controller.features.setting.view.layouts import SettingLayout


class SettingsTab(QWidget):
    """設定タブの見た目制御"""

    # === 要素
    _main_layout: SettingLayout

    # === シグナル
    load_requested = Signal()
    save_requested = Signal()

    def __init__(self) -> None:
        super().__init__()

        self._main_layout = SettingLayout()
        self.setLayout(self._main_layout)

        self._init_connect()

    def _init_connect(self) -> None:
        self._main_layout.btn_load.clicked.connect(self.load_requested.emit)
        self._main_layout.btn_save.clicked.connect(self.save_requested.emit)

    def set_config(self, config: AppConfig) -> None:
        """Configの内容を各ページのウィジェットにセット"""
        # 1. Common
        self._main_layout.general_page.encode_edit.setText(config.common.encode)
        self._main_layout.general_page.tz_spin.setValue(config.common.tz_offset_hours)
        self._main_layout.general_page.is_simulation = config.common.is_simulation_mode

        # 2. Devices - GM10
        self._main_layout.gm10_page.visa_edit.setText(config.devices.gm10_visa)
        self._main_layout.gm10_page.ext_ch_spin.setValue(config.devices.gm10.ext_ch)
        self._main_layout.gm10_page.sip_ch_spin.setValue(config.devices.gm10.sip_ch)
        self._main_layout.gm10_page.pc_ch_spin.setValue(config.devices.gm10.pc_ch)
        self._main_layout.gm10_page.hv_ch_spin.setValue(config.devices.gm10.hv_ch)
        self._main_layout.gm10_page.tc_ch_spin.setValue(config.devices.gm10.tc_ch)

        # 3. Devices - HPS (Heater)
        self._main_layout.hps_page.visa_address_edit.setText(config.devices.hps_visa)
        self._main_layout.hps_page.unit_spin.setValue(config.devices.hps.unit)
        self._main_layout.hps_page.v_limit_spin.setValue(config.devices.hps.v_limit)
        self._main_layout.hps_page.ovp_spin.setValue(config.devices.hps.ovp)
        self._main_layout.hps_page.ocp_spin.setValue(config.devices.hps.ocp)

        # 4. Devices - APS (AMD)
        self._main_layout.aps_page.visa_address_edit.setText(config.devices.aps_visa)
        self._main_layout.aps_page.unit_spin.setValue(config.devices.amd.unit)
        self._main_layout.aps_page.v_limit_spin.setValue(config.devices.amd.v_limit)
        self._main_layout.aps_page.ovp_spin.setValue(config.devices.amd.ovp)
        self._main_layout.aps_page.ocp_spin.setValue(config.devices.amd.ocp)

        # 5. Devices - iBeam
        self._main_layout.ibeam_page.com_number_edit.setValue(config.devices.ibeam_com_port)
        self._main_layout.ibeam_page.beam_channel_spin.setValue(config.devices.ibeam.beam_ch)

        # 6. Devices - PWUX
        self._main_layout.pwux_page.com_number_edit.setValue(config.devices.pwux_com_port)

    def create_config_from_ui(self) -> AppConfig:
        """UIの値からConfigオブジェクトを構築"""
        # Common
        common = CommonConfig(
            encode=self._main_layout.general_page.encode_edit.text(),
            tz_offset_hours=self._main_layout.general_page.tz_spin.value(),
            is_simulation_mode=self._main_layout.general_page.is_simulation,
        )

        # GM10 Config
        gm10_config = GM10Config(
            ext_ch=self._main_layout.gm10_page.ext_ch_spin.value(),
            sip_ch=self._main_layout.gm10_page.sip_ch_spin.value(),
            pc_ch=self._main_layout.gm10_page.pc_ch_spin.value(),
            hv_ch=self._main_layout.gm10_page.hv_ch_spin.value(),
            tc_ch=self._main_layout.gm10_page.tc_ch_spin.value(),
        )

        # HPS Config
        hps_config = PFR100l50Config(
            unit=self._main_layout.hps_page.unit_spin.value(),
            v_limit=self._main_layout.hps_page.v_limit_spin.value(),
            ovp=self._main_layout.hps_page.ovp_spin.value(),
            ocp=self._main_layout.hps_page.ocp_spin.value(),
        )

        # AMD Config
        amd_config = PFR100l50Config(
            unit=self._main_layout.aps_page.unit_spin.value(),
            v_limit=self._main_layout.aps_page.v_limit_spin.value(),
            ovp=self._main_layout.aps_page.ovp_spin.value(),
            ocp=self._main_layout.aps_page.ocp_spin.value(),
        )

        # iBeam Config
        ibeam_config = IBeamConfig(beam_ch=self._main_layout.ibeam_page.beam_channel_spin.value())

        # Devices (Root)
        devices = DevicesConfig(
            gm10_visa=self._main_layout.gm10_page.visa_edit.text(),
            hps_visa=self._main_layout.hps_page.visa_address_edit.text(),
            aps_visa=self._main_layout.aps_page.visa_address_edit.text(),
            pwux_com_port=self._main_layout.pwux_page.com_number_edit.value(),
            ibeam_com_port=self._main_layout.ibeam_page.com_number_edit.value(),
            gm10=gm10_config,
            hps=hps_config,
            amd=amd_config,
            ibeam=ibeam_config,
        )

        return AppConfig(common=common, devices=devices)
