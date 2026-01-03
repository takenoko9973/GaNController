from dataclasses import dataclass


@dataclass(frozen=True)
class PrefixSpec:
    scale: float
    allowed_units: frozenset[str]
