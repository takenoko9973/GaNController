from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator

from gan_controller.core.constants import NEA_CONFIG_PATH
from gan_controller.core.domain.quantity import (
    Ampere,
    Current,
    Dimensionless,
    Length,
    Meter,
    Ohm,
    Power,
    PydanticUnit,
    Quantity,
    Resistance,
    Second,
    Time,
    Value,
    Volt,
    Voltage,
    Watt,
)
from gan_controller.infrastructure.persistence.toml_config_io import (
    load_toml_config,
    save_toml_config,
)


class NEAConditionConfig(BaseModel):
    """実験中不変の設定値"""

    shunt_resistance: Annotated[
        Quantity[Ohm], *PydanticUnit("kΩ"), Field(description="換算抵抗 (シャント抵抗)[kΩ]")
    ] = Resistance(10, "k")
    laser_wavelength: Annotated[
        Quantity[Meter], *PydanticUnit("nm"), Field(description="レーザー波長[nm]")
    ] = Length(406, "n")
    is_fixed_background: bool = Field(
        default=False, description="Photocurrentバックグラウンドの固定"
    )
    fixed_background_volt: Annotated[
        Quantity[Volt], *PydanticUnit("mV"), Field(description="Photocurrentバックグラウンド[mV]")
    ] = Voltage(1.5, "mV")
    stabilization_time: Annotated[
        Quantity[Second], *PydanticUnit("s"), Field(description="安定化時間[s]")
    ] = Time(1.0)
    integration_count: Annotated[
        Quantity[Dimensionless], *PydanticUnit(""), Field(description="積算回数")
    ] = Value(5)
    integration_interval: Annotated[
        Quantity[Second], *PydanticUnit("s"), Field(description="積算間隔[s]")
    ] = Time(0.2)

    @field_validator("shunt_resistance")
    @classmethod
    def validate_resistance(cls, v: Quantity[Dimensionless]) -> Quantity[Dimensionless]:
        """抵抗値は正の数"""
        if v.base_value <= 0:
            msg = "Resistance must be > 0"
            raise ValueError(msg)

        return v

    @field_validator("laser_wavelength")
    @classmethod
    def validate_wavelength(cls, v: Quantity[Dimensionless]) -> Quantity[Dimensionless]:
        """波長は正の数"""
        if v.base_value <= 0:
            msg = "Wavelength must be > 0"
            raise ValueError(msg)

        return v

    @field_validator("integration_count")
    @classmethod
    def validate_count(cls, v: Quantity[Dimensionless]) -> Quantity[Dimensionless]:
        """積算回数は正の整数"""
        if v.base_value < 1:
            msg = "Integration count must be >= 1"
            raise ValueError(msg)

        return v

    @field_validator("stabilization_time", "integration_interval")
    @classmethod
    def validate_time(cls, v: Quantity[Second]) -> Quantity[Second]:
        """秒数は非負"""
        if v.base_value < 0:
            msg = "Time cannot be negative"
            raise ValueError(msg)

        return v


class NEALogConfig(BaseModel):
    """ログ設定パラメータ"""

    update_date_folder: bool = Field(default=False, description="日付フォルダを更新するか")
    update_major_number: bool = Field(default=False, description="実験のメジャー番号を更新するか")
    comment: str = Field(default="", exclude=True)


class NEAControlConfig(BaseModel):
    """
    実行制御パラメータ (Runtime State)

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

    @field_validator("amd_output_current")
    @classmethod
    def validate_count(cls, v: Quantity[Dimensionless]) -> Quantity[Dimensionless]:
        """電流値は非負"""
        if v.base_value < 0:
            msg = "Current cannot be negative"
            raise ValueError(msg)

        return v

    @field_validator("laser_power_sv", "laser_power_pv")
    @classmethod
    def validate_time(cls, v: Quantity[Second]) -> Quantity[Second]:
        """電力は非負"""
        if v.base_value < 0:
            msg = "Power cannot be negative"
            raise ValueError(msg)

        return v


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
