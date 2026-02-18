from abc import ABC, abstractmethod

from gan_controller.core.domain.hardware import IExperimentHardwareFacade
from gan_controller.core.domain.quantity import Ampere, Quantity
from gan_controller.features.heat_cleaning.domain.config import ProtocolConfig

from .models import HCExperimentResult


class IHCHardwareFacade(IExperimentHardwareFacade):
    """HeatCleaningRunnerがハードウェアを操作するためのインターフェース"""

    @abstractmethod
    def setup_for_protocol(self, protocol: ProtocolConfig) -> None:
        """プロトコルに応じた初期設定 (出力ON/OFFなど) を行う"""

    @abstractmethod
    def set_currents(
        self, hc_current: Quantity[Ampere] | None, amd_current: Quantity[Ampere] | None
    ) -> None:
        """
        電源の電流値を設定する

        Args:
            hc_current (Quantity[Ampere]): HC電源への指令値
            amd_current (Quantity[Ampere]): AMD電源への指令値

        """

    @abstractmethod
    def read_metrics(self) -> HCExperimentResult:
        """現在のセンサー値や電源状態を読み取り、Resultオブジェクトとして返す"""


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
