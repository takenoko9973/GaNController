# 使用可能な単位
from .unit_types import ALL_UNIT_TYPES

BASE_UNITS = {u.symbol for u in ALL_UNIT_TYPES}


def split_unit(unit: str, known_prefixes: set[str]) -> tuple[str, str]:
    """接頭辞と単位を分離"""
    # 「単位」として完全一致するか確認 (例: "m" は接頭辞ミリではなくメートルとして認識させる)
    if unit in BASE_UNITS and unit != "":
        return "", unit

    # 無次元
    if unit in known_prefixes:
        return unit, ""

    # 単位部分を検索
    dimension_units = BASE_UNITS - {""}
    for base in sorted(dimension_units, key=len, reverse=True):  # 長い単位から先に見る (Pa)
        if unit.endswith(base):
            prefix = unit[: -len(base)]
            if prefix in known_prefixes:
                return prefix, base

    msg = f"Invalid unit: {unit}"
    raise ValueError(msg)
