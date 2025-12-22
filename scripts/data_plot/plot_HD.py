import re

from scripts.data_plot.base_plotter import BasePlotter
from scripts.data_plot.plot_util import AxisSide, PlotInfo, ScaleEnum


class HDPlotter(BasePlotter):
    def plot(self) -> None:
        self.plot_power()
        self.plot_pressure()

    def plot_power(self) -> None:
        df = self.log_df

        if "Volt(AMD)[V]" in df and "Current(AMD)[A]" in df:
            hc_power = df["Volt[V]"] * df["Current[A]"]
            amd_power = df["Volt(AMD)[V]"] * df["Current(AMD)[A]"]
            hc_current = re.sub(r"[\[\]]", "", self.conditions["Condition"]["HC_CURRENT"])
            amd_current = re.sub(r"[\[\]]", "", self.conditions["Condition"]["AMD_CURRENT"])

            temp = PlotInfo(df["Temp(TC)[deg.C]"], AxisSide.LEFT, "TC (℃)", "red")
            heater = PlotInfo(hc_power, AxisSide.RIGHT, f"Heater({hc_current})", "orange")
            amd = PlotInfo(amd_power, AxisSide.RIGHT, f"AMD({amd_current})", "gold")
            plot_info_list = [temp, heater, amd]
        else:
            hc_power = df["Volt[V]"] * df["Current[A]"]
            hc_current = re.sub(r"[\[\]]", "", self.conditions["Condition"]["HC_CURRENT"])

            temp = PlotInfo(df["Temp(TC)[deg.C]"], AxisSide.LEFT, "TC (℃)", "red")
            heater = PlotInfo(hc_power, AxisSide.RIGHT, f"Heater({hc_current})", "orange")
            plot_info_list = [temp, heater]

        self._plot_save(
            f"{self.logfile.path.stem}_power.svg",
            plot_info_list,
            "Time (h)",
            "Temperature (℃)",
            "Power (W)",
            ylim_left=(0, 800),
            ylim_right=(0, 15),
        )

    def plot_pressure(self) -> None:
        df = self.log_df

        temp = PlotInfo(df["Temp(TC)[deg.C]"], AxisSide.LEFT, "TC (℃)", "red")
        pressure_ext = PlotInfo(
            df["Pressure(EXT)[Pa]"], AxisSide.RIGHT, "Pressure(EXT)", "green", scale=ScaleEnum.LOG
        )
        pressure_sip = PlotInfo(
            df["Pressure(SIP)[Pa]"], AxisSide.RIGHT, "Pressure(SIP)", "purple", scale=ScaleEnum.LOG
        )

        plot_info_list = [temp, pressure_ext, pressure_sip]

        self._plot_save(
            f"{self.logfile.path.stem}_pressure.svg",
            plot_info_list,
            "Time (h)",
            "Temperature (℃)",
            "Pressure (Pa)",
            ylim_left=(0, 800),
            ylim_right=(1e-9, 1e-3),
        )
