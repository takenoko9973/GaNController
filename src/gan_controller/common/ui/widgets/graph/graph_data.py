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

    def decimate(self, max_points: int) -> "GraphData":
        """データ点が max_points 以下になるように間引いたGraphDataを新たに返す"""
        count = len(self.x)

        if count <= max_points:  # もともと max_points 以下
            # そのままコピーして返す
            return self.__class__(
                x=self.x[:],
                left={k: v[:] for k, v in self.left.items()},
                right={k: v[:] for k, v in self.right.items()},
            )

        # 間引きステップ数の計算
        step = max(1, count // max_points)
        return self.__class__(
            x=self.x[::step],
            left={k: v[::step] for k, v in self.left.items()},
            right={k: v[::step] for k, v in self.right.items()},
        )
