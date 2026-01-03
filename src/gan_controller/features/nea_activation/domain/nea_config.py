from pathlib import Path

from pydantic import BaseModel, Field

from gan_controller.common.constants import NEA_CONFIG_PATH
from gan_controller.common.types.quantity import Quantity
from gan_controller.common.utils.toml_config_io import load_toml_config, save_toml_config


# ===============================================
#  1. 保存対象の設定 (Persistent Configuration)
#  Pydanticを使用: JSON保存、単位定義、バリデーション用
# ===============================================
class NEAConfig(BaseModel):
    """NEA活性化実験の設定 (保存対象)"""

    # --- Condition Settings (実験条件) ---
    shunt_resistance: float = Field(
        default=10.0, description="換算抵抗 (シャント抵抗)", json_schema_extra={"unit": "kΩ"}
    )
    laser_wavelength: float = Field(
        default=406.0, description="レーザー波長", json_schema_extra={"unit": "nm"}
    )
    stabilization_time: float = Field(
        default=1.0, description="安定化時間", json_schema_extra={"unit": "s"}
    )
    integration_count: int = Field(
        default=1, description="積算回数", json_schema_extra={"unit": ""}
    )
    integration_interval: float = Field(
        default=0.1, description="積算間隔", json_schema_extra={"unit": "s"}
    )

    # --- Execution Initial Values (実行制御の初期値) ---
    amd_output_current: float = Field(
        default=3.5, description="AMD電流", json_schema_extra={"unit": "A"}
    )
    laser_power_sv: float = Field(
        default=30.0, description="レーザー設定出力", json_schema_extra={"unit": "mW"}
    )
    laser_power_output: float = Field(
        default=10.0, description="レーザー実出力", json_schema_extra={"unit": "mW"}
    )

    # --- Helper Methods ---
    @classmethod
    def load(cls, path: str | Path = NEA_CONFIG_PATH) -> "NEAConfig":
        return load_toml_config(cls, path)

    def save(self, path: str | Path = NEA_CONFIG_PATH) -> None:
        save_toml_config(self, path)

    def get_quantity(self, field_name: str) -> Quantity:
        """指定したフィールドの値をQuantityとして取得"""
        value = getattr(self, field_name)
        unit = self.get_unit(field_name)
        return Quantity(value=value, unit=unit)

    def get_unit(self, field_name: str) -> str:
        """指定したフィールドの単位文字列を取得"""
        field_info = NEAConfig.model_fields[field_name]
        if field_info.json_schema_extra:
            return field_info.json_schema_extra.get("unit", "")

        return ""
