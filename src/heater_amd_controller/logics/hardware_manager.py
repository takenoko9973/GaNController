import random
from dataclasses import dataclass


@dataclass
class SensorData:
    """測定値データの型定義"""

    hc_current: float = 0.0
    hc_voltage: float = 0.0
    hc_power: float = 0.0

    amd_current: float = 0.0
    amd_voltage: float = 0.0
    amd_power: float = 0.0

    temperature: float = 0.0
    pressure_ext: float = 0.0
    pressure_sip: float = 0.0


class HardwareManager:
    def __init__(self) -> None:
        # 本来はここで各装置のドライバクラスをインスタンス化する
        # self.hc_device = HeaterDevice(...)
        # self.amd_device = AmdDevice(...)
        # self.gauge_device = VacuumGauge(...)
        self._is_hc_connected = False
        self._is_amd_connected = False

    def connect_devices(self) -> bool:
        """全装置への接続処理"""
        # success = self.hc_device.connect() and ...
        self._is_hc_connected = True
        self._is_amd_connected = True
        return True

    def disconnect_devices(self) -> None:
        """全装置の切断処理"""
        self._is_hc_connected = False
        self._is_amd_connected = False

    def set_hc_current(self, hc_current: float) -> None:
        """ヒーター電源に電流値を設定する"""
        if not self._is_hc_connected:
            return

        self._last_set_hc = hc_current

    def set_amd_current(self, amd_current: float) -> None:
        """AMD用電源に電流値を設定する"""
        if not self._is_amd_connected:
            return

        self._last_set_amd = amd_current

    def read_all(self) -> SensorData:
        """全センサーから最新の値を取得して返す"""
        if not self._is_hc_connected:
            # 未接続時はゼロ埋めデータを返す、などの安全策
            return SensorData()

        # --- Mock: 実際は各装置から値を読む ---
        # hc_vals = self.hc_device.get_output()
        # amd_vals = self.amd_device.get_output()
        # env_vals = self.gauge_device.get_status()

        # ダミーデータの生成
        data = SensorData()

        # HC
        data.hc_current = random.uniform(0, 5)
        data.hc_voltage = random.uniform(10, 12)
        data.hc_power = data.hc_current * data.hc_voltage

        # AMD
        data.amd_current = random.uniform(0, 2)
        data.amd_voltage = random.uniform(5, 5.5)
        data.amd_power = data.amd_current * data.amd_voltage

        # Environment
        data.temperature = 25.0 + random.uniform(-0.1, 0.1)
        data.pressure_ext = 1.2e-8 * random.uniform(0.9, 1.1)
        data.pressure_sip = 3.5e-7 * random.uniform(0.9, 1.1)

        return data
