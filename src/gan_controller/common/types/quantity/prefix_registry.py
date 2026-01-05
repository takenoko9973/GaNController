from dataclasses import dataclass


@dataclass(frozen=True)
class PrefixSpec:
    scale: float
    allowed_units: frozenset[str]


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
        # 特別枠 prefix (無次元のみ)
        "%": PrefixSpec(1e-2, frozenset({""})),
        "ppm": PrefixSpec(1e-6, frozenset({""})),
    }
)
