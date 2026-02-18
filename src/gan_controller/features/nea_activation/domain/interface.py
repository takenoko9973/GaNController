from abc import abstractmethod

from gan_controller.core.domain.hardware import IExperimentHardwareFacade
from gan_controller.core.domain.quantity import Ampere, Ohm, Quantity, Volt
from gan_controller.features.nea_activation.domain.config import (
    NEAConditionConfig,
    NEAControlConfig,
)
from gan_controller.features.nea_activation.domain.models import NEARunnerResult


class INEAHardwareFacade(IExperimentHardwareFacade):
    """NEAActivationRunnerがハードウェアを操作するためのインターフェース"""

    @abstractmethod
    def setup_devices(self) -> None:
        """実験前の静的な初期設定 (チャンネル有効化、安全設定など) を行う"""

    @abstractmethod
    def apply_control_params(self, params: NEAControlConfig) -> None:
        """実験中の動的なパラメータ (レーザー出力、AMD電源設定) を適用する"""

    @abstractmethod
    def set_laser_emission(self, enable: bool) -> None:
        """レーザーの出力をON/OFFする"""

    @abstractmethod
    def read_photocurrent(
        self, shunt_r: Quantity[Ohm], count: int, interval: float
    ) -> tuple[Quantity[Volt], Quantity[Ampere]]:
        """指定された条件で光電流を積分測定し、電圧値と電流値を返す"""

    @abstractmethod
    def read_metrics(
        self,
        control_config: NEAControlConfig,
        condition_config: NEAConditionConfig,
        timestamp: float,
        bright_pc: Quantity[Ampere],
        bright_pc_voltage: Quantity[Volt],
        dark_pc: Quantity[Ampere],
        dark_pc_voltage: Quantity[Volt],
    ) -> NEARunnerResult:
        """現在のセンサー値や電源状態を読み取り、測定済みのPC値と合わせてResultオブジェクトを生成する"""
