from PySide6.QtWidgets import QVBoxLayout, QWidget

from gan_controller.common.ui.widgets import DualAxisGraph, GraphData
from gan_controller.features.heat_cleaning.domain.models import HCExperimentResult


class HCGraphPanel(QWidget):
    """実行制御およびモニタリング表示用ウィジェット"""

    _history_power: GraphData
    _history_pressure: GraphData

    graph_power: DualAxisGraph
    graph_pressure: DualAxisGraph

    # グラフ描画時の最大点数 (これを超えると間引かれる)
    MAX_PLOT_POINTS = 2000

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # 履歴データ (全データ) をここに保持
        self._history_power = GraphData()
        self._history_pressure = GraphData()

        layout = QVBoxLayout(self)

        self.graph_power = DualAxisGraph()
        self.graph_power.setMinimumSize(500, 300)
        self.graph_power.set_title("Power")
        self.graph_power.set_axis_labels(
            x_label="Time (h)", left_label="Temperature (°C)", right_label="Power (W)"
        )

        self.graph_pressure = DualAxisGraph()
        self.graph_pressure.setMinimumSize(500, 300)
        self.graph_pressure.set_title("Pressure")
        self.graph_pressure.set_axis_labels(
            x_label="Time (h)", left_label="Temperature (°C)", right_label="Pressure (Pa)"
        )
        self.graph_pressure.set_axis_scale("right", "log")

        layout.addWidget(self.graph_power)
        layout.addSpacing(10)
        layout.addWidget(self.graph_pressure)

        self._init_lines()

    def _init_lines(self) -> None:
        """グラフにプロットする線を定義"""
        # Power Graph
        self.graph_power.add_series("temp", "left", "red", legend_label="Temp(TC)[℃]")
        self.graph_power.add_series("heater_power", "right", "orange", legend_label="Heater[W]")
        self.graph_power.add_series("amd_power", "right", "gold", legend_label="AMD[W]")

        # Pressure Graph
        self.graph_pressure.add_series("temp", "left", "red", legend_label="Temp(TC)[℃]")
        self.graph_pressure.add_series(
            "ext_pres", "right", "green", legend_label="Pressure(EXT)[Pa]"
        )
        self.graph_pressure.add_series(
            "sip_pres", "right", "purple", legend_label="Pressure(SIP)[Pa]"
        )

    def clear_graph(self) -> None:
        """グラフデータをクリアして再初期化"""
        self._history_power = GraphData()
        self._history_pressure = GraphData()

        self.graph_power.clear_view()
        self.graph_pressure.clear_view()

        self._init_lines()  # ライン再設定

    def append_data(self, result: HCExperimentResult) -> None:
        t = result.total_timestamp

        # データ追加
        self._history_power.append_point(
            x_value=t.value_as("hour"),
            y_values={
                "temp": result.case_temperature.base_value,
                "heater_power": result.electricity_hc.power.base_value,
                "amd_power": result.electricity_amd.power.base_value,
            },
        )
        self._history_pressure.append_point(
            x_value=t.value_as("hour"),
            y_values={
                "temp": result.case_temperature.base_value,
                "ext_pres": result.ext_pressure.base_value,
                "sip_pres": result.sip_pressure.base_value,
            },
        )

        # データが多い場合の間引き処理
        disp_power = self._history_power.get_downsampled_data(self.MAX_PLOT_POINTS)
        disp_pressure = self._history_pressure.get_downsampled_data(self.MAX_PLOT_POINTS)

        # グラフ更新
        self.graph_power.update_plot(disp_power)
        self.graph_pressure.update_plot(disp_pressure)
