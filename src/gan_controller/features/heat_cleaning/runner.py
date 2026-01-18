import datetime
import queue

from gan_controller.common.application.runner import BaseRunner
from gan_controller.common.io.log_manager import LogManager
from gan_controller.common.schemas.app_config import AppConfig
from gan_controller.features.heat_cleaning.devices import (
    HCDeviceManager,
    HCDevices,
    RealHCDeviceFactory,
    SimulationHCDeviceFactory,
)
from gan_controller.features.heat_cleaning.recorder import HCLogRecorder
from gan_controller.features.heat_cleaning.schemas.config import ProtocolConfig


class HCActivationRunner(BaseRunner):
    app_config: AppConfig  # 全体設定
    protocol_config: ProtocolConfig  # 実験条件

    # _recorder: HCLogRecorder
    _request_queue: queue.Queue

    def __init__(self, app_config: AppConfig, protocol_config: ProtocolConfig) -> None:
        super().__init__()
        self.app_config = app_config  # VISAアドレスなど
        self.protocol_config = protocol_config  # 実験条件

        self._request_queue = queue.Queue()  # スレッド通信用キュー

    # =================================================================

    def run(self) -> None:
        """実験開始"""
        tz = self.app_config.common.get_tz()
        try:
            # 設定に基づいて適切なFactoryを選択する
            is_simulation = getattr(self.app_config.common, "is_simulation_mode", False)
            device_factory = SimulationHCDeviceFactory() if is_simulation else RealHCDeviceFactory()

            start_time = datetime.datetime.now(tz)
            print(f"\033[32m{start_time:%Y/%m/%d %H:%M:%S} Experiment start\033[0m")
            self._setup_recorder(start_time)

            with HCDeviceManager(self.app_config, factory=device_factory) as dev:
                self._setup_devices(dev)
                # self._measurement_loop(dev)

        except Exception as e:
            # エラー発生時はログ出力などを行う
            print(f"Experiment Error: {e}")
            raise  # Workerスレッド側でキャッチさせるために再送出

        finally:
            finish_time = datetime.datetime.now(tz)
            print(f"\033[31m{finish_time:%Y/%m/%d %H:%M:%S} Finish\033[0m")

    # =================================================================

    def _setup_recorder(self, start_time: datetime.datetime) -> None:
        """記録用ファイルの準備とヘッダー書き込み"""
        manager = LogManager(self.app_config)

        # ログファイル準備
        update_date = self.protocol_config.log.update_date_folder
        major_update = self.protocol_config.log.update_major_number

        log_dir = manager.get_date_directory(update_date)
        log_file = log_dir.create_logfile(protocol_name="NEA", major_update=major_update)
        print(f"Recording to: {log_file.path}")

        # レコーダー準備
        self._recorder = HCLogRecorder(log_file, self.protocol_config)
        self._recorder.record_header(start_time=start_time)

    def _setup_devices(self, devices: HCDevices) -> None:
        """実験前の初期設定"""
        print("Setting up devices...")

        # self._init_laser_static(devices.laser)
        # self._init_aps_static(devices.aps)
        # self._init_gm10_static(devices.logger)

        # # 動的設定の適応
        # self._apply_params_to_device(devices, self.nea_config.control)
