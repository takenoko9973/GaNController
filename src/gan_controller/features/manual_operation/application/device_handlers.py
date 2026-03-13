from __future__ import annotations

from typing import TYPE_CHECKING

from gan_controller.core.domain.quantity import Power
from gan_controller.features.manual_operation.infrastructure.device_clients import (
    LaserClient,
    PwuxClient,
)

if TYPE_CHECKING:
    from gan_controller.core.domain.app_config import AppConfig
    from gan_controller.core.domain.quantity import Celsius, Quantity, Watt


class PwuxHandler:
    """PWUXの低レベル操作をアプリ層でまとめる。"""

    def __init__(self, client: PwuxClient | None = None) -> None:
        self._client = client or PwuxClient()

    @property
    def is_connected(self) -> bool:
        return self._client.is_connected

    def connect(self, app_config: AppConfig) -> None:
        # 設定を受け取って接続だけを担当する
        self._client.connect(app_config)

    def disconnect(self) -> None:
        # 切断時に照準OFFも合わせて実施
        self._client.disconnect()

    def read_temperature(self) -> Quantity[Celsius]:
        return self._client.read_temperature()

    def set_pointer(self, enable: bool) -> None:
        self._client.set_pointer(enable)


class LaserHandler:
    """レーザーの接続と出力操作をアプリ層でまとめる。"""

    def __init__(self, client: LaserClient | None = None) -> None:
        self._client = client or LaserClient()

    @property
    def is_connected(self) -> bool:
        return self._client.is_connected

    def connect(self, app_config: AppConfig) -> None:
        # 接続時にCH有効化とEmission OFFまで実施
        self._client.connect(app_config)

    def disconnect(self) -> None:
        # Emission OFFとCH無効化を行ってから切断
        self._client.disconnect()

    def set_power(self, power_mw: float) -> None:
        self._client.set_power(Power(power_mw, "m"))

    def set_emission(self, enable: bool) -> None:
        self._client.set_emission(enable)

    def get_current_power(self) -> Quantity[Watt]:
        return self._client.get_current_power()
