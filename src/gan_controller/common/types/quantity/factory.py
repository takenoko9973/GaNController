from .quantity import Quantity
from .unit_types import (
    Ampere,
    Celsius,
    Dimensionless,
    Meter,
    Ohm,
    Pascal,
    Second,
    UnitBase,
    Volt,
    Watt,
)


def _make(val: float, prefix: str, unit_type: type[UnitBase]) -> Quantity:
    """内部ヘルパー: 単位クラスの情報を使ってQuantityを生成"""
    # クラス定義からシンボルを取得 ("A", "V" 等)
    base_symbol = unit_type.symbol
    return Quantity[unit_type](val, f"{prefix}{base_symbol}")


# === ファクトリ関数 ===
def Current(value: float, prefix: str = "") -> Quantity[Ampere]:  # noqa: N802
    return _make(value, prefix, Ampere)


def Voltage(value: float, prefix: str = "") -> Quantity[Volt]:  # noqa: N802
    return _make(value, prefix, Volt)


def Power(value: float, prefix: str = "") -> Quantity[Watt]:  # noqa: N802
    return _make(value, prefix, Watt)


def Time(value: float, prefix: str = "") -> Quantity[Second]:  # noqa: N802
    return _make(value, prefix, Second)


def Pressure(value: float, prefix: str = "") -> Quantity[Pascal]:  # noqa: N802
    return _make(value, prefix, Pascal)


def Resistance(value: float, prefix: str = "") -> Quantity[Ohm]:  # noqa: N802
    return _make(value, prefix, Ohm)


def Temperature(value: float, prefix: str = "") -> Quantity[Celsius]:  # noqa: N802
    return _make(value, prefix, Celsius)


def Length(value: float, prefix: str = "") -> Quantity[Meter]:  # noqa: N802
    return _make(value, prefix, Meter)


def Value(value: float, prefix: str = "") -> Quantity[Dimensionless]:  # noqa: N802
    return _make(value, prefix, Dimensionless)
