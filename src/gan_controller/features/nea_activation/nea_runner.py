import time

from gan_controller.dto.nea_activation import NEAActivationResult
from gan_controller.runners.base import BaseRunner


class NEAActivationRunner(BaseRunner):
    def __init__(self) -> None:
        super().__init__()
        # self.devices = devices
        # self.config = config

    def run(self) -> None:
        while not self._stop:
            time.sleep(1)
            print("hoge")
