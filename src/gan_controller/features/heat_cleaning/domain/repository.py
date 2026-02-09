from abc import ABC, abstractmethod

from gan_controller.features.heat_cleaning.schemas.config import ProtocolConfig


class IProtocolRepository(ABC):
    """プロトコル設定の読み書きに関する抽象定義"""

    @abstractmethod
    def list_names(self) -> list[str]: ...

    @abstractmethod
    def load(self, name: str) -> ProtocolConfig: ...

    @abstractmethod
    def save(self, name: str, config: ProtocolConfig) -> None: ...

    @abstractmethod
    def exists(self, name: str) -> bool: ...
