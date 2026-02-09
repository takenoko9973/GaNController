from gan_controller.common.domain.quantity.quantity import Quantity
from gan_controller.common.domain.quantity.unit_types import Pascal
from gan_controller.common.hardware.adapters.logger_adapter import ILoggerAdapter
from gan_controller.common.hardware.processing.vacuum_reader import VacuumSensorReader
from gan_controller.common.schemas.app_config import AppConfig


class HCSensorReader:
    """HeatCleaning用のセンサー読み取りサービス"""

    def __init__(self, adapter: ILoggerAdapter, config: AppConfig) -> None:
        self._adapter = adapter
        self._config = config

        self._vacuum_reader = VacuumSensorReader(adapter, config.devices.gm10)

    def read_ext(self) -> Quantity[Pascal]:
        return self._vacuum_reader.read_ext_pressure()

    def read_sip(self) -> Quantity[Pascal]:
        return self._vacuum_reader.read_sip_pressure()
