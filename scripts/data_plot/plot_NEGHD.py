import re

from scripts.data_plot.base_plotter import BasePlotter

from .plot_util import AxisSide, PlotInfo, ScaleEnum


class NEGHDPlotter(BasePlotter):
    def plot(self) -> None:
        self.plot_power()

    def plot_power(self) -> None:
        df = self.log_df

        neg_power = df["Volt[V]"] * df["Current[A]"]
        neg_current = re.sub(r"[\[\]]", "", self.conditions["Condition"]["HC_CURRENT"])

        heater_plot_info = PlotInfo(
            neg_power, AxisSide.LEFT, f"NEG power({neg_current})", "chocolate"
        )
        pressure_ext_plot_info = PlotInfo(
            df["Pressure(EXT)[Pa]"], AxisSide.RIGHT, "Pressure(EXT)", "green", scale=ScaleEnum.LOG
        )
        plot_info_list = [heater_plot_info, pressure_ext_plot_info]

        self._plot_save(
            f"{self.logfile.path.stem}.svg",
            plot_info_list,
            "Time (h)",
            "Power (W)",
            "Pressure (Pa)",
            ylim_left=(0, 100),
            ylim_right=(1e-9, 1e-3),
        )
