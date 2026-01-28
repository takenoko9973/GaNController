from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field

from gan_controller.common.constants import PROTOCOLS_DIR
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
from gan_controller.common.io.toml_config_io import load_toml_config, save_toml_config
from gan_controller.features.heat_cleaning.domain import Sequence, SequenceMode


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

    def get_sequence_time(self, mode: SequenceMode) -> Quantity[Second]:
        if mode == SequenceMode.RISING:
            return self.rising_time
        if mode == SequenceMode.HEAT_CLEANING:
            return self.heating_time
        if mode == SequenceMode.DECREASE:
            return self.decrease_time
        if mode == SequenceMode.WAIT:
            return self.wait_time

        msg = "Unknown SequenceMode"
        raise ValueError(msg)


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

    def get_sequences(self) -> list[Sequence]:
        sequences = []

        repeat_count = int(self.condition.repeat_count.base_value)
        for _ in range(repeat_count):
            for sequence_mode in SequenceMode:
                sequence_time = self.sequence.get_sequence_time(sequence_mode)
                sequence = Sequence.create(sequence_mode, sequence_time.base_value, 0.33)
                sequences.append(sequence)

        return sequences

    @classmethod
    def load(cls, file_name: str, config_dir: str | Path = PROTOCOLS_DIR) -> "ProtocolConfig":
        path = Path(config_dir) / file_name
        return load_toml_config(cls, path)

    def save(self, file_name: str, config_dir: str | Path = PROTOCOLS_DIR) -> None:
        path = Path(config_dir) / file_name
        save_toml_config(self, path)
