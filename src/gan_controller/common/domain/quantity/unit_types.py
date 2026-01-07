class UnitBase:
    """全ての単位の基底クラス"""

    symbol: str = ""
    name: str = ""


# === 基本単位 ===
class Dimensionless(UnitBase):
    symbol = ""
    name = "dimensionless"


class Ampere(UnitBase):
    symbol = "A"
    name = "current"


class Volt(UnitBase):
    symbol = "V"
    name = "voltage"


class Watt(UnitBase):
    symbol = "W"
    name = "power"


class Second(UnitBase):
    symbol = "s"
    name = "time"


class Meter(UnitBase):
    symbol = "m"
    name = "length"


class Pascal(UnitBase):
    symbol = "Pa"
    name = "pressure"


class Ohm(UnitBase):
    symbol = "Ω"
    name = "resistance"


class Celsius(UnitBase):
    symbol = "℃"
    name = "celsius"


# システムで使用する全単位クラスのリスト
ALL_UNIT_TYPES: list[type[UnitBase]] = [
    Dimensionless,
    Ampere,
    Volt,
    Watt,
    Second,
    Meter,
    Pascal,
    Ohm,
    Celsius,
]
