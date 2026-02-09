from abc import ABC, abstractmethod

from gan_controller.common.domain.quantity import Ampere, Quantity
from gan_controller.features.heat_cleaning.schemas.config import ProtocolConfig

from .models import HCHardwareMetrics


class IHeatCleaningHardware(ABC):
    """HeatCleaningRunnerがハードウェアを操作するためのインターフェース"""

    @abstractmethod
    def set_currents(
        self, hc_current: Quantity[Ampere] | None, amd_current: Quantity[Ampere] | None
    ) -> None:
        """電源の電流値を設定する

        Args:
            hc_current (Quantity[Ampere]): HC電源への指令値
            amd_current (Quantity[Ampere]): AMD電源への指令値

        """

    @abstractmethod
    def read_metrics(self) -> HCHardwareMetrics:
        """現在のセンサー値や電源状態を読み取り、Resultオブジェクトとして返す"""

    @abstractmethod
    def emergency_stop(self) -> None:
        """安全のための停止措置 (出力OFFなど) を行う"""


class IProtocolRepository(ABC):
    """プロトコル設定の読み書きに関するインターフェース"""

    @abstractmethod
    def list_names(self) -> list[str]: ...

    @abstractmethod
    def load(self, name: str) -> ProtocolConfig: ...

    @abstractmethod
    def save(self, name: str, config: ProtocolConfig) -> None: ...

    @abstractmethod
    def exists(self, name: str) -> bool: ...
