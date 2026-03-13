# 使用可能な単位
from .unit_types import ALL_UNIT_TYPES

BASE_UNITS: set[str] = {u.symbol for u in ALL_UNIT_TYPES}


def split_unit(unit: str, known_prefixes: set[str]) -> tuple[str, str]:
    """接頭辞と単位を分離"""
    # 「単位」として完全一致するか確認 (例: "m" は接頭辞ミリではなくメートルとして認識させる)
    if unit in BASE_UNITS and unit != "":
        return "", unit

    # 無次元
    if unit in known_prefixes:
        return unit, ""

    # 単位部分を検索
    dimension_units: set[str] = BASE_UNITS - {""}
    for base in sorted(dimension_units, key=len, reverse=True):  # 長い単位から先に見る (Pa)
        base_str = str(base)
        if unit.endswith(base_str):
            prefix = unit[: -len(base_str)]
            if prefix in known_prefixes:
                return prefix, base_str

    msg = f"Invalid unit: {unit}"
    raise ValueError(msg)
