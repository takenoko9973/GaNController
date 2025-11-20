from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QInputDialog, QMessageBox

from heater_amd_controller.logics.hardware_manager import HardwareManager, SensorData
from heater_amd_controller.logics.protocol_manager import ProtocolManager
from heater_amd_controller.models.protocol import SEQUENCE_NAMES, ProtocolConfig
from heater_amd_controller.views.tabs.heat_cleaning_tab import HeatCleaningTab


class HeatCleaningController(QObject):
    status_message_requested = Signal(str, int)  # メッセージシグナル (メッセージ内容, 表示時間ms)

    def __init__(self, view: HeatCleaningTab, manager: ProtocolManager) -> None:
        super().__init__()
        self.view = view
        self.manager = manager

        self.hw_manager = HardwareManager()

        # 読み込み直後、保存直後のデータ
        self._last_loaded_data: ProtocolConfig | None = None

        # --- 実行制御用変数 ---
        self.timer = QTimer(self)
        self.timer.setInterval(1000)  # 1秒毎カウント
        self.timer.timeout.connect(self._on_timer_tick)

        self._running_config: ProtocolConfig | None = None  # 実行プロトコル状態を保存
        self._total_elapsed_sec = 0
        self._sequence_elapsed_sec = 0

        self._next_log_sec = 0  # ログ書き込み予定時間

        # 状態管理
        self._current_sequence_idx = 0  # シーケンス数

        # --- シグナル接続 ---
        self.view.execution_toggled.connect(self.on_execution_toggled)
        self.view.protocol_changed.connect(self.on_protocol_selected)
        self.view.save_requested.connect(self.on_save_requested)

        # 初期化処理
        self.initialize_view()

    def initialize_view(self) -> None:
        self.refresh_list()

    def refresh_list(self, select_name: str | None = None) -> None:
        """リストを更新し、指定があればそれを選択する"""
        names = self.manager.get_protocol_names()
        self.view.set_protocol_list(names)

        if select_name and select_name in names:
            target_name = select_name
        elif names:
            target_name = names[0]

        if target_name:
            self.view.select_protocol(target_name)
            self.on_protocol_selected(target_name)  # 更新

    def on_protocol_selected(self, protocol_name: str) -> None:
        """プロトコル変更"""
        print(f"[HC_Ctrl] プロトコル変更: {protocol_name}")

        data = self.manager.get_protocol(protocol_name)
        self._last_loaded_data = data  # 読み込み直後のデータを取得

        self.view.update_ui_from_data(data)

    def on_save_requested(self) -> None:
        """プロトコル保存時"""
        # データ読み込み
        current_name = self.view.get_current_protocol_name()
        current_data = self.view.get_current_ui_data()

        # 保存する名前を決定
        save_name = self._determine_save_name(current_name)
        if not save_name:
            return

        # 変更があるか確認し、必要ならユーザーに聞く
        if not self._confirm_overwrite_if_needed(save_name, current_data):
            return

        # 保存実行
        self._protocol_save(save_name, current_data)

    def _determine_save_name(self, current_name: str) -> str | None:
        """新規ならダイアログ、既存ならそのまま名前を返す"""
        if current_name == self.manager.NEW_PROTOCOL_NAME:
            text, ok = QInputDialog.getText(
                self.view, "プロトコル保存", "新しいプロトコル名を入力してください:"
            )
            return text.strip() if ok and text else None

        return current_name

    def _confirm_overwrite_if_needed(self, current_name: str, current_data: ProtocolConfig) -> bool:
        """変更がある場合の上書き確認。保存してよければ True を返す"""
        if self._last_loaded_data and current_data != self._last_loaded_data:  # 差分確認
            # 確認ダイアログ
            reply = QMessageBox.question(
                self.view,
                "変更の確認",
                f"プロトコル '{current_name}' に変更があります。\n上書き保存しますか？",  # noqa: RUF001
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,  # デフォルトはNo (安全側)
            )

            if reply != QMessageBox.StandardButton.Yes:
                return False  # 保存中止

        return True

    def _protocol_save(self, current_name: str, current_data: ProtocolConfig) -> None:
        """Managerを呼んで保存し、UI更新"""
        success = self.manager.save_protocol(current_name, current_data)
        if success:
            print(f"[HC_Ctrl] 保存: {current_name}")

            msg = f"保存完了: {current_name} を保存しました。"
            self.status_message_requested.emit(msg, 5000)

            self._last_loaded_data = current_data  # 保存直後のデータに更新

            self.refresh_list(select_name=current_name)
        else:
            self.status_message_requested.emit("エラー: 保存に失敗しました。", 10000)

    # ============================================================================
    # 実行制御
    # ============================================================================

    def on_execution_toggled(self, is_running: bool) -> None:
        """開始/停止ボタン"""
        if is_running:
            self._start_protocol()
        else:
            self._stop_protocol()

    def _start_protocol(self) -> None:
        print("[HC_Ctrl] プロトコル開始")

        self.hw_manager.connect_devices()

        # 現在の設定を読み込み
        self._running_config = self.view.get_current_ui_data()

        # カウンタ初期化
        self._total_elapsed_sec = 0  # 合計時間
        self._sequence_elapsed_sec = 0  # シーケンス時間
        self._next_log_sec = 0  # ログ予定時間
        self._current_loop = 1  # ループ回数
        self._current_sequence_idx = 0  # 現在のシーケンスインデックス

        # UI初期化
        self._update_status_display()

        self.timer.start()

    def _stop_protocol(self) -> None:
        """プロトコル停止 (リセット)"""
        print("[HC_Ctrl] プロトコル停止")
        self.timer.stop()

        self.hw_manager.disconnect_devices()

        self.view.update_execution_status(
            "停止",
            self._format_time(0),
            self._format_time(self._total_elapsed_sec),
            False,  # noqa: FBT003
        )
        self._running_config = None
        self.status_message_requested.emit("プロトコルを停止しました。", 5000)

    def _finish_protocol(self) -> None:
        print("[HC_Ctrl] プロトコル完了")
        self.timer.stop()
        self.hw_manager.disconnect_devices()

        total_str = self._format_time(self._total_elapsed_sec)
        self.view.update_execution_status("完了", "00:00:00", total_str, False)  # noqa: FBT003

        # ボタンを「開始」に戻す
        self.view.execution_group.exec_button.force_stop()
        self._running_config = None

        self.status_message_requested.emit("プロトコルが完了しました。", 0)

    def _on_timer_tick(self) -> None:
        """1秒ごとの処理 (UI更新 & 状態遷移チェック)"""
        if not self._running_config:
            return

        # 時間を進める
        self._total_elapsed_sec += 1
        self._sequence_elapsed_sec += 1

        current_values = self._perform_measurement()
        self._update_measure_values(current_values)

        if self._total_elapsed_sec >= self._next_log_sec:
            self._perform_logging(current_values)

            interval = max(1, int(self._running_config.step_interval))
            self._next_log_sec += interval

        # --- 状態遷移チェック ---
        current_step_name = SEQUENCE_NAMES[self._current_sequence_idx % len(SEQUENCE_NAMES)]
        target_duration_sec = self._running_config.sequence_hours.get(current_step_name, 0.0) * 3600

        if self._sequence_elapsed_sec >= target_duration_sec:
            self._check_next_sequence()

        # --- 画面更新 ---
        self._update_status_display()

    def _check_next_sequence(self) -> None:
        """次のステップまたは次のループへ進める"""
        if not self._running_config:
            return

        self._sequence_elapsed_sec = 0
        self._current_sequence_idx += 1

        current_loop = self._current_sequence_idx // len(SEQUENCE_NAMES)
        if current_loop >= self._running_config.repeat_count:
            self._finish_protocol()
            return

    def _perform_measurement(self) -> SensorData:
        """測定処理"""
        return self.hw_manager.read_all()

    def _update_measure_values(self, data: SensorData) -> None:
        hc_vals = (data.hc_current, data.hc_voltage, data.hc_power)
        amd_vals = (data.amd_current, data.amd_voltage, data.amd_power)

        self.view.execution_group.update_sensor_values(
            hc_vals, amd_vals, data.temperature, data.pressure_ext, data.pressure_sip
        )

    def _perform_logging(self, data: SensorData) -> None:
        """ログ書き込み処理"""
        print(f"[Log] Time={self._total_elapsed_sec}s | Temp={data.temperature:.2f}")

    def _update_status_display(self) -> None:
        """現在の状態をUIに反映"""
        if not self._running_config:
            return

        # 完了済みなら更新しない
        if self._current_loop > self._running_config.repeat_count:
            return

        current_step_name = SEQUENCE_NAMES[self._current_sequence_idx % len(SEQUENCE_NAMES)]
        status_text = f"{self._current_sequence_idx + 1}.{current_step_name}"

        step_str = self._format_time(self._sequence_elapsed_sec)
        total_str = self._format_time(self._total_elapsed_sec)

        self.view.update_execution_status(status_text, step_str, total_str, True)  # noqa: FBT003

    def _format_time(self, seconds: int) -> str:
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
