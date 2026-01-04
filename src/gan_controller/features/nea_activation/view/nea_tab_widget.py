from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from gan_controller.common.types.electricity import ElectricProperties
from gan_controller.common.types.quantity.quantity import Quantity
from gan_controller.features.nea_activation.domain.nea_config import NEAConfig
from gan_controller.features.nea_activation.dtos.nea_params import (
    NEAConditionParams,
    NEAControlParams,
    NEALogParams,
)
from gan_controller.features.nea_activation.dtos.nea_result import NEAActivationResult
from gan_controller.features.nea_activation.state import NEAActivationState

from .layouts import NEAActMainLayout


class NEAActivationTab(QWidget):
    """NEA 活性化タブの見た目制御"""

    # === 要素
    _main_layout: NEAActMainLayout

    # === シグナル
    experiment_start = Signal()
    experiment_stop = Signal()
    setting_apply = Signal()

    def __init__(self) -> None:
        super().__init__()

        # View
        self._main_layout = NEAActMainLayout()
        self.setLayout(self._main_layout)

        self._init_connect()

        self.set_running(NEAActivationState.IDLE)

    def _init_connect(self) -> None:
        self._main_layout.execution_panel.start_button.clicked.connect(self.experiment_start.emit)
        self._main_layout.execution_panel.stop_button.clicked.connect(self.experiment_stop.emit)
        self._main_layout.execution_panel.apply_button.clicked.connect(self.setting_apply.emit)

    def set_running(self, state: NEAActivationState) -> None:
        """実験表示 (ボタン) 切り替え"""
        if state == NEAActivationState.IDLE:
            self._main_layout.execution_panel.start_button.setEnabled(True)
            self._main_layout.execution_panel.stop_button.setEnabled(False)
            self._main_layout.measure_panel.set_status("待機中", False)
        elif state == NEAActivationState.RUNNING:
            self._main_layout.execution_panel.start_button.setEnabled(False)
            self._main_layout.execution_panel.stop_button.setEnabled(True)
            self._main_layout.measure_panel.set_status("実行中", True)
        elif state == NEAActivationState.STOPPING:
            self._main_layout.execution_panel.start_button.setEnabled(False)
            self._main_layout.execution_panel.stop_button.setEnabled(False)
            self._main_layout.measure_panel.set_status("停止処理中", False)

    # ==========================================================
    #  Data Binding Methods
    # ==========================================================

    def set_ui_from_config(self, config: NEAConfig) -> None:
        """Configの内容をUIに反映する"""
        cond_p = self._main_layout.condition_setting_panel
        log_p = self._main_layout.log_setting_panel  # noqa: F841
        exec_p = self._main_layout.execution_panel

        # Condition Panel
        cond_p.shunt_r_spin.setValue(config.condition.shunt_resistance)
        cond_p.laser_wavelength_spin.setValue(config.condition.laser_wavelength)
        cond_p.stabilization_time_spin.setValue(config.condition.stabilization_time)
        cond_p.integrated_count_spin.setValue(config.condition.integration_count)
        cond_p.integrated_interval_spin.setValue(config.condition.integration_interval)
        # 単位
        # cond_p.shunt_r_spin.setSuffix(f" {config.get_unit('shunt_resistance')}")
        # cond_p.laser_lambda_spin.setSuffix(f" {config.get_unit('laser_wavelength')}")

        # Execution Settings
        exec_p.amd_output_current_spin.setValue(config.execution.amd_output_current)
        exec_p.laser_sv_spin.setValue(config.execution.laser_power_sv)
        exec_p.laser_output_spin.setValue(config.execution.laser_power_output)
        # 単位
        # exec_p.amd_output_current_spin.set_suffix(f" {config.get_unit('amd_output_current')}")
        # exec_p.laser_sv_spin.setSuffix(f" {config.get_unit('laser_power_sv')}")
        # exec_p.laser_output_spin.setSuffix(f" {config.get_unit('laser_power_output')}")

    def get_config_from_ui(self) -> NEAConfig:
        """現在のUIから保存用Configを生成する"""
        cond_p = self._main_layout.condition_setting_panel
        exec_p = self._main_layout.execution_panel

        return NEAConfig(
            # Condition
            shunt_resistance=cond_p.shunt_r_spin.value(),
            laser_wavelength=cond_p.laser_wavelength_spin.value(),
            stabilization_time=cond_p.stabilization_time_spin.value(),
            integration_count=int(cond_p.integrated_interval_spin.value()),
            integration_time=cond_p.integrated_count_spin.value(),
            # Execution (初期値として保存)
            amd_output_current=exec_p.amd_output_current_spin.value(),
            laser_power_sv=exec_p.laser_sv_spin.value(),
            laser_power_output=exec_p.laser_output_spin.value(),
        )

    # ==========================================================
    #  Parameters Binding Methods
    # ==========================================================

    def get_condition_params(self) -> NEAConditionParams:
        """動的パラメータを取得"""
        cond_p = self._main_layout.condition_setting_panel

        return NEAConditionParams(
            shunt_resistance=Quantity(cond_p.shunt_r_spin.value(), "kΩ"),
            laser_wavelength=Quantity(cond_p.laser_wavelength_spin.value(), "nm"),
            stabilization_time=Quantity(cond_p.stabilization_time_spin.value(), "s"),
            integration_interval=Quantity(cond_p.integrated_interval_spin.value(), "s"),
            integration_count=Quantity(cond_p.integrated_count_spin.value(), ""),
        )

    def get_log_params(self) -> NEALogParams:
        """現在のUIからログ設定(DTO)を取得する"""
        log_p = self._main_layout.log_setting_panel

        return NEALogParams(
            update_date_folder=log_p.chk_date_update.isChecked(),
            update_major_version=log_p.chk_major_update.isChecked(),
            comment=log_p.comment_edit.text(),
        )

    def get_control_params(self) -> NEAControlParams:
        """現在のUIから実行制御パラメータ(DTO)を取得する"""
        exec_p = self._main_layout.execution_panel

        return NEAControlParams(
            amd_enable=exec_p.amd_output_current_spin.isChecked(),
            amd_output_current=Quantity(exec_p.amd_output_current_spin.value(), "A"),
            laser_power_sv=Quantity(exec_p.laser_sv_spin.value(), "mW"),
            laser_power_output=Quantity(exec_p.laser_output_spin.value(), "mW"),
        )

    # ==========================================================
    #  Update results to UI
    # ==========================================================

    def update_view(self, result: NEAActivationResult) -> None:
        """結果をUIに反映"""
        self._update_measure_values(result)
        self._main_layout.graph_panel.update_graph(result)

    def clear_view(self) -> None:
        """グラフや表示を初期化"""
        self._main_layout.graph_panel.clear_graph()

    def _update_measure_values(self, result: NEAActivationResult) -> None:
        """測定結果で表示を更新"""
        measure_p = self._main_layout.measure_panel

        measure_p.elapsed_time_label.set_value(Quantity(result.timestamp, "s"))

        measure_p.pc_value_label.set_value(result.photocurrent)
        measure_p.qe_value_label.set_value(result.quantum_efficiency)
        measure_p.ext_pres_val.set_value(result.ext_pressure)

        # AMD電源
        measure_p.amd_value_labels[ElectricProperties.VOLTAGE].set_value(result.electricity.voltage)
        measure_p.amd_value_labels[ElectricProperties.CURRENT].set_value(result.electricity.current)
        measure_p.amd_value_labels[ElectricProperties.POWER].set_value(result.electricity.power)
