# 使用可能な単位
BASE_UNITS = {
    "": "dimensionless",
    "A": "current",
    "V": "voltage",
    "W": "power",
    "s": "time",
    "m": "length",
    "Pa": "pressure",
    "Ω": "resistance",
    "℃": "celsius",
}


def split_unit(unit: str, known_prefixes: set[str]) -> tuple[str, str]:
    """接頭辞と単位を分離"""
    # 無次元
    if unit in known_prefixes:
        return unit, ""

    # 単位部分を検索
    dimension_units = BASE_UNITS.keys() - {""}  # 無次元を除いた単位
    for base in sorted(dimension_units, key=len, reverse=True):  # 長い単位から先に見る (Pa)
        if unit.endswith(base):
            prefix = unit[: -len(base)]
            if prefix in known_prefixes:
                return prefix, base

    msg = f"Invalid unit: {unit}"
    raise ValueError(msg)
