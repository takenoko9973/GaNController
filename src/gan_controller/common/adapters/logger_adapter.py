import random
import time
from abc import ABC, abstractmethod

from gan_controller.common.drivers.gm10 import GM10
from gan_controller.common.types.quantity import Quantity


# Interface
class ILoggerAdapter(ABC):
    @abstractmethod
    def read_voltage(self, channel: int | str, unit: str) -> Quantity:
        """指定チャンネルの電圧を読み取る"""

    @abstractmethod
    def read_integrated_voltage(
        self, channel: int | str, unit: str, n: int, interval: float
    ) -> Quantity:
        """指定チャンネルを積算平均して読み取る"""

    # 必要であればクローズ処理など
    @abstractmethod
    def close(self) -> None:
        pass


class GM10Adapter(ILoggerAdapter):
    def __init__(self, driver: GM10) -> None:
        self._driver = driver

    def read_voltage(self, channel: int | str, unit: str = "V") -> Quantity:
        raw_val = self._driver.read_channel(channel)
        # GM10の生の戻り値がエラー(nan)の場合のハンドリングもここで可能
        return Quantity(raw_val, unit)  # 単位はGM10の設定によるが通常Vと仮定

    def read_integrated_voltage(
        self, channel: int | str, unit: str = "V", n: int = 1, interval: float = 0.1
    ) -> Quantity:
        """指定のチャンネルについて、積算平均を行う"""
        if n <= 0:
            msg = "n must be positive"
            raise ValueError(msg)
        if interval <= 0:
            msg = "interval must be positive"
            raise ValueError(msg)

        results: list[float] = []
        t0 = time.perf_counter()
        for i in range(n):
            # 測定予定時刻
            target_time = t0 + i * interval

            # 予定時刻まで待機
            # (sleep(t) だけでは測定による遅延を考慮できないため)
            now = time.perf_counter()
            sleep_time = target_time - now
            if sleep_time > 0:
                time.sleep(sleep_time)

            # 生のドライバを呼ぶ
            value = self._driver.read_channel(channel)
            results.append(value)

        return Quantity(sum(results) / n, unit)

    def close(self) -> None:
        self._driver.close()


# ダミー用
class MockLoggerAdapter(ILoggerAdapter):
    def __init__(self, base_voltage: float = 1.0, noise_level: float = 0.01) -> None:
        self.base_voltage = base_voltage
        self.noise_level = noise_level

    def read_voltage(self, channel: int | str, unit: str = "V") -> Quantity:  # noqa: ARG002
        # ランダムなノイズを乗せた値を返す
        noise = random.uniform(-self.noise_level, self.noise_level)  # noqa: S311
        val = self.base_voltage + noise

        return Quantity(val, unit)

    def read_integrated_voltage(
        self, channel: int | str, unit: str = "V", n: int = 1, interval: float = 0.1
    ) -> Quantity:
        # ダミーでも時間の経過をシミュレートする (UIが固まらないか確認するため)
        total_wait = n * interval
        if total_wait > 0:
            time.sleep(total_wait)

        return self.read_voltage(channel, unit)

    def close(self) -> None:
        print("Mock logger closed.")
