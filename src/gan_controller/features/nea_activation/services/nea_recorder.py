import datetime
from typing import ClassVar

from gan_controller.common.services.log_manager import LogFile
from gan_controller.features.nea_activation.dtos.nea_params import (
    NEAConditionParams,
    NEAControlParams,
)
from gan_controller.features.nea_activation.dtos.nea_result import NEAActivationResult


class NEARecorder:
    """NEA実験データの記録を担当するクラス (Recorder)"""

    COLUMNS: ClassVar[list[str]] = [
        "Time[s]",
        "LP(PV)[W]",  # Laser power (PV)
        "QE[%]",  # Quantum efficiency
        "PC[A]",  # Photocurrent
        "Pressure(EXT)[Pa]",
        "Pressure(SIP)[Pa]",
        "BPc[A]",  # Bright photocurrent
        "DPc[A]",  # Dark photocurrent
        "Event",
    ]

    def __init__(self, log_file: LogFile) -> None:
        self.file = log_file

    def record_header(
        self,
        start_time: datetime.datetime,
        condition: NEAConditionParams,
        init_control: NEAControlParams,
        comment: str,
    ) -> None:
        """ヘッダー情報を記録"""
        lf = self.file

        # パラメータの取得 (Quantity -> float/int)
        wavelength = int(condition.laser_wavelength.value_as("n"))
        laser_power_sv = int(init_control.laser_power_sv.value_as("m"))
        stabilization_time = condition.stabilization_time.value_as()
        integrated_count = int(condition.integration_count.value_as(""))
        interval = condition.integration_interval.value_as("")

        # NOTE: NEAActivationParamsにHV設定がないため、リファレンスのデフォルト値(100)を使用
        # もし将来的に設定可能にするなら params.hv などを参照する
        extraction_voltage = 100

        # === Header Writing (Identical to reference) ===
        lf.write("#NEA activation monitor\n\n")
        lf.write(f"#Protocol:\t{lf.protocol}\n\n")

        lf.write("#Measurement\n")
        lf.write(f"#Number:\t{lf.number}\n")
        lf.write(f"#Date:\t{start_time.strftime('%Y/%m/%d')}\n")
        lf.write(f"#Time:\t{start_time.strftime('%H:%M:%S')}\n")
        lf.write(f"#Encode:\t{lf.encoding}\n")

        lf.write("#Condition\n")
        lf.write(f"#Wavelength:\t{wavelength:d}[nm]\n")
        lf.write(f"#LaserPower(SV):\t{laser_power_sv:d}[mW]\n")

        lf.write(f"#StabilizationTime:\t{stabilization_time:.1f}[s]\n")
        lf.write(f"#IntegratedTimes:\t{integrated_count:d}[-]\n")
        lf.write(f"#IntervalTime:\t{interval:.1f}[s]\n")
        lf.write(f"#ExtractionVoltage:\t{extraction_voltage:d}[V]\n\n")

        lf.write("#Comment\n")
        lf.write(f"#{comment}\n\n")

        lf.write("#Data\n")
        lf.write("\t".join(self.COLUMNS) + "\n")

    def record_data(self, result: NEAActivationResult, event: str = "") -> None:
        """測定結果を1行記録"""
        cols = [
            f"{result.timestamp:.1f}",
            f"{result.laser_power_pv.value_as():.4e}",
            f"{result.photocurrent.value_as():.4e}",
            f"{result.quantum_efficiency.value_as('%'):.4e}",
            f"{result.ext_pressure.value_as():.4e}",
            f"{result.bright_pc.value_as():.4e}",
            f"{result.dark_pc.value_as():.4e}",
            f"{event}",  # Event
        ]
        self.file.write("\t".join(cols) + "\n")
