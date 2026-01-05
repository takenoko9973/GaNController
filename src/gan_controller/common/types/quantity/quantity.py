from dataclasses import dataclass, field

from .parser import split_unit
from .prefix_registry import PREFIX_REGISTRY


@dataclass
class Quantity[T]:
    _value_si: float = field(init=False)  # 接頭辞無しでの値
    unit: str = field(init=False)
    display_prefix: str = field(init=False)

    def __init__(self, value: float = 0.0, unit: str = "") -> None:
        prefix, base = split_unit(unit, PREFIX_REGISTRY.known_prefixes)

        PREFIX_REGISTRY.validate(prefix, base)

        self._value_si = value * PREFIX_REGISTRY.get(prefix).scale
        self.unit = base
        self.display_prefix = prefix

    # === 変換処理

    def value_as(self, prefix: str = "") -> float:
        """指定の接頭辞で値を取得"""
        PREFIX_REGISTRY.validate(prefix, self.unit)
        return self._value_si / PREFIX_REGISTRY.get(prefix).scale

    def with_prefix(self, prefix: str) -> "Quantity":
        """表示用接頭辞を変更"""
        return Quantity(
            _value_si=self._value_si,
            unit=self.unit,
            display_prefix=prefix,
        )

    # === 表示

    def __format__(self, format_spec: str) -> str:
        """f-string 時に呼ばれる"""
        value = self.value_as(self.display_prefix)
        formatted_value = format(value, format_spec)  # f-string で指定されたフォーマットを適用
        return f"{formatted_value} {self.display_prefix}{self.unit}"

    def __str__(self) -> str:
        value = self.value_as(self.display_prefix)
        return f"{value} {self.display_prefix}{self.unit}"
