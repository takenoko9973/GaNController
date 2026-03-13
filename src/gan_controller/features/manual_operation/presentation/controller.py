from contextlib import suppress

import pyvisa
from PySide6.QtCore import Slot

from gan_controller.core.domain.app_config import AppConfig
from gan_controller.core.domain.quantity import Power
from gan_controller.features.manual_operation.application.workflow import GM10MonitorWorkflow
from gan_controller.features.manual_operation.domain.models import ManualResult
from gan_controller.features.manual_operation.presentation.view import ManualOperationMainView
from gan_controller.infrastructure.hardware.adapters.laser_adapter import (
    IBeamAdapter,
    MockLaserAdapter,
)
from gan_controller.infrastructure.hardware.adapters.pyrometer_adapter import (
    MockPyrometerAdapter,
    PWUXAdapter,
)
from gan_controller.infrastructure.hardware.drivers import PWUX, IBeam
from gan_controller.presentation.async_runners.manager import AsyncExperimentManager
from gan_controller.presentation.components.tab_controller import ITabController


class ManualOperationController(ITabController):
    _view: ManualOperationMainView
    _gm10_runner: AsyncExperimentManager
    _pwux_adapter: PWUXAdapter | MockPyrometerAdapter | None
    _pwux_rm: pyvisa.ResourceManager | None
    _laser_adapter: IBeamAdapter | MockLaserAdapter | None
    _laser_rm: pyvisa.ResourceManager | None

    def __init__(self, view: ManualOperationMainView) -> None:
        super().__init__()
        self._view = view
        self._gm10_runner = AsyncExperimentManager()
        self._pwux_adapter = None
        self._pwux_rm = None
        self._laser_adapter = None
        self._laser_rm = None

        self._connect_view_signals()
        self._connect_manager_signals()

        self._load_channel_config()
        self._view.set_gm10_connected(False)
        self._view.set_pwux_connected(False)
        self._view.set_laser_connected(False)

    def _connect_view_signals(self) -> None:
        self._view.gm10_connect_requested.connect(self.connect_gm10)
        self._view.gm10_disconnect_requested.connect(self.disconnect_gm10)
        self._view.pwux_connect_requested.connect(self.connect_pwux)
        self._view.pwux_disconnect_requested.connect(self.disconnect_pwux)
        self._view.laser_connect_requested.connect(self.connect_laser)
        self._view.laser_disconnect_requested.connect(self.disconnect_laser)
        self._view.pwux_read_requested.connect(self.request_pwux_temperature)
        self._view.pwux_pointer_toggled.connect(self.set_pwux_pointer)
        self._view.laser_set_requested.connect(self.set_laser_power)
        self._view.laser_emission_toggled.connect(self.set_laser_emission)

    def _connect_manager_signals(self) -> None:
        self._gm10_runner.step_result_observed.connect(self.on_gm10_result)
        self._gm10_runner.error_occurred.connect(self.on_gm10_error)
        self._gm10_runner.finished.connect(self.on_gm10_finished)

    def _load_channel_config(self) -> None:
        # 起動時にGM10のチャンネル表示だけ先にセットしておく
        with suppress(OSError, ValueError):
            app_config = AppConfig.load()

        self._view.set_gm10_channel_config(app_config.devices.gm10)

    # =================================================
    # View -> GM10 Workflow
    # =================================================

    @Slot()
    def connect_gm10(self) -> None:
        # GM10のみを監視スレッドで接続・監視開始
        if self._gm10_runner.is_running():
            return

        app_config = AppConfig.load()
        self._view.set_gm10_channel_config(app_config.devices.gm10)

        try:
            workflow = GM10MonitorWorkflow(app_config, poll_interval=1.0)
            self._gm10_runner.start_workflow(workflow)
            self._view.set_gm10_connected(True)

        except Exception as e:  # noqa: BLE001
            self._show_error(f"GM10 接続エラー: {e}")
            self._view.set_gm10_connected(False)

    @Slot()
    def disconnect_gm10(self) -> None:
        # GM10の監視スレッドを停止
        if not self._gm10_runner.is_running():
            return

        self._gm10_runner.stop_workflow()

    # =================================================
    # View -> PWUX
    # =================================================

    @Slot()
    def connect_pwux(self) -> None:
        # PWUXは必要なときに個別接続
        if self._pwux_adapter is not None:
            return

        app_config = AppConfig.load()
        if not app_config.common.is_simulation_mode and app_config.devices.pwux.com_port <= 0:
            self._show_error("PWUX com_port が無効です。")
            return

        try:
            if app_config.common.is_simulation_mode:
                self._pwux_adapter = MockPyrometerAdapter()
            else:
                self._pwux_rm = pyvisa.ResourceManager()
                driver = PWUX(self._pwux_rm, f"COM{app_config.devices.pwux.com_port}")
                self._pwux_adapter = PWUXAdapter(driver)

            self._view.set_pwux_connected(True)

        except Exception as e:  # noqa: BLE001
            self._show_error(f"PWUX 接続エラー: {e}")
            self._cleanup_pwux()

    @Slot()
    def disconnect_pwux(self) -> None:
        # 切断前に照準を必ずOFF
        if self._pwux_adapter is None:
            return

        try:
            self._pwux_adapter.set_pointer(False)
        except Exception as e:  # noqa: BLE001
            print(f"Failed to disable PWUX pointer: {e}")

        self._cleanup_pwux()
        self._view.set_pwux_pointer_checked(False)
        self._view.set_pwux_connected(False)

    @Slot()
    def request_pwux_temperature(self) -> None:
        # 手動で温度取得
        if self._pwux_adapter is None:
            return
        try:
            temp = self._pwux_adapter.read_temperature()
            self._view.set_pwux_temperature(temp)
        except Exception as e:  # noqa: BLE001
            self._show_error(f"PWUX 温度取得エラー: {e}")

    @Slot(bool)
    def set_pwux_pointer(self, enable: bool) -> None:
        # 照準表示のON/OFF
        if self._pwux_adapter is None:
            return
        try:
            self._pwux_adapter.set_pointer(enable)
        except Exception as e:  # noqa: BLE001
            self._show_error(f"PWUX 照準表示切替エラー: {e}")

    # =================================================
    # View -> Laser
    # =================================================

    @Slot()
    def connect_laser(self) -> None:
        # Laserを個別接続し、CH有効化 + Emission OFFで初期化
        if self._laser_adapter is not None:
            return

        app_config = AppConfig.load()
        if not app_config.common.is_simulation_mode and app_config.devices.ibeam.com_port <= 0:
            self._show_error("iBeam com_port が無効です。")
            return

        try:
            if app_config.common.is_simulation_mode:
                self._laser_adapter = MockLaserAdapter()
            else:
                self._laser_rm = pyvisa.ResourceManager()
                driver = IBeam(self._laser_rm, f"COM{app_config.devices.ibeam.com_port}")
                self._laser_adapter = IBeamAdapter(driver)

            self._laser_adapter.set_channel_enable(app_config.devices.ibeam.beam_ch, True)
            self._laser_adapter.set_emission(False)
            self._update_laser_current_power(app_config)

            self._view.set_laser_connected(True)

        except Exception as e:  # noqa: BLE001
            self._show_error(f"レーザー 接続エラー: {e}")
            self._cleanup_laser()

    @Slot()
    def disconnect_laser(self) -> None:
        # Emission OFF + CH無効化を行ってから切断
        if self._laser_adapter is None:
            return

        try:
            self._laser_adapter.set_emission(False)
        except Exception as e:  # noqa: BLE001
            print(f"Failed to stop laser emission: {e}")

        try:
            app_config = AppConfig.load()
            self._laser_adapter.set_channel_enable(app_config.devices.ibeam.beam_ch, False)
        except Exception as e:  # noqa: BLE001
            print(f"Failed to disable laser channel: {e}")

        self._cleanup_laser()
        self._view.set_laser_emission_checked(False)
        self._view.set_laser_current_power(None)
        self._view.set_laser_connected(False)

    @Slot()
    def set_laser_power(self) -> None:
        # 出力設定
        if self._laser_adapter is None:
            return
        try:
            app_config = AppConfig.load()
            power = Power(self._view.laser_power_spin.value(), "m")
            self._laser_adapter.set_channel_power(app_config.devices.ibeam.beam_ch, power)
            self._update_laser_current_power(app_config)
        except Exception as e:  # noqa: BLE001
            self._show_error(f"レーザー 出力設定エラー: {e}")

    @Slot(bool)
    def set_laser_emission(self, enable: bool) -> None:
        # Emission切替
        if self._laser_adapter is None:
            return
        try:
            self._laser_adapter.set_emission(enable)
        except Exception as e:  # noqa: BLE001
            self._show_error(f"レーザー Emission切替エラー: {e}")

    # =================================================
    # GM10 Workflow -> View
    # =================================================

    @Slot(object)
    def on_gm10_result(self, result: ManualResult) -> None:
        if result.gm10_values:
            self._view.update_gm10_values(result.gm10_values)

    @Slot(str)
    def on_gm10_error(self, message: str) -> None:
        self._show_error(f"GM10 エラー: {message}")
        self.status_message_requested.emit(message, 10000)

    @Slot()
    def on_gm10_finished(self) -> None:
        self._view.set_gm10_connected(False)

    # =================================================

    def try_switch_from(self) -> bool:
        # タブ切替時: 接続中なら確認ダイアログ
        if not self._has_active_connections():
            return True

        if not self._view.confirm_disconnect_all():
            return False

        self.disconnect_all()
        return True

    def disconnect_all(self) -> None:
        # 一括切断（タブ切替時に使用）
        self.disconnect_gm10()
        self.disconnect_pwux()
        self.disconnect_laser()

    def _has_active_connections(self) -> bool:
        return (
            self._gm10_runner.is_running()
            or self._pwux_adapter is not None
            or self._laser_adapter is not None
        )

    def _cleanup_pwux(self) -> None:
        # PWUXの接続解除処理
        if self._pwux_adapter:
            try:
                self._pwux_adapter.close()
            except Exception as e:  # noqa: BLE001
                print(f"Error closing PWUX adapter: {e}")
        self._pwux_adapter = None

        if self._pwux_rm:
            try:
                self._pwux_rm.close()
            except Exception as e:  # noqa: BLE001
                print(f"Error closing PWUX RM: {e}")
        self._pwux_rm = None

    def _cleanup_laser(self) -> None:
        # Laserの接続解除処理
        if self._laser_adapter:
            try:
                self._laser_adapter.close()
            except Exception as e:  # noqa: BLE001
                print(f"Error closing laser adapter: {e}")
        self._laser_adapter = None

        if self._laser_rm:
            try:
                self._laser_rm.close()
            except Exception as e:  # noqa: BLE001
                print(f"Error closing laser RM: {e}")
        self._laser_rm = None

    def _update_laser_current_power(self, app_config: AppConfig) -> None:
        if self._laser_adapter is None:
            return
        try:
            power = self._laser_adapter.get_channel_power(app_config.devices.ibeam.beam_ch)
            self._view.set_laser_current_power(power)
        except Exception as e:  # noqa: BLE001
            self._show_error(f"レーザー 出力取得エラー: {e}")

    def _show_error(self, message: str) -> None:
        self._view.show_error(message)
