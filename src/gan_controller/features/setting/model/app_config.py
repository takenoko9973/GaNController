import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from gan_controller.common.constants import APP_CONFIG_PATH
from gan_controller.common.utils.toml_config_io import load_toml_config, save_toml_config


# gm10 セクション
class GM10Config(BaseModel):
    ext_ch: int = Field(default=-1, description="真空度(EXT)測定Ch番号")
    sip_ch: int = Field(default=-1, description="SIP測定Ch番号")
    hv_ch: int = Field(default=-1, description="HV制御出力Ch番号")
    pc_ch: int = Field(default=-1, description="フォトカレント測定Ch番号")
    tc_ch: int = Field(default=-1, description="TC測定Ch番号")


# pfr_100l50 セクション
class PFR100l50Config(BaseModel):
    unit: int = Field(default=0)
    v_limit: float = Field(default=18, description="最大印加電圧[V]")
    ovp: float = Field(default=19, description="過電圧保護値[V]")
    ocp: float = Field(default=5.0, description="過電流保護値[A]")


class IBeamConfig(BaseModel):
    beam_ch: int = Field(default=2, description="ビームチャンネル")


# ======================================================================================


# [common] セクション
class CommonConfig(BaseModel):
    log_dir: str = Field(default="logs", description="ログディレクトリ")
    encode: str = Field(default="utf-8", description="ログファイルエンコード")
    tz_offset_hours: int = Field(default=9, description="タイムゾーン (JST)")

    def get_tz(self) -> datetime.timezone:
        return datetime.timezone(datetime.timedelta(hours=self.tz_offset_hours))


# [devices] セクション
class DevicesConfig(BaseModel):
    # [devices] 直下のキー
    gm10_visa: str = Field(
        default="TCPIP0::192.168.x.x::34434::SOCKET", description="Logger (gm10)"
    )
    hps_visa: str = Field(
        default="TCPIP0::192.168.x.x::2268::SOCKET", description="Heater Power Supply (pfr_100l50)"
    )
    aps_visa: str = Field(
        default="TCPIP0::192.168.x.x::2268::SOCKET", description="AMD Power Supply (pfr_100l50)"
    )
    pwux_com_port: int = Field(default=0, description="PWUX (Temp) COMポート番号")
    ibeam_com_port: int = Field(default=0, description="Laser (ibeam) COMポート番号")

    # ネストされたテーブル
    gm10: GM10Config = Field(default_factory=GM10Config, description="Logger (gm10)")
    hps: PFR100l50Config = Field(default_factory=PFR100l50Config, description="Heater Power Supply")
    amd: PFR100l50Config = Field(default_factory=PFR100l50Config, description="AMD Power Supply")
    ibeam: IBeamConfig = Field(default_factory=IBeamConfig, description="Toptica IBeam laser")


# ======================================================================================


class AppConfig(BaseModel):
    common: CommonConfig = Field(default_factory=CommonConfig)
    devices: DevicesConfig = Field(default_factory=DevicesConfig)

    @classmethod
    def load(cls, path: str | Path = APP_CONFIG_PATH) -> "AppConfig":
        return load_toml_config(cls, path)

    def save(self, path: str | Path = APP_CONFIG_PATH) -> None:
        save_toml_config(self, path)
