from dataclasses import dataclass


@dataclass(frozen=True)
class PrefixSpec:
    scale: float
    allowed_units: frozenset[str]
    unit_hidden: bool = False


class PrefixRegistry:
    def __init__(self, specs: dict[str, PrefixSpec]) -> None:
        self._specs = specs

    def get(self, prefix: str) -> PrefixSpec:
        return self._specs[prefix]

    def validate(self, prefix: str, unit: str) -> None:
        spec = self.get(prefix)
        if spec.allowed_units and unit not in spec.allowed_units:
            msg = f"Prefix '{prefix}' cannot be used with unit '{unit}'"
            raise ValueError(msg)

    @property
    def known_prefixes(self) -> set[str]:
        return set(self._specs.keys())


PREFIX_REGISTRY = PrefixRegistry(
    {
        # 通常 SI prefix (制限なし)
        "p": PrefixSpec(1e-12, frozenset()),
        "n": PrefixSpec(1e-9, frozenset()),
        "µ": PrefixSpec(1e-6, frozenset()),
        "u": PrefixSpec(1e-6, frozenset()),  # "u" でも "μ" と同じように
        "m": PrefixSpec(1e-3, frozenset()),
        "": PrefixSpec(1.0, frozenset()),
        "k": PrefixSpec(1e3, frozenset()),
        "M": PrefixSpec(1e6, frozenset()),
        "G": PrefixSpec(1e9, frozenset()),
        # 時間用 Prefix (単位 s を隠す)
        "min": PrefixSpec(60.0, frozenset({"s"}), unit_hidden=True),
        "hour": PrefixSpec(3600.0, frozenset({"s"}), unit_hidden=True),
        # 特別な prefix
        "%": PrefixSpec(1e-2, frozenset({""})),
        "ppm": PrefixSpec(1e-6, frozenset({""})),
    }
)
