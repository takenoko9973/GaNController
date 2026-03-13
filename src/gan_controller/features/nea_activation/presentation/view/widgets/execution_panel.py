from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gan_controller.core.domain.quantity import Current, Power
from gan_controller.features.nea_activation.domain.config import NEAControlConfig
from gan_controller.presentation.components.widgets import (
    CheckableSpinBox,
    SignificantFigureSpinBox,
)

_APPLY_DIRTY_STYLE = (
    "QPushButton { background-color: #fff3cd; }"
    "QPushButton:hover { background-color: #ffe8a1; }"
)


class NEAExecutionPanel(QGroupBox):
    """実行制御ウィジェット"""

    # === 要素
    amd_output_current_spin: CheckableSpinBox
    laser_sv_spin: QDoubleSpinBox
    laser_pv_spin: QDoubleSpinBox

    start_button: QPushButton
    stop_button: QPushButton
    apply_button: QPushButton

    # === シグナル
    start_requested = Signal()
    stop_requested = Signal()
    apply_requested = Signal()

    _baseline_config: NEAControlConfig
    _dirty_tracking_enabled: bool

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("実行制御", parent)

        layout = QVBoxLayout(self)
        layout.addWidget(self._create_control_section())
        layout.addLayout(self._create_execution_section())  # 制御

        self._connect_signals()
        self._dirty_tracking_enabled = True
        # 反映済みの設定を保持して、未適用の変更を検出する
        self._baseline_config = self.get_config()
        self._update_apply_state()

    def _create_control_section(self) -> QGroupBox:
        control_group = QGroupBox()
        control_layout = QVBoxLayout(control_group)

        # ====== 設定値入力
        value_set_layout = QHBoxLayout()

        # === AMD
        amd_control_layout = QVBoxLayout()
        amd_control_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.amd_output_current_spin = CheckableSpinBox(
            "AMD出力 :", checked=False, value=3.5, suffix=" A", maximum=10, single_step=0.1
        )
        amd_control_layout.addWidget(self.amd_output_current_spin)

        # === Laser
        laser_layout = QGridLayout()
        laser_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.laser_sv_spin = QDoubleSpinBox()
        self.laser_sv_spin.setValue(10)
        self.laser_sv_spin.setSuffix(" mW")
        self.laser_sv_spin.setRange(0, 120)
        self.laser_sv_spin.setDecimals(1)
        self.laser_sv_spin.setSingleStep(0.1)
        self.laser_pv_spin = SignificantFigureSpinBox(sig_figs=3)
        self.laser_pv_spin.setValue(3.01)
        self.laser_pv_spin.setSuffix(" mW")
        self.laser_pv_spin.setRange(1e-3, 120)
        laser_layout.addWidget(QLabel("レーザー出力 :"), 0, 0)
        laser_layout.addWidget(self.laser_sv_spin, 0, 1)
        laser_layout.addWidget(QLabel("レーザー実出力 :"), 1, 0)
        laser_layout.addWidget(self.laser_pv_spin, 1, 1)

        value_set_layout.addLayout(amd_control_layout, stretch=1)
        value_set_layout.addSpacing(10)
        value_set_layout.addLayout(laser_layout, stretch=1)

        # ====== 適応
        self.apply_button = QPushButton("Apply")

        control_layout.addLayout(value_set_layout)
        control_layout.addWidget(self.apply_button)

        return control_group

    def _create_execution_section(self) -> QLayout:
        execution_layout = QHBoxLayout()

        self.start_button = QPushButton("開始")
        self.stop_button = QPushButton("停止")

        self.start_button.setMinimumHeight(40)
        self.stop_button.setMinimumHeight(40)

        # 初期状態: 停止中なので「停止」ボタンは無効化
        self.stop_button.setEnabled(False)

        execution_layout.addWidget(self.start_button)
        execution_layout.addWidget(self.stop_button)

        return execution_layout

    def _connect_signals(self) -> None:
        self.start_button.clicked.connect(self.start_requested)
        self.stop_button.clicked.connect(self.stop_requested)
        self.apply_button.clicked.connect(self.apply_requested)

        self.amd_output_current_spin.check_box.stateChanged.connect(self._on_input_changed)
        self.amd_output_current_spin.spin_box.valueChanged.connect(self._on_input_changed)
        self.laser_sv_spin.valueChanged.connect(self._on_input_changed)
        self.laser_pv_spin.valueChanged.connect(self._on_input_changed)

    def _on_input_changed(self) -> None:
        # 停止中は変更検知を無効化
        if not self._dirty_tracking_enabled:
            return
        self._update_apply_state()

    def _is_dirty(self) -> bool:
        """現在の入力値と反映済み設定との差分を判定"""
        current = self.get_config()
        return not self._is_same_config(current, self._baseline_config)

    def _is_same_config(self, current: NEAControlConfig, baseline: NEAControlConfig) -> bool:
        # AMD無効時はAMD電流値の差分を無視する
        if current.amd_enable != baseline.amd_enable:
            return False
        if current.amd_enable and not current.amd_output_current.isclose(
            baseline.amd_output_current
        ):
            return False

        return current.laser_power_sv.isclose(
            baseline.laser_power_sv
        ) and current.laser_power_pv.isclose(baseline.laser_power_pv)

    def _update_apply_state(self) -> None:
        # 変更検知が無効なときは表示変化を出さない
        if not self._dirty_tracking_enabled:
            self.apply_button.setEnabled(False)
            self.apply_button.setStyleSheet("")
            return

        self._set_apply_dirty_state(self._is_dirty())

    def _set_apply_dirty_state(self, is_dirty: bool) -> None:
        if is_dirty:
            self.apply_button.setEnabled(True)
            self.apply_button.setStyleSheet(_APPLY_DIRTY_STYLE)
            self.apply_button.setToolTip("変更あり: Applyで反映")
        else:
            self.apply_button.setEnabled(False)
            self.apply_button.setStyleSheet("")
            self.apply_button.setToolTip("現在の値が反映済みです")

    def _block_input_signals(self, block: bool) -> None:
        self.amd_output_current_spin.check_box.blockSignals(block)
        self.amd_output_current_spin.spin_box.blockSignals(block)
        self.laser_sv_spin.blockSignals(block)
        self.laser_pv_spin.blockSignals(block)

    def mark_applied(self) -> None:
        # 現在値を反映済みとして基準値を更新する
        self._baseline_config = self.get_config()
        self._update_apply_state()

    def set_dirty_tracking(self, enabled: bool) -> None:
        # 実験状態に応じて変更検知の有効/無効を切り替える
        self._dirty_tracking_enabled = enabled
        if not enabled:
            self.apply_button.setEnabled(False)
            self.apply_button.setStyleSheet("")
        self._update_apply_state()

    # =============================================================================

    def get_config(self) -> NEAControlConfig:
        return NEAControlConfig(
            amd_enable=self.amd_output_current_spin.isChecked(),
            amd_output_current=Current(self.amd_output_current_spin.value()),
            laser_power_sv=Power(self.laser_sv_spin.value(), "m"),
            laser_power_pv=Power(self.laser_pv_spin.value(), "m"),
        )

    def set_config(self, config: NEAControlConfig) -> None:
        self._block_input_signals(True)
        self.amd_output_current_spin.setChecked(config.amd_enable)
        self.amd_output_current_spin.setValue(config.amd_output_current.base_value)
        self.laser_sv_spin.setValue(config.laser_power_sv.value_as("m"))
        self.laser_pv_spin.setValue(config.laser_power_pv.value_as("m"))
        self._block_input_signals(False)
        self.mark_applied()
