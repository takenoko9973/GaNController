from abc import abstractmethod

from gan_controller.core.domain.hardware import IExperimentHardwareFacade
from gan_controller.core.domain.quantity import Celsius, Quantity, Volt, Watt


class IManualHardwareFacade(IExperimentHardwareFacade):
    """手動操作タブがハードウェアを操作するためのインターフェース"""

    @abstractmethod
    def setup_devices(self) -> None:
        """接続後の初期設定"""

    @abstractmethod
    def read_gm10_values(self) -> dict[str, Quantity[Volt]]:
        """GM10の各設定チャンネル値を取得"""

    @abstractmethod
    def read_pwux_temperature(self) -> Quantity[Celsius]:
        """PWUX温度取得"""

    @abstractmethod
    def set_pwux_pointer(self, enable: bool) -> None:
        """PWUX照準表示の切替"""

    @abstractmethod
    def set_laser_power(self, power: Quantity[Watt]) -> None:
        """レーザー出力を設定"""

    @abstractmethod
    def set_laser_emission(self, enable: bool) -> None:
        """レーザー出力のON/OFFを切替"""
