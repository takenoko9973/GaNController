from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field

from gan_controller.common.constants import NEA_CONFIG_PATH
from gan_controller.common.types.quantity.factory import (
    Current,
    Length,
    Power,
    Resistance,
    Time,
    Value,
)
from gan_controller.common.types.quantity.quantity import Quantity
from gan_controller.common.types.quantity.schemas import PydanticUnit
from gan_controller.common.types.quantity.unit_types import (
    Ampere,
    Dimensionless,
    Meter,
    Ohm,
    Second,
    Watt,
)
from gan_controller.common.utils.toml_config_io import load_toml_config, save_toml_config


class NEAConditionConfig(BaseModel):
    """実験中不変の設定値"""

    shunt_resistance: Annotated[
        Quantity[Ohm], *PydanticUnit("kΩ"), Field(description="換算抵抗 (シャント抵抗)[kΩ]")
    ] = Resistance(10, "k")
    laser_wavelength: Annotated[
        Quantity[Meter], *PydanticUnit("nm"), Field(description="レーザー波長[nm]")
    ] = Length(406, "n")
    stabilization_time: Annotated[
        Quantity[Second], *PydanticUnit("s"), Field(description="安定化時間[s]")
    ] = Time(1.0)
    integration_count: Annotated[
        Quantity[Dimensionless], *PydanticUnit(""), Field(description="積算回数")
    ] = Value(5)
    integration_interval: Annotated[
        Quantity[Second], *PydanticUnit("s"), Field(description="積算間隔[s]")
    ] = Time(0.2)


class NEALogConfig(BaseModel):
    """ログ設定パラメータ"""

    update_date_folder: bool = Field(default=False, description="日付フォルダを更新するか")
    update_major_number: bool = Field(default=False, description="実験のメジャー番号を更新するか")
    comment: str = Field(default="", exclude=True)


class NEAControlConfig(BaseModel):
    """実行制御パラメータ (Runtime State)

    実験中のデバイス制御値や状態を保持する
    """

    amd_enable: bool = Field(default=False, exclude=True)  # AMDを有効化するか (設定には保存しない)
    amd_output_current: Annotated[
        Quantity[Ampere], *PydanticUnit("A"), Field(description="AMD電流[A]")
    ] = Current(3.5)
    laser_power_sv: Annotated[
        Quantity[Watt], *PydanticUnit("mW"), Field(description="レーザー設定出力[mW]")
    ] = Power(10, "m")
    laser_power_pv: Annotated[
        Quantity[Watt], *PydanticUnit("mW"), Field(description="レーザー実出力[mW]")
    ] = Power(3.01, "m")


class NEAConfig(BaseModel):
    """NEA活性化実験の設定 (保存対象)"""

    condition: NEAConditionConfig = Field(default_factory=NEAConditionConfig)
    log: NEALogConfig = Field(default_factory=NEALogConfig)
    control: NEAControlConfig = Field(default_factory=NEAControlConfig)

    @classmethod
    def load(cls, path: str | Path = NEA_CONFIG_PATH) -> "NEAConfig":
        return load_toml_config(cls, path)

    def save(self, path: str | Path = NEA_CONFIG_PATH) -> None:
        save_toml_config(self, path)
