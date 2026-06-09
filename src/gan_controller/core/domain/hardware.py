from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

import pyvisa

from gan_controller.core.console_logger import get_logger

logger = get_logger(__name__)


class IHardwareBackend[T_Devices, T_Facade](ABC):
    """すべてのハードウェアBackendが満たすべき共通インターフェース"""

    _devices: T_Devices | None = None
    _rm: pyvisa.ResourceManager | None = None

    def __enter__(self) -> Self:
        """通信リソースを確保し、対象のデバイスコンテナを返す"""
        self._devices, self._rm = self._connect_devices()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """通信リソースを安全に解放・切断する"""
        self._disconnect_devices()

        # VISAリソースマネージャの破棄
        if self._rm:
            try:
                self._rm.close()
                logger.info("[DISCONNECT][ResourceManager] success")
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "[DISCONNECT][ResourceManager] failed: %s",
                    e,
                    extra={"color": "yellow"},
                )

    @abstractmethod
    def _connect_devices(self) -> tuple[T_Devices, pyvisa.ResourceManager | None]:
        """具体的な接続処理"""

    @abstractmethod
    def _disconnect_devices(self) -> None:
        """具体的な切断処理"""

    @abstractmethod
    def get_facade(self) -> T_Facade:
        """準備が完了したFacadeを生成して返す (Factory Method)"""


class IExperimentHardwareFacade(ABC):
    """すべての実験ハードウェアFacadeが必ず実装すべき共通の振る舞い"""

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.emergency_stop()

    @abstractmethod
    def emergency_stop(self) -> None:
        """安全のためのハードウェア停止措置 (出力OFFなど) を行う"""
