import re
from typing import Any

import pandas as pd

from scripts.data_plot.base_plotter import BasePlotter
from scripts.data_plot.plot_util import AxisSide, PlotInfo, ScaleEnum


class HDPlotter(BasePlotter):
    Y_LIM_TEMP = (0, 800)
    Y_LIM_POWER = (0, 20)
    Y_LIM_PRESSURE = (1e-9, 1e-3)

    COLOR_TEMP = "red"
    COLOR_HEATER = "orange"
    COLOR_AMD = "gold"
    COLOR_PRESS_EXT = "green"
    COLOR_PRESS_SIP = "purple"

    def plot(self) -> None:
        if not self.extract_data():
            print(f"[SKIP] {self.logfile.path.name}: データが無効なためプロットをスキップします。")
            return

        # 電力グラフの処理
        power_data = self._transform_power_data()
        self._visualize_power(power_data)

        # 圧力グラフの処理
        pressure_data = self._transform_pressure_data()
        self._visualize_pressure(pressure_data)

    # ==========================================
    # Transform (加工層) : 描画機能を持たせず、純粋にデータを計算・抽出する
    # ==========================================
    def _transform_power_data(self) -> dict[str, Any]:
        """電力計算のロジック"""
        df = self.log_df

        # 条件のパース
        hc_current_str = self.conditions.get("Condition", {}).get("HC_CURRENT", "")
        amd_current_str = self.conditions.get("Condition", {}).get("AMD_CURRENT", "")
        hc_current = re.sub(r"[\[\]]", "", hc_current_str)
        amd_current = re.sub(r"[\[\]]", "", amd_current_str)

        data = {
            "temp": df["Temp(TC)[deg.C]"],
            "hc_power": df["Volt[V]"] * df["Current[A]"],
            "hc_current_label": hc_current,
            "has_amd": False,
        }

        # AMDデータが存在する場合
        if "Volt(AMD)[V]" in df and "Current(AMD)[A]" in df:
            data["has_amd"] = True
            data["amd_power"] = df["Volt(AMD)[V]"] * df["Current(AMD)[A]"]
            data["amd_current_label"] = amd_current

        return data

    def _transform_pressure_data(self) -> dict[str, pd.Series]:
        """圧力データの抽出ロジック"""
        return {
            "temp": self.log_df["Temp(TC)[deg.C]"],
            "pressure_ext": self.log_df["Pressure(EXT)[Pa]"],
            "pressure_sip": self.log_df["Pressure(SIP)[Pa]"],
        }

    # ==========================================
    # Visualize (描画層) : 計算済みのデータを受け取り、プロットのみを行う
    # ==========================================
    def _visualize_power(self, data: dict[str, Any]) -> None:
        plot_info_list = [
            PlotInfo(data["temp"], AxisSide.LEFT, "TC (℃)", self.COLOR_TEMP),
            PlotInfo(
                data["hc_power"],
                AxisSide.RIGHT,
                f"Heater({data['hc_current_label']})",
                self.COLOR_HEATER,
            ),
        ]

        if data["has_amd"]:
            plot_info_list.append(
                PlotInfo(
                    data["amd_power"],
                    AxisSide.RIGHT,
                    f"AMD({data['amd_current_label']})",
                    self.COLOR_AMD,
                )
            )

        self._plot_save(
            filename=f"{self.logfile.path.stem}_power.svg",
            plot_info_list=plot_info_list,
            xlabel="Time (h)",
            ylabel_left="Temperature (℃)",
            ylabel_right="Power (W)",
            ylim_left=self.Y_LIM_TEMP,
            ylim_right=self.Y_LIM_POWER,
        )

    def _visualize_pressure(self, data: dict[str, pd.Series]) -> None:
        plot_info_list = [
            PlotInfo(data["temp"], AxisSide.LEFT, "TC (℃)", self.COLOR_TEMP),
            PlotInfo(
                data["pressure_ext"],
                AxisSide.RIGHT,
                "Pressure(EXT)",
                self.COLOR_PRESS_EXT,
                scale=ScaleEnum.LOG,
            ),
            PlotInfo(
                data["pressure_sip"],
                AxisSide.RIGHT,
                "Pressure(SIP)",
                self.COLOR_PRESS_SIP,
                scale=ScaleEnum.LOG,
            ),
        ]

        self._plot_save(
            filename=f"{self.logfile.path.stem}_pressure.svg",
            plot_info_list=plot_info_list,
            xlabel="Time (h)",
            ylabel_left="Temperature (℃)",
            ylabel_right="Pressure (Pa)",
            ylim_left=self.Y_LIM_TEMP,
            ylim_right=self.Y_LIM_PRESSURE,
        )
