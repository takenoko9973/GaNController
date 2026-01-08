import datetime
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field

from gan_controller.common.constants import APP_CONFIG_PATH
from gan_controller.common.domain.quantity import (
    Ampere,
    Current,
    PydanticUnit,
    Quantity,
    Volt,
    Voltage,
)
from gan_controller.common.io.toml_config_io import load_toml_config, save_toml_config


# gm10 セクション
class GM10Config(BaseModel):
    visa: str = Field(default="TCPIP0::192.168.x.x::34434::SOCKET", description="VISAアドレス")
    ext_ch: int = Field(default=-1, description="真空度(EXT)測定Ch番号")
    sip_ch: int = Field(default=-1, description="SIP測定Ch番号")
    hv_ch: int = Field(default=-1, description="HV制御出力Ch番号")
    pc_ch: int = Field(default=-1, description="フォトカレント測定Ch番号")
    tc_ch: int = Field(default=-1, description="TC測定Ch番号")


# pfr_100l50 セクション
class PFR100l50Config(BaseModel):
    visa: str = Field(default="", description="VISAアドレス")
    unit: int = Field(default=0)
    v_limit: Annotated[Quantity[Volt], *PydanticUnit("V"), Field(description="最大印加電圧[V]")] = (
        Voltage(18)
    )
    ovp: Annotated[Quantity[Volt], *PydanticUnit("V"), Field(description="過電圧保護値[V]")] = (
        Voltage(19)
    )
    ocp: Annotated[Quantity[Ampere], *PydanticUnit("A"), Field(description="過電流保護値[A]")] = (
        Current(5)
    )


class IBeamConfig(BaseModel):
    com_port: int = Field(default=0, description="COMポート番号 (0=無効化)")
    beam_ch: int = Field(default=2, description="ビームチャンネル")


class PWUXConfig(BaseModel):
    com_port: int = Field(default=0, description="COMポート番号 (0=無効化)")


# ======================================================================================


# [common] セクション
class CommonConfig(BaseModel):
    encode: str = Field(default="utf-8", description="ログファイルエンコード")
    tz_offset_hours: int = Field(default=9, description="タイムゾーン (JST)")
    is_simulation_mode: bool = Field(
        default=False, description="デバック用 (シミュレーションモード)"
    )

    def get_tz(self) -> datetime.timezone:
        return datetime.timezone(datetime.timedelta(hours=self.tz_offset_hours))


# [devices] セクション
class DevicesConfig(BaseModel):
    gm10: GM10Config = Field(default_factory=GM10Config, description="Logger (gm10)")
    hps: PFR100l50Config = Field(
        default_factory=lambda: PFR100l50Config(
            visa="TCPIP0::192.168.x.x::2268::SOCKET",  # HPS用デフォルト
            ocp=Current(10),
        ),
        description="Heater Power Supply",
    )
    aps: PFR100l50Config = Field(
        default_factory=lambda: PFR100l50Config(
            visa="TCPIP0::192.168.x.x::2268::SOCKET",  # AMD用デフォルト
            ocp=Current(5),
        ),
        description="AMD Power Supply",
    )
    ibeam: IBeamConfig = Field(default_factory=IBeamConfig, description="Toptica IBeam laser")
    pwux: PWUXConfig = Field(default_factory=PWUXConfig, description="PWUX")


# ======================================================================================


class AppConfig(BaseModel):
    common: CommonConfig = Field(default_factory=CommonConfig)
    devices: DevicesConfig = Field(default_factory=DevicesConfig)

    @classmethod
    def load(cls, path: str | Path = APP_CONFIG_PATH) -> "AppConfig":
        return load_toml_config(cls, path)

    def save(self, path: str | Path = APP_CONFIG_PATH) -> None:
        save_toml_config(self, path)
