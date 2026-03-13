import time

import pyvisa

from gan_controller.core.domain.app_config import AppConfig
from gan_controller.core.domain.quantity import Quantity, Volt
from gan_controller.features.manual_operation.domain.models import ManualResult
from gan_controller.infrastructure.hardware.adapters.logger_adapter import (
    GM10Adapter,
    MockLoggerAdapter,
)
from gan_controller.infrastructure.hardware.drivers import GM10
from gan_controller.presentation.async_runners.interfaces import (
    IExperimentObserver,
    IExperimentWorkflow,
)


class GM10MonitorWorkflow(IExperimentWorkflow):
    """GM10の値を一定周期で取得して通知する"""

    def __init__(self, app_config: AppConfig, poll_interval: float) -> None:
        super().__init__()
        self._app_config = app_config
        self._poll_interval = poll_interval
        self._observer: IExperimentObserver | None = None

    def execute(self, observer: IExperimentObserver) -> None:
        self._observer = observer
        adapter = None
        rm = None

        try:
            # 実機/シミュレーションで接続先を切り替える
            if self._app_config.common.is_simulation_mode:
                adapter = MockLoggerAdapter()
            else:
                rm = pyvisa.ResourceManager()
                gm10 = GM10(rm, self._app_config.devices.gm10.visa)
                adapter = GM10Adapter(gm10)

            # 監視ループを開始
            self._run_loop(adapter)

        except Exception as e:  # noqa: BLE001
            self._notify_error(str(e))

        finally:
            # 例外の有無に関わらず安全に切断
            if adapter:
                try:
                    adapter.close()
                except Exception as e:  # noqa: BLE001
                    print(f"Error closing GM10 adapter: {e}")

            if rm:
                try:
                    rm.close()
                except Exception as e:  # noqa: BLE001
                    print(f"Error closing ResourceManager: {e}")

            if self._observer:
                self._observer.on_finished()

    # ==================================================================

    def _run_loop(self, adapter: GM10Adapter | MockLoggerAdapter) -> None:
        # 1秒周期でGM10値をポーリング
        next_poll = time.perf_counter()
        while not self._should_stop():
            now = time.perf_counter()
            if now >= next_poll:
                result = ManualResult(gm10_values=self._read_gm10_values(adapter))
                self._notify_result(result)
                next_poll = now + self._poll_interval

            time.sleep(0.05)

    def _read_gm10_values(
        self, adapter: GM10Adapter | MockLoggerAdapter
    ) -> dict[str, Quantity[Volt]]:
        gm10 = self._app_config.devices.gm10
        return {
            "ext": adapter.read_voltage(gm10.ext_ch),
            "sip": adapter.read_voltage(gm10.sip_ch),
            "hv": adapter.read_voltage(gm10.hv_ch),
            "pc": adapter.read_voltage(gm10.pc_ch),
            "tc": adapter.read_voltage(gm10.tc_ch),
        }

    # ==================================================================

    def _should_stop(self) -> bool:
        if self._observer is None:
            return True
        return self._observer.is_interruption_requested()

    def _notify_result(self, result: ManualResult) -> None:
        if self._observer:
            self._observer.on_step_completed(result)

    def _notify_error(self, message: str) -> None:
        if self._observer:
            self._observer.on_error(message)
