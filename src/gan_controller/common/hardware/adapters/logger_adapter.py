import random
import time
from abc import ABC, abstractmethod

from gan_controller.common.domain.quantity import Quantity, Volt
from gan_controller.common.hardware.drivers.gm10 import GM10


# Interface
class ILoggerAdapter(ABC):
    @abstractmethod
    def read_voltage(self, channel: int | str, unit: str) -> Quantity[Volt]:
        """指定チャンネルの電圧を読み取る"""

    @abstractmethod
    def read_integrated_voltage(
        self, channel: int | str, unit: str, n: int, interval: float
    ) -> Quantity[Volt]:
        """指定チャンネルを積算平均して読み取る"""

    # 必要であればクローズ処理など
    @abstractmethod
    def close(self) -> None:
        pass


class GM10Adapter(ILoggerAdapter):
    def __init__(self, driver: GM10) -> None:
        self._driver = driver

    def read_voltage(self, channel: int | str, unit: str = "V") -> Quantity[Volt]:
        if isinstance(channel, int) and channel <= 0:
            return Quantity(float("nan"), unit)

        try:
            raw_val = self._driver.read_channel(channel)
            return Quantity(raw_val, unit)

        except (RuntimeError, ValueError) as e:
            # チャンネル設定ミスや、機器からのエラー応答(E1など)があった場合
            # ログを出力して NaN (欠損値) を返す
            print(f"\033[33m[WARNING] GM10 Read Error (Ch: {channel}): {e}\033[0m")
            return Quantity(float("nan"), unit)

    def read_integrated_voltage(
        self, channel: int | str, unit: str = "V", n: int = 1, interval: float = 0.1
    ) -> Quantity[Volt]:
        """指定のチャンネルについて、積算平均を行う"""
        if n <= 0:
            msg = "n must be positive"
            raise ValueError(msg)
        if interval <= 0:
            msg = "interval must be positive"
            raise ValueError(msg)

        # ============================================================

        if isinstance(channel, int) and channel <= 0:
            return Quantity(float("nan"), unit)

        results: list[float] = []
        t0 = time.perf_counter()
        try:
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

            result_avg = sum(results) / n
            return Quantity(result_avg, unit)

        except (RuntimeError, ValueError) as e:
            # 積算中にエラーが発生した場合 (チャンネル無効など)
            print(f"GM10 Integrated Read Error (Ch: {channel}): {e}")
            return Quantity(float("nan"), unit)

    def close(self) -> None:
        self._driver.close()


# ダミー用
class MockLoggerAdapter(ILoggerAdapter):
    def __init__(self, base_voltage: float = 1.0, noise_level: float = 0.01) -> None:
        self.base_voltage = base_voltage
        self.noise_level = noise_level

    def read_voltage(self, channel: int | str, unit: str = "V") -> Quantity[Volt]:
        if isinstance(channel, int) and channel < 0:
            return Quantity(float("nan"), unit)

        # ランダムなノイズを乗せた値を返す
        noise = random.uniform(-self.noise_level, self.noise_level)  # noqa: S311
        val = self.base_voltage + noise

        return Quantity(val, unit)

    def read_integrated_voltage(
        self, channel: int | str, unit: str = "V", n: int = 1, interval: float = 0.1
    ) -> Quantity[Volt]:
        if n <= 0:
            msg = "n must be positive"
            raise ValueError(msg)
        if interval <= 0:
            msg = "interval must be positive"
            raise ValueError(msg)

        # ダミーでも時間の経過をシミュレートする (UIが固まらないか確認するため)
        total_wait = n * interval
        if total_wait > 0:
            time.sleep(total_wait)

        return self.read_voltage(channel, unit)

    def close(self) -> None:
        print("Mock logger closed.")
