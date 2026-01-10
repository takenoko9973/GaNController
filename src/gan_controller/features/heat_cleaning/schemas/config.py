from typing import Annotated

from pydantic import BaseModel, Field

from gan_controller.common.domain.quantity import (
    Ampere,
    Current,
    Dimensionless,
    PydanticUnit,
    Quantity,
    Second,
    Time,
    Value,
)


class HCSequenceConfig(BaseModel):
    """シーケンスの設定値"""

    # hours = hour + s として登録している (設計上どうしようもなかった)
    # 気になるなら、common/sequenceパッケージを頑張って修正して
    rising_time: Annotated[
        Quantity[Second], *PydanticUnit("hours"), Field(description="昇温時間[h]")
    ] = Time(1, "hour")
    heating_time: Annotated[
        Quantity[Second], *PydanticUnit("hours"), Field(description="HeatCleaning時間[h]")
    ] = Time(1, "hour")
    decrease_time: Annotated[
        Quantity[Second], *PydanticUnit("hours"), Field(description="降温時間[h]")
    ] = Time(0.5, "hour")
    wait_time: Annotated[
        Quantity[Second], *PydanticUnit("hours"), Field(description="待機時間[h]")
    ] = Time(15, "hour")


class HCConditionConfig(BaseModel):
    """実験条件の設定値"""

    repeat_count: Annotated[
        Quantity[Dimensionless], *PydanticUnit(""), Field(description="繰り返し回数")
    ] = Value(1)
    logging_interval: Annotated[
        Quantity[Second], *PydanticUnit("s"), Field(description="ログ間隔[s]")
    ] = Time(10)

    # === HC電源
    hc_enabled: bool = Field(default=True, description="HC電流制御有効/無効")
    hc_current: Annotated[
        Quantity[Ampere], *PydanticUnit("A"), Field(description="HC電流値[A]")
    ] = Current(3)

    # === HC電源
    amd_enabled: bool = Field(default=True, description="AMD電流制御有効/無効")
    amd_current: Annotated[
        Quantity[Ampere], *PydanticUnit("A"), Field(description="AMD電流値[A]")
    ] = Current(3)


class HCLogConfig(BaseModel):
    """ログ設定パラメータ"""

    update_date_folder: bool = Field(default=False, description="日付フォルダを更新するか")
    update_major_number: bool = Field(default=False, description="実験のメジャー番号を更新するか")
    comment: str = Field(default="", exclude=True)


class ProtocolConfig(BaseModel):
    """プロトコルの設定値"""

    sequence: HCSequenceConfig = Field(default_factory=HCSequenceConfig)
    condition: HCConditionConfig = Field(default_factory=HCConditionConfig)
    log: HCLogConfig = Field(default_factory=HCLogConfig)
