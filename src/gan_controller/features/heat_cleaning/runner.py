import datetime
import queue

from gan_controller.common.application.runner import BaseRunner
from gan_controller.common.schemas.app_config import AppConfig
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
            start_time = datetime.datetime.now(tz)
            print(f"\033[32m{start_time:%Y/%m/%d %H:%M:%S} Experiment start\033[0m")

            # 設定に基づいて適切なFactoryを選択する
            # is_simulation = getattr(self.app_config.common, "is_simulation_mode", False)
            # device_factory = SimulationDeviceFactory() if is_simulation else RealDeviceFactory()

            # with NEADeviceManager(self.app_config, factory=device_factory) as dev:
            #     self._setup_devices(dev)
            #     self._measurement_loop(dev)

        except Exception as e:
            # エラー発生時はログ出力などを行う
            print(f"Experiment Error: {e}")
            raise  # Workerスレッド側でキャッチさせるために再送出

        finally:
            finish_time = datetime.datetime.now(tz)
            print(f"\033[31m{finish_time:%Y/%m/%d %H:%M:%S} Finish\033[0m")

    # =================================================================
