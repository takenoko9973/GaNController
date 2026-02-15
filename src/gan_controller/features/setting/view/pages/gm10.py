from PySide6.QtWidgets import QFormLayout, QGroupBox, QLineEdit, QVBoxLayout, QWidget

from gan_controller.core.models.app_config import GM10Config
from gan_controller.presentation.components.widgets import NoScrollSpinBox


class GM10ConfigPage(QWidget):
    """GM10 (Logger) 設定画面"""

    visa_edit: QLineEdit

    ext_ch_spin: NoScrollSpinBox
    sip_ch_spin: NoScrollSpinBox
    pc_ch_spin: NoScrollSpinBox
    hv_ch_spin: NoScrollSpinBox
    tc_ch_spin: NoScrollSpinBox

    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)

        layout.addWidget(self._create_connection_config_group())
        layout.addWidget(self._create_channel_config_group())
        layout.addStretch()

    def _create_connection_config_group(self) -> QGroupBox:
        connection_config_group = QGroupBox("接続設定")
        connection_config_form = QFormLayout(connection_config_group)

        self.visa_edit = QLineEdit()
        connection_config_form.addRow("VISA Address :", self.visa_edit)

        return connection_config_group

    def _create_channel_config_group(self) -> QGroupBox:
        channel_config_group = QGroupBox("チャンネル設定 (0以下で無効化)")
        channel_config_form = QFormLayout(channel_config_group)

        self.ext_ch_spin = NoScrollSpinBox(minimum=-1, maximum=20)
        self.sip_ch_spin = NoScrollSpinBox(minimum=-1, maximum=20)
        self.hv_ch_spin = NoScrollSpinBox(minimum=-1, maximum=20)
        self.pc_ch_spin = NoScrollSpinBox(minimum=-1, maximum=20)
        self.tc_ch_spin = NoScrollSpinBox(minimum=-1, maximum=20)

        channel_config_form.addRow("真空度 (EXT) Ch :", self.ext_ch_spin)
        channel_config_form.addRow("真空度 (SIP) Ch :", self.sip_ch_spin)
        channel_config_form.addRow("HV Control Ch :", self.hv_ch_spin)
        channel_config_form.addRow("Photo Current Ch :", self.pc_ch_spin)
        channel_config_form.addRow("TC Measure Ch :", self.tc_ch_spin)

        return channel_config_group

    # =============================================================================

    def get_config(self) -> GM10Config:
        return GM10Config(
            visa=self.visa_edit.text(),
            ext_ch=self.ext_ch_spin.value(),
            sip_ch=self.sip_ch_spin.value(),
            pc_ch=self.pc_ch_spin.value(),
            hv_ch=self.hv_ch_spin.value(),
            tc_ch=self.tc_ch_spin.value(),
        )

    def set_config(self, config: GM10Config) -> None:
        self.visa_edit.setText(config.visa)

        self.ext_ch_spin.setValue(config.ext_ch)
        self.sip_ch_spin.setValue(config.sip_ch)
        self.pc_ch_spin.setValue(config.pc_ch)
        self.hv_ch_spin.setValue(config.hv_ch)
        self.tc_ch_spin.setValue(config.tc_ch)
