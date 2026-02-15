from typing import Any

from pydantic import BeforeValidator, PlainSerializer

from gan_controller.core.models.quantity.unit_types import UNIT_BY_SYMBOL

from .parser import split_unit
from .prefix_registry import PREFIX_REGISTRY
from .quantity import Quantity


def PydanticUnit(unit_str: str) -> tuple[BeforeValidator, PlainSerializer]:  # noqa: N802
    """Pydantic Annotated用のヘルパー"""
    target_prefix, target_base = split_unit(unit_str, PREFIX_REGISTRY.known_prefixes)
    target_unit_type = UNIT_BY_SYMBOL[target_base]

    # バリデータ (設定ファイルの数値 -> Quantity)
    def validate(v: Any) -> Quantity:  # noqa: ANN401
        if isinstance(v, Quantity):
            return v

        try:
            val = float(v)
        except (ValueError, TypeError) as e:
            msg = f"Number expected, got {v}"
            raise ValueError(msg) from e

        # 指定された単位 ("mm") でQuantityを作成
        return Quantity(val, unit_str)

    # シリアライザ (Quantity -> 設定ファイルの数値)
    def serialize(q: Quantity) -> float:
        # 単位の整合性チェック (実行時の確認)
        if q.unit != target_unit_type.symbol:
            msg = f"Unit mismatch: expected base '{target_base}' for {unit_str}, got '{q.unit}'"
            raise ValueError(msg)

        return q.value_as(target_prefix)

    # Pydanticへの指示セットを返す
    return (BeforeValidator(validate), PlainSerializer(serialize, return_type=float))
