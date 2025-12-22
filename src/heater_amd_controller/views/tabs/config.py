from PySide6.QtCore import Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from heater_amd_controller.models.app_config import (
    AppConfig,
    CommonConfig,
    DevicesConfig,
    GM10Config,
    IBeamConfig,
    PFR100l50Config,
)


# ==========================================
# スクロールで値が変わらないカスタムウィジェット
# ==========================================
class NoScrollSpinBox(QSpinBox):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        suffix: str | None = None,
        minimum: int | None = None,
        maximum: int | None = None,
    ) -> None:
        super().__init__(
            parent,
            suffix=suffix,
            minimum=minimum,
            maximum=maximum,
        )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        event.ignore()


class NoScrollDoubleSpinBox(QDoubleSpinBox):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        suffix: str | None = None,
        decimals: int | None = None,
    ) -> None:
        super().__init__(
            parent,
            suffix=suffix,
            decimals=decimals,
        )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        event.ignore()


# ==========================================
# 各設定ページコンポーネント
# ==========================================
class GM10ConfigPage(QWidget):
    """GM10 (Logger) 設定画面"""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        # 接続設定
        conn_group = QGroupBox("接続設定")
        conn_form = QFormLayout()
        self.visa_edit = QLineEdit()
        conn_form.addRow("VISA Address:", self.visa_edit)
        conn_group.setLayout(conn_form)
        layout.addWidget(conn_group)

        # 詳細パラメータ
        param_group = QGroupBox("詳細パラメータ (チャンネル設定)")
        param_form = QFormLayout()

        self.ext_ch_spin = NoScrollSpinBox(minimum=-1, maximum=20)
        self.sip_ch_spin = NoScrollSpinBox(minimum=-1, maximum=20)
        self.pc_ch_spin = NoScrollSpinBox(minimum=-1, maximum=20)
        self.hv_ch_spin = NoScrollSpinBox(minimum=-1, maximum=20)
        self.tc_ch_spin = NoScrollSpinBox(minimum=-1, maximum=20)

        param_form.addRow("真空度 (EXT) Ch:", self.ext_ch_spin)
        param_form.addRow("SIP Ch:", self.sip_ch_spin)
        param_form.addRow("Photo Current Ch:", self.pc_ch_spin)
        param_form.addRow("HV Control Ch:", self.hv_ch_spin)
        param_form.addRow("TC Measure Ch:", self.tc_ch_spin)

        param_group.setLayout(param_form)
        layout.addWidget(param_group)
        layout.addStretch()


class PFRConfigPage(QWidget):
    """PFR-100L50 (Heater/AMD) 共通設定画面"""

    def __init__(self, title_suffix: str) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        # 接続設定
        conn_group = QGroupBox("接続設定")
        conn_form = QFormLayout()
        self.visa_edit = QLineEdit()
        conn_form.addRow("VISA Address:", self.visa_edit)
        conn_group.setLayout(conn_form)
        layout.addWidget(conn_group)

        # 詳細パラメータ
        param_group = QGroupBox(f"詳細パラメータ {title_suffix}")
        param_form = QFormLayout()

        self.unit_spin = NoScrollSpinBox(minimum=-10, maximum=10)
        self.v_limit_spin = NoScrollDoubleSpinBox(suffix=" V", decimals=2)
        self.ovp_spin = NoScrollDoubleSpinBox(suffix=" V", decimals=2)
        self.ocp_spin = NoScrollDoubleSpinBox(suffix=" A", decimals=2)

        param_form.addRow("Unit ID:", self.unit_spin)
        param_form.addRow("Max Voltage:", self.v_limit_spin)
        param_form.addRow("OVP (過電圧保護):", self.ovp_spin)
        param_form.addRow("OCP (過電流保護):", self.ocp_spin)

        param_group.setLayout(param_form)
        layout.addWidget(param_group)
        layout.addStretch()


class IBeamConfigPage(QWidget):
    """iBeam (Laser) 設定画面"""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        conn_group = QGroupBox("接続設定")
        conn_form = QFormLayout()
        self.port_edit = QLineEdit()
        conn_form.addRow("COM Port:", self.port_edit)
        conn_group.setLayout(conn_form)
        layout.addWidget(conn_group)

        param_group = QGroupBox("詳細パラメータ")
        param_form = QFormLayout()
        self.ch_spin = NoScrollSpinBox(minimum=1, maximum=4)
        param_form.addRow("Beam Channel:", self.ch_spin)
        param_group.setLayout(param_form)
        layout.addWidget(param_group)
        layout.addStretch()


class PWUXConfigPage(QWidget):
    """PWUX (Temp Controller) 設定画面"""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        conn_group = QGroupBox("接続設定")
        conn_form = QFormLayout()
        self.port_edit = QLineEdit()
        conn_form.addRow("COM Port:", self.port_edit)
        conn_group.setLayout(conn_form)
        layout.addWidget(conn_group)
        layout.addStretch()


class GeneralConfigPage(QWidget):
    """共通設定画面"""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        common_group = QGroupBox("共通設定 (Logging / System)")
        common_form = QFormLayout()

        self.log_dir_edit = QLineEdit()
        self.encode_edit = QLineEdit()
        self.tz_spin = NoScrollSpinBox(minimum=-12, maximum=14)

        common_form.addRow("ログ保存先:", self.log_dir_edit)
        common_form.addRow("ログエンコード:", self.encode_edit)
        common_form.addRow("タイムゾーン (JST=9):", self.tz_spin)

        common_group.setLayout(common_form)
        layout.addWidget(common_group)
        layout.addStretch()


# ==========================================
# ConfigTab クラス
# ==========================================
class ConfigTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.init_ui()

    def init_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        # --- ヘッダー ---
        header_layout = QHBoxLayout()
        self.btn_load = QPushButton("設定読み込み")
        self.btn_save = QPushButton("設定保存")
        header_layout.addStretch()
        header_layout.addWidget(self.btn_load)
        header_layout.addWidget(self.btn_save)
        main_layout.addLayout(header_layout)

        # --- コンテンツエリア ---
        content_layout = QHBoxLayout()

        # サイドバー
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)

        # スタックウィジェット
        self.stack = QStackedWidget()

        # ページのインスタンス化
        self.gm10_page = GM10ConfigPage()
        self.hps_page = PFRConfigPage("(Heater)")
        self.aps_page = PFRConfigPage("(AMD)")
        self.ibeam_page = IBeamConfigPage()
        self.pwux_page = PWUXConfigPage()
        self.general_page = GeneralConfigPage()

        # リスト登録 (タイトルとウィジェットのペア)
        pages = [
            ("GM10 (Logger)", self.gm10_page),
            ("HPS (Heater)", self.hps_page),
            ("APS (AMD)", self.aps_page),
            ("iBeam (Laser)", self.ibeam_page),
            ("PWUX (Temp Controller)", self.pwux_page),
            ("その他設定 (General)", self.general_page),
        ]
        for title, widget in pages:
            self.sidebar.addItem(title)
            self.stack.addWidget(widget)

        content_layout.addWidget(self.sidebar)
        content_layout.addWidget(self.stack)
        main_layout.addLayout(content_layout)

        # --- イベント接続 ---
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.btn_save.clicked.connect(self.save_settings)
        self.btn_load.clicked.connect(self.load_settings)

        # 初期化
        self.sidebar.setCurrentRow(0)
        try:
            self.load_settings()
        except Exception:  # noqa: BLE001
            self._set_ui_defaults()

    # ==========================================
    # Load / Save Logic
    # ==========================================
    def _set_ui_defaults(self) -> None:
        # GM10
        self.gm10_page.visa_edit.setText("TCPIP0::192.168.1.105::34434::SOCKET")
        self.gm10_page.ext_ch_spin.setValue(1)
        self.gm10_page.sip_ch_spin.setValue(2)
        # PFR 100L50
        self.hps_page.visa_edit.setText("TCPIP0::192.168.1.111::2268::SOCKET")
        self.aps_page.visa_edit.setText("TCPIP0::192.168.1.112::2268::SOCKET")
        # Others
        self.pwux_page.port_edit.setText("")
        self.ibeam_page.port_edit.setText("")
        # General
        self.general_page.log_dir_edit.setText("logs")
        self.general_page.encode_edit.setText("utf-8")
        self.general_page.tz_spin.setValue(9)

    def load_settings(self) -> None:
        config = AppConfig.load()

        # GM10
        self.gm10_page.visa_edit.setText(config.devices.gm10_visa)
        self.gm10_page.ext_ch_spin.setValue(config.devices.gm10.ext_ch)
        self.gm10_page.sip_ch_spin.setValue(config.devices.gm10.sip_ch)
        self.gm10_page.pc_ch_spin.setValue(config.devices.gm10.pc_ch)
        self.gm10_page.hv_ch_spin.setValue(config.devices.gm10.hv_ch)
        self.gm10_page.tc_ch_spin.setValue(config.devices.gm10.tc_ch)

        # HPS
        self.hps_page.visa_edit.setText(config.devices.hps_visa)
        self.hps_page.unit_spin.setValue(config.devices.hps.unit)
        self.hps_page.v_limit_spin.setValue(config.devices.hps.v_limit)
        self.hps_page.ovp_spin.setValue(config.devices.hps.ovp)
        self.hps_page.ocp_spin.setValue(config.devices.hps.ocp)

        # APS
        self.aps_page.visa_edit.setText(config.devices.aps_visa)
        self.aps_page.unit_spin.setValue(config.devices.amd.unit)
        self.aps_page.v_limit_spin.setValue(config.devices.amd.v_limit)
        self.aps_page.ovp_spin.setValue(config.devices.amd.ovp)
        self.aps_page.ocp_spin.setValue(config.devices.amd.ocp)

        # iBeam & PWUX
        self.ibeam_page.port_edit.setText(config.devices.ibeam_com_port)
        self.ibeam_page.ch_spin.setValue(config.devices.ibeam.beam_ch)
        self.pwux_page.port_edit.setText(config.devices.pwux_com_port)

        # General
        self.general_page.log_dir_edit.setText(config.common.log_dir)
        self.general_page.encode_edit.setText(config.common.encode)
        self.general_page.tz_spin.setValue(config.common.tz_offset_hours)

    def save_settings(self) -> None:
        try:
            config = AppConfig(
                common=CommonConfig(
                    log_dir=self.general_page.log_dir_edit.text(),
                    encode=self.general_page.encode_edit.text(),
                    tz_offset_hours=self.general_page.tz_spin.value(),
                ),
                devices=DevicesConfig(
                    gm10_visa=self.gm10_page.visa_edit.text(),
                    hps_visa=self.hps_page.visa_edit.text(),
                    aps_visa=self.aps_page.visa_edit.text(),
                    pwux_com_port=self.pwux_page.port_edit.text(),
                    ibeam_com_port=self.ibeam_page.port_edit.text(),
                    gm10=GM10Config(
                        ext_ch=self.gm10_page.ext_ch_spin.value(),
                        sip_ch=self.gm10_page.sip_ch_spin.value(),
                        pc_ch=self.gm10_page.pc_ch_spin.value(),
                        hv_ch=self.gm10_page.hv_ch_spin.value(),
                        tc_ch=self.gm10_page.tc_ch_spin.value(),
                    ),
                    hps=PFR100l50Config(
                        unit=self.hps_page.unit_spin.value(),
                        v_limit=self.hps_page.v_limit_spin.value(),
                        ovp=self.hps_page.ovp_spin.value(),
                        ocp=self.hps_page.ocp_spin.value(),
                    ),
                    amd=PFR100l50Config(
                        unit=self.aps_page.unit_spin.value(),
                        v_limit=self.aps_page.v_limit_spin.value(),
                        ovp=self.aps_page.ovp_spin.value(),
                        ocp=self.aps_page.ocp_spin.value(),
                    ),
                    ibeam=IBeamConfig(
                        beam_ch=self.ibeam_page.ch_spin.value(),
                    ),
                ),
            )
            config.save()
            QMessageBox.information(self, "完了", "設定を保存しました。")

        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "エラー", f"保存に失敗しました:\n{e}")
