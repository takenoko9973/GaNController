import re
from typing import Any

from scripts.data_plot.base_plotter import BasePlotter
from scripts.data_plot.plot_util import AxisSide, PlotInfo, ScaleEnum


class NEGHDPlotter(BasePlotter):
    Y_LIM_POWER = (0, 100)
    Y_LIM_PRESSURE = (1e-9, 1e-3)

    COLOR_NEG = "chocolate"
    COLOR_PRESS_EXT = "green"

    def plot(self) -> None:
        if not self.extract_data():
            print(f"[SKIP] {self.logfile.path.name}: データが無効なためプロットをスキップします。")
            return

        # グラフの処理
        power_data = self._transform_data()
        self._visualize(power_data)

    # ==========================================
    # Transform (加工層) : 描画機能を持たせず、純粋にデータを計算・抽出する
    # ==========================================
    def _transform_data(self) -> dict[str, Any]:
        """電力計算のロジック"""
        df = self.log_df

        # 条件のパース
        neg_current_str = self.conditions.get("Condition", {}).get("HC_CURRENT", "")
        neg_current = re.sub(r"[\[\]]", "", neg_current_str)

        return {
            "neg_power": df["Volt[V]"] * df["Current[A]"],
            "pressure_ext": df["Pressure(EXT)[Pa]"],
            "neg_current_label": neg_current,
        }

    # ==========================================
    # Visualize (描画層) : 計算済みのデータを受け取り、プロットのみを行う
    # ==========================================
    def _visualize(self, data: dict[str, Any]) -> None:
        plot_info_list = [
            PlotInfo(
                data=data["neg_power"],
                axis=AxisSide.LEFT,
                label=f"NEG power({data['neg_current_label']})",
                color=self.COLOR_NEG,
            ),
            PlotInfo(
                data=data["pressure_ext"],
                axis=AxisSide.RIGHT,
                label="Pressure(EXT)",
                color=self.COLOR_PRESS_EXT,
                scale=ScaleEnum.LOG,
            ),
        ]

        self._plot_save(
            filename=f"{self.logfile.path.stem}.svg",
            plot_info_list=plot_info_list,
            xlabel="Time (h)",
            ylabel_left="Power (W)",
            ylabel_right="Pressure (Pa)",
            ylim_left=self.Y_LIM_POWER,
            ylim_right=self.Y_LIM_PRESSURE,
        )
