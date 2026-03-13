from collections.abc import Callable

from PySide6.QtCore import Slot

from gan_controller.core.domain.app_config import AppConfig
from gan_controller.features.manual_operation.application.device_handlers import (
    LaserHandler,
    PwuxHandler,
)
from gan_controller.features.manual_operation.application.workflow import GM10MonitorWorkflow
from gan_controller.features.manual_operation.domain.models import ManualResult
from gan_controller.features.manual_operation.presentation.view import ManualOperationMainView
from gan_controller.presentation.async_runners.manager import AsyncExperimentManager
from gan_controller.presentation.components.tab_controller import ITabController


class ManualOperationController(ITabController):
    _view: ManualOperationMainView
    _gm10_runner: AsyncExperimentManager
    _pwux: PwuxHandler
    _laser: LaserHandler

    def __init__(self, view: ManualOperationMainView) -> None:
        super().__init__()
        self._view = view
        # GM10は監視スレッドで管理する
        self._gm10_runner = AsyncExperimentManager()
        self._pwux = PwuxHandler()
        self._laser = LaserHandler()

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
        # GM10の監視結果をUIへ反映
        self._gm10_runner.step_result_observed.connect(self.on_gm10_result)
        self._gm10_runner.error_occurred.connect(self.on_gm10_error)
        self._gm10_runner.finished.connect(self.on_gm10_finished)

    def _load_channel_config(self) -> None:
        # 起動時にGM10のチャンネル表示だけ先にセットしておく
        app_config = self._load_app_config(show_error=False)
        if app_config is None:
            return
        self._view.set_gm10_channel_config(app_config.devices.gm10)

    # =================================================
    # View -> GM10 Workflow
    # =================================================

    @Slot()
    def connect_gm10(self) -> None:
        # GM10のみを監視スレッドで接続・監視開始
        if self._gm10_runner.is_running():
            return

        def do_connect(app_config: AppConfig) -> None:
            self._view.set_gm10_channel_config(app_config.devices.gm10)

            def start_monitor() -> None:
                workflow = GM10MonitorWorkflow(app_config, poll_interval=1.0)
                self._gm10_runner.start_workflow(workflow)
                self._view.set_gm10_connected(True)

            if not self._guard_action("GM10 接続エラー", start_monitor):
                self._view.set_gm10_connected(False)

        self._with_app_config(do_connect)

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
        self._connect_device(
            label="PWUX",
            is_connected=self._pwux.is_connected,
            connect_action=self._pwux.connect,
            on_success=lambda: self._view.set_pwux_connected(True),
            on_failure=self._pwux.disconnect,
        )

    @Slot()
    def disconnect_pwux(self) -> None:
        # 切断前に照準を必ずOFF
        if not self._pwux.is_connected:
            return
        self._pwux.disconnect()
        self._view.set_pwux_pointer_checked(False)
        self._view.set_pwux_connected(False)

    @Slot()
    def request_pwux_temperature(self) -> None:
        # 手動で温度取得
        if not self._pwux.is_connected:
            return
        temperature = self._guard_value("PWUX 温度取得エラー", self._pwux.read_temperature)
        if temperature is not None:
            self._view.set_pwux_temperature(temperature)

    @Slot(bool)
    def set_pwux_pointer(self, enable: bool) -> None:
        # 照準表示のON/OFF
        if not self._pwux.is_connected:
            return
        self._guard_action("PWUX 照準表示切替エラー", lambda: self._pwux.set_pointer(enable))

    # =================================================
    # View -> Laser
    # =================================================

    @Slot()
    def connect_laser(self) -> None:
        # Laserを個別接続し、CH有効化 + Emission OFFで初期化
        self._connect_device(
            label="レーザー",
            is_connected=self._laser.is_connected,
            connect_action=self._laser.connect,
            on_success=self._on_laser_connected,
            on_failure=self._laser.disconnect,
        )

    @Slot()
    def disconnect_laser(self) -> None:
        # Emission OFF + CH無効化を行ってから切断
        if not self._laser.is_connected:
            return
        self._laser.disconnect()
        self._view.set_laser_emission_checked(False)
        self._view.set_laser_current_power(None)
        self._view.set_laser_connected(False)

    @Slot()
    def set_laser_power(self) -> None:
        # 出力設定
        if not self._laser.is_connected:
            return
        if self._guard_action(
            "レーザー 出力設定エラー",
            lambda: self._laser.set_power(self._view.laser_power_spin.value()),
        ):
            self._update_laser_current_power()

    @Slot(bool)
    def set_laser_emission(self, enable: bool) -> None:
        # Emission切替
        if not self._laser.is_connected:
            return
        self._guard_action("レーザー Emission切替エラー", lambda: self._laser.set_emission(enable))

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

    def on_close(self) -> None:
        # アプリ終了時は無条件で安全停止
        self.disconnect_all()

    def disconnect_all(self) -> None:
        # 一括切断（タブ切替時に使用）
        self.disconnect_gm10()
        self.disconnect_pwux()
        self.disconnect_laser()

    def _has_active_connections(self) -> bool:
        return self._gm10_runner.is_running() or self._pwux.is_connected or self._laser.is_connected

    def _load_app_config(self, show_error: bool = True) -> AppConfig | None:
        try:
            return AppConfig.load()
        except (OSError, ValueError) as e:
            if show_error:
                self._show_error(f"設定読み込みエラー: {e}")
            return None

    def _with_app_config(self, action: Callable[[AppConfig], None]) -> None:
        # 設定読み込みに成功したときだけ処理を進める
        app_config = self._load_app_config()
        if app_config is None:
            return
        action(app_config)

    def _connect_device(
        self,
        label: str,
        is_connected: bool,
        connect_action: Callable[[AppConfig], None],
        on_success: Callable[[], None],
        on_failure: Callable[[], None],
    ) -> None:
        if is_connected:
            return

        def do_connect(app_config: AppConfig) -> None:
            if self._guard_action(f"{label} 接続エラー", lambda: connect_action(app_config)):
                on_success()
            else:
                on_failure()

        self._with_app_config(do_connect)

    def _show_error(self, message: str) -> None:
        self._view.show_error(message)

    def _update_laser_current_power(self) -> None:
        if not self._laser.is_connected:
            return
        power = self._guard_value("レーザー 出力取得エラー", self._laser.get_current_power)
        if power is not None:
            self._view.set_laser_current_power(power)

    def _on_laser_connected(self) -> None:
        self._update_laser_current_power()
        self._view.set_laser_connected(True)

    def _guard_action(self, label: str, action: Callable[[], None]) -> bool:
        # 例外をまとめて捕捉し、UIへエラーを通知する
        try:
            action()
            return True
        except Exception as e:  # noqa: BLE001
            self._show_error(f"{label}: {e}")
            return False

    def _guard_value[T](self, label: str, action: Callable[[], T]) -> T | None:
        # 返り値が必要な処理向けの共通ガード
        try:
            return action()
        except Exception as e:  # noqa: BLE001
            self._show_error(f"{label}: {e}")
            return None
