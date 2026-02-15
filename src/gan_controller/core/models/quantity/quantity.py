from dataclasses import dataclass, field

from gan_controller.core.models.quantity.unit_types import UNIT_BY_SYMBOL

from .parser import split_unit
from .prefix_registry import PREFIX_REGISTRY


@dataclass
class Quantity[T]:
    _value_si: float = field(init=False)  # 接頭辞無しでの値
    unit: str = field(init=False)
    display_prefix: str = field(init=False)

    def __init__(self, value: float = 0.0, unit: str = "") -> None:
        prefix, base = split_unit(unit, PREFIX_REGISTRY.known_prefixes)
        PREFIX_REGISTRY.validate(prefix, base)  # %, ppm などに単位が存在するかチェック

        unit_type = UNIT_BY_SYMBOL[base]

        self._value_si = value * PREFIX_REGISTRY.get(prefix).scale
        self.unit = unit_type.symbol
        self.display_prefix = prefix
        self.display_unit = base

    @property
    def base_value(self) -> float:
        """基本単位(SI)での値を取得 (例: 1.2 mA なら 0.0012)"""
        return self._value_si

    @property
    def value(self) -> float:
        """現在の表示用接頭辞での値を取得 (例: 1.2 mA なら 1.2)"""
        return self.value_as(self.display_prefix)

    # ==================================================

    # === 変換処理

    def value_as(self, prefix: str = "") -> float:
        """指定の接頭辞で値を取得"""
        PREFIX_REGISTRY.validate(prefix, self.unit)
        return self._value_si / PREFIX_REGISTRY.get(prefix).scale

    # === 表示

    def _get_unit_suffix(self) -> str:
        """表示用の単位接尾辞を取得。設定により単位が隠されている場合は空文字を返す。"""
        spec = PREFIX_REGISTRY.get(self.display_prefix)
        if spec.unit_hidden:
            return ""

        return self.unit

    def __format__(self, format_spec: str) -> str:
        """f-string 時に呼ばれる"""
        value = self.value_as(self.display_prefix)
        formatted_value = format(value, format_spec)  # f-string で指定されたフォーマットを適用
        unit_str = f"{self.display_prefix}{self._get_unit_suffix()}"

        if unit_str == "":
            return f"{formatted_value}"
        return f"{formatted_value} {self.display_prefix}{self._get_unit_suffix()}"

    def __str__(self) -> str:
        value = self.value_as(self.display_prefix)
        unit_str = f"{self.display_prefix}{self._get_unit_suffix()}"

        if unit_str == "":
            return f"{value}"
        return f"{value} {self.display_prefix}{self._get_unit_suffix()}"
