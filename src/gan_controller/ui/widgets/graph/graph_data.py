# graph_data.py
from dataclasses import dataclass, field


@dataclass
class GraphData:
    x: list[float] = field(default_factory=list)
    left: dict[str, list[float]] = field(default_factory=dict)
    right: dict[str, list[float]] = field(default_factory=dict)

    def clear(self) -> None:
        self.x.clear()
        self.left.clear()
        self.right.clear()

    def append_point(self, x_val: float, values: dict[str, float]) -> None:
        self.x.append(x_val)
        for name, val in values.items():
            if name in self.left:
                self.left[name].append(val)
            elif name in self.right:
                self.right[name].append(val)
