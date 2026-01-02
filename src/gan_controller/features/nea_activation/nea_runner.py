import time

from gan_controller.common.interfaces.runner import BaseRunner


class NEAActivationRunner(BaseRunner):
    def __init__(self) -> None:
        super().__init__()
        # self.devices = devices
        # self.config = config

    def run(self) -> None:
        while not self._stop:
            time.sleep(1)
            print("hoge")
