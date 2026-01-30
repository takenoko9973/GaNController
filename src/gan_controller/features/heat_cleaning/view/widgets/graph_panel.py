from PySide6.QtWidgets import QVBoxLayout, QWidget

from gan_controller.common.ui.widgets import AxisScale, DualAxisGraph
from gan_controller.common.ui.widgets.graph import GraphData
from gan_controller.features.heat_cleaning.schemas.result import HCRunnerResult


class HCGraphPanel(QWidget):
    """実行制御およびモニタリング表示用ウィジェット"""

    # グラフ描画時の最大点数 (これを超えると間引かれる)
    MAX_PLOT_POINTS = 2000

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # 履歴データ (全データ) をここに保持
        self._history_power = GraphData()
        self._history_pressure = GraphData()

        layout = QVBoxLayout(self)

        self.graph_power = DualAxisGraph(
            "Power",
            "Time (h)",
            "Temperature (°C)",
            "Power (W)",
        )
        self.graph_power.setMinimumSize(500, 300)

        self.graph_pressure = DualAxisGraph(
            "Pressure",
            "Time (h)",
            "Temperature (°C)",
            "Pressure (Pa)",
            right_scale=AxisScale.LOG,
        )
        self.graph_power.setMinimumSize(500, 300)

        layout.addWidget(self.graph_power)
        layout.addSpacing(10)
        layout.addWidget(self.graph_pressure)

        self._init_lines()

    def _init_lines(self) -> None:
        """グラフにプロットする線を定義"""
        # Power Graph
        self.graph_power.add_line("temp", "Temp(TC)[℃]", "red", is_right_axis=False)
        self.graph_power.add_line("heater_power", "Heater[W]", "orange", is_right_axis=True)
        self.graph_power.add_line("amd_power", "AMD[W]", "gold", is_right_axis=True)

        # Pressure Graph
        self.graph_pressure.add_line("temp", "Temp(TC)[℃]", "red", is_right_axis=False)
        self.graph_pressure.add_line("ext_pres", "Pressure(EXT)[Pa]", "green", is_right_axis=True)
        self.graph_pressure.add_line("sip_pres", "Pressure(SIP)[Pa]", "purple", is_right_axis=True)

    def clear_graph(self) -> None:
        """グラフデータをクリアして再初期化"""
        self.graph_power.clear_view()
        self.graph_pressure.clear_view()

        self._init_lines()  # ライン再設定

    def append_data(self, result: HCRunnerResult) -> None:
        t = result.total_timestamp

        # データ追加
        self._history_power.append_point(
            x_val=t.value_as("hour"),
            values={
                "temp": result.case_temperature.base_value,
                "heater_power": result.hc_electricity.power.base_value,
                "amd_power": result.amd_electricity.power.base_value,
            },
        )
        self._history_pressure.append_point(
            x_val=t.value_as("hour"),
            values={
                "temp": result.case_temperature.base_value,
                "ext_pres": result.ext_pressure.base_value,
                "sip_pres": result.sip_pressure.base_value,
            },
        )

        # データが多い場合の間引き処理
        disp_power = self._history_power.decimate(self.MAX_PLOT_POINTS)
        disp_pressure = self._history_pressure.decimate(self.MAX_PLOT_POINTS)

        # グラフ更新
        self.graph_power.set_data(disp_power)
        self.graph_pressure.set_data(disp_pressure)
