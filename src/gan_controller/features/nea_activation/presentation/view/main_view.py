from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QWidget

from gan_controller.core.domain.electricity import ElectricProperties
from gan_controller.features.nea_activation.domain.config import NEAConfig
from gan_controller.features.nea_activation.domain.models import NEAActivationState, NEARunnerResult

from .widgets import (
    NEAConditionSettingsPanel,
    NEAExecutionPanel,
    NEAGraphPanel,
    NEALogSettingPanel,
    NEAMeasurePanel,
)


class NEAActivationMainView(QWidget):
    # === 要素
    _main_layout: QHBoxLayout

    # 左側 (入力欄、装置表示)
    condition_setting_panel: NEAConditionSettingsPanel
    log_setting_panel: NEALogSettingPanel
    measure_panel: NEAMeasurePanel
    execution_panel: NEAExecutionPanel
    # 右側 (グラフ)
    graph_panel: NEAGraphPanel

    def __init__(self) -> None:
        super().__init__()

        self._init_ui()

        self.set_running(NEAActivationState.IDLE)

    def _init_ui(self) -> None:
        self._main_layout = QHBoxLayout(self)
        self.setLayout(self._main_layout)

        self._main_layout.addWidget(self._left_panel())
        self._main_layout.addWidget(self._right_panel())

    def _left_panel(self) -> QFrame:
        """左側 (設定値、制御) レイアウト"""
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.Shape.StyledPanel)
        left_panel.setFixedWidth(400)

        left_layout = QVBoxLayout(left_panel)

        self.condition_setting_panel = NEAConditionSettingsPanel()
        self.log_setting_panel = NEALogSettingPanel()
        self.execution_panel = NEAExecutionPanel()
        self.measure_panel = NEAMeasurePanel()

        left_layout.addWidget(self.condition_setting_panel)
        left_layout.addSpacing(10)
        left_layout.addWidget(self.log_setting_panel)
        left_layout.addSpacing(10)
        left_layout.addWidget(self.execution_panel)
        left_layout.addSpacing(10)
        left_layout.addWidget(self.measure_panel)
        left_layout.addStretch()

        return left_panel

    def _right_panel(self) -> QFrame:
        """右側 (グラフ) レイアウト"""
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        right_panel.setMinimumWidth(540)

        right_layout = QVBoxLayout(right_panel)

        self.graph_panel = NEAGraphPanel()

        right_layout.addWidget(self.graph_panel)

        return right_panel

    # =============================================================================

    def set_running(self, state: NEAActivationState) -> None:
        """実験表示 (ボタン) 切り替え"""
        if state == NEAActivationState.IDLE:
            # 設定パネルの有効化
            self.condition_setting_panel.setEnabled(True)
            self.log_setting_panel.setEnabled(True)

            self.execution_panel.start_button.setEnabled(True)  # 実行ボタン
            self.execution_panel.stop_button.setEnabled(False)  # 停止ボタン
            self.measure_panel.set_status("待機中", False)
        elif state == NEAActivationState.RUNNING:
            # 設定パネルの無効化
            self.condition_setting_panel.setEnabled(False)
            self.log_setting_panel.setEnabled(False)

            self.execution_panel.start_button.setEnabled(False)
            self.execution_panel.stop_button.setEnabled(True)
            self.measure_panel.set_status("実行中", True)
        elif state == NEAActivationState.STOPPING:
            # 停止中もパネル操作不可
            self.condition_setting_panel.setEnabled(False)
            self.log_setting_panel.setEnabled(False)

            # 停止中はどちらも操作不可
            self.execution_panel.start_button.setEnabled(False)
            self.execution_panel.stop_button.setEnabled(False)
            self.measure_panel.set_status("停止処理中", False)

    def update_view(self, result: NEARunnerResult) -> None:
        """結果をUIに反映"""
        self._update_measure_values(result)
        self.graph_panel.append_data(result)

    def clear_view(self) -> None:
        """グラフや表示を初期化"""
        self.graph_panel.clear_graph()

    def _update_measure_values(self, result: NEARunnerResult) -> None:
        """測定結果で表示を更新"""
        measure_p = self.measure_panel

        measure_p.elapsed_time_label.setValue(result.timestamp)

        measure_p.pc_value_label.setValue(result.photocurrent)
        measure_p.qe_value_label.setValue(result.quantum_efficiency)
        measure_p.ext_pres_val.setValue(result.ext_pressure)

        # AMD電源
        measure_p.amd_value_labels[ElectricProperties.VOLTAGE].setValue(
            result.amd_electricity.voltage
        )
        measure_p.amd_value_labels[ElectricProperties.CURRENT].setValue(
            result.amd_electricity.current
        )
        measure_p.amd_value_labels[ElectricProperties.POWER].setValue(result.amd_electricity.power)

    # =============================================================================

    def get_full_config(self) -> NEAConfig:
        return NEAConfig(
            condition=self.condition_setting_panel.get_config(),
            log=self.log_setting_panel.get_config(),
            control=self.execution_panel.get_config(),
        )

    def set_full_config(self, config: NEAConfig) -> None:
        self.condition_setting_panel.set_config(config.condition)
        self.log_setting_panel.set_config(config.log)
        self.execution_panel.set_config(config.control)
