import math

import pandas as pd


class GraphData:
    _data: pd.DataFrame

    def __init__(self) -> None:
        self._data = pd.DataFrame()

    def append_point(self, x_value: float, y_values: dict[str, float]) -> None:
        new_row = {"x": x_value}
        new_row.update(y_values)
        new_df = pd.DataFrame([new_row])

        if self._data.empty:
            self._data = new_df
        else:
            self._data = pd.concat([self._data, new_df], ignore_index=True)

    def get_data(self) -> pd.DataFrame:
        """生の全データを取得"""
        return self._data

    def get_downsampled_data(self, max_points: int) -> "GraphData":
        """指定された点数以下になるようにデータを間引いて取得する。

        :param max_points: 最大データ点数
        :return: 間引かれたGraphData (コピー)
        """
        new_instance = GraphData()
        decimated_data = self._decimate(max_points)

        new_instance._data = decimated_data
        return new_instance

    def _decimate(self, max_points: int) -> pd.DataFrame:
        """データ点が max_points 以下になるように間引いたGraphDataを新たに返す"""
        total_len = len(self._data)

        if total_len <= max_points:
            return self._data.copy()

        # 間引きステップ数の計算
        step = math.ceil(total_len / max_points)
        return self._data.iloc[::step].copy()
