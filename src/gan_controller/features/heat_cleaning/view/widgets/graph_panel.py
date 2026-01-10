from PySide6.QtWidgets import QVBoxLayout, QWidget

from gan_controller.common.ui.widgets import AxisScale, DualAxisGraph
from gan_controller.features.heat_cleaning.schemas.result import HCRunnerResult


class HCGraphPanel(QWidget):
    """実行制御およびモニタリング表示用ウィジェット"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.graph_power = DualAxisGraph(
            "Power",
            "Time (h)",
            "Temperature (°C)",
            "Power (W)",
        )
        self.graph_power.setMinimumWidth(500)
        self.graph_power.setMinimumHeight(300)

        self.graph_pressure = DualAxisGraph(
            "Pressure",
            "Time (h)",
            "Temperature (°C)",
            "Pressure (Pa)",
            right_scale=AxisScale.LOG,
        )
        self.graph_pressure.setMinimumWidth(500)
        self.graph_pressure.setMinimumHeight(300)

        layout.addWidget(self.graph_power)
        layout.addSpacing(10)
        layout.addWidget(self.graph_pressure)

        self._setup_lines()

    def _setup_lines(self) -> None:
        """グラフにプロットする線を定義"""
        # Power Graph
        self.graph_power.add_line("temp", "Temp(TC)[℃]", "red", is_right_axis=False)
        self.graph_power.add_line("heater_power", "Heater[W]", "orange", is_right_axis=True)
        self.graph_power.add_line("amd_power", "AMD[W]", "gold", is_right_axis=True)

        # Pressure Graph
        self.graph_pressure.add_line("temp", "Temp(TC)[℃]", "red", is_right_axis=False)
        self.graph_pressure.add_line("ext_pres", "Pressure(EXT)[Pa]", "green", is_right_axis=True)
        self.graph_pressure.add_line("sip_pres", "Pressure(SIP)[Pa]", "purple", is_right_axis=True)

    def update_graph(self, result: HCRunnerResult) -> None:
        t = result.total_timestamp

        # --- Photocurrent Graph の更新 ---
        # Resultオブジェクトから値を取り出し、辞書形式でグラフに渡す
        self.graph_power.update_point(
            x_val=t.value_as("hour"),
            values={
                "temp": result.case_temperature.base_value,
                "heater_power": result.hc_electricity.power.base_value,
                "amd_power": result.amd_electricity.power.base_value,
            },
        )

        # --- QE Graph の更新 ---
        self.graph_pressure.update_point(
            x_val=t.value_as("hour"),
            values={
                "temp": result.case_temperature.base_value,
                "ext_pres": result.ext_pressure.base_value,
                "sip_pres": result.sip_pressure.base_value,
            },
        )

    def clear_graph(self) -> None:
        """グラフデータをクリアして再初期化"""
        self.graph_power.clear_data()
        self.graph_pressure.clear_data()

        self._setup_lines()  # ライン再設定
