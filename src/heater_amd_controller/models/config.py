import datetime
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field


# gm10 セクション
class GM10Config(BaseModel):
    ext_ch: int = Field(description="真空度測定Ch番号")
    sip_ch: int = Field(description="SIP測定Ch番号")
    pc_ch: int = Field(description="フォトカレント測定Ch番号")
    hv_ch: int = Field(description="HV制御出力Ch番号")
    tc_ch: int = Field(description="TC測定Ch番号")


# pfr_100l50 セクション
class PFR100l50Config(BaseModel):
    unit: int
    v_limit: float = Field(description="最大印加電圧[V]")
    ovp: float = Field(description="過電圧保護値[V]")
    ocp: float = Field(description="過電流保護値[A]")


class IBeamConfig(BaseModel):
    beam_ch: int = Field(description="ビームチャンネル")


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
    gm10_visa: str = Field(description="Logger (gm10)")
    hps_visa: str = Field(description="Heater Power Supply (pfr_100l50)")
    aps_visa: str = Field(description="AMD Power Supply (pfr_100l50)")
    pwux_com_port: int = Field(description="PWUX (Temp) COMポート番号")
    ibeam_com_port: int = Field(description="Laser (ibeam) COMポート番号")

    # ネストされたテーブル
    gm10: GM10Config
    hps: PFR100l50Config  # Heater power supply
    amd: PFR100l50Config
    ibeam: IBeamConfig


class Config(BaseModel):
    common: CommonConfig
    devices: DevicesConfig

    @classmethod
    def load_config(cls, config_path: str | Path) -> "Config":
        try:
            with Path(config_path).open("rb") as f:
                data = tomllib.load(f)
                return cls.model_validate(data)

        except FileNotFoundError:
            print(f"エラー: 設定ファイルが見つかりません: {config_path}")
            raise
        except Exception as e:
            print(f"エラー: 設定ファイルの読み込みまたは検証に失敗しました: {e}")
            raise
