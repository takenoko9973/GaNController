import datetime
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from gan_controller.common.services.log_manager import LogFile
from gan_controller.features.nea_activation.dtos.nea_params import (
    NEAConditionParams,
    NEAControlParams,
)
from gan_controller.features.nea_activation.dtos.nea_result import NEAActivationResult


@dataclass
class LogColumn:
    """1つのログ列を定義する構造体"""

    header: str  # ヘッダー名
    fmt: str  # フォーマット文字列 (例: "{:.4E}")

    # 値取り出し形式 (引数: Result, Event文字列)
    extractor: Callable[[NEAActivationResult, str], Any]


class NEARecorder:
    """NEA実験データの記録を担当するクラス (Recorder)"""

    def __init__(self, log_file: LogFile) -> None:
        self.file = log_file

        self.columns: list[LogColumn] = [
            LogColumn("Time[s]", "{:.1f}", lambda r, _: r.timestamp),
            # Laser power
            LogColumn("LP(SV)[W]", "{:.4E}", lambda r, _: r.laser_power_sv.si_value),
            LogColumn("LP(PV)[W]", "{:.4E}", lambda r, _: r.laser_power_pv.si_value),
            # Quantum efficiency
            LogColumn("QE[%]", "{:.4E}", lambda r, _: r.quantum_efficiency.value_as("%")),
            # Photocurrent
            LogColumn("PC[A]", "{:.4E}", lambda r, _: r.photocurrent.si_value),
            # Pressure
            LogColumn("Pressure(EXT)[Pa]", "{:.4E}", lambda r, _: r.ext_pressure.si_value),
            LogColumn("Pressure(SIP)[Pa]", "{:.4E}", lambda r, _: r.sip_pressure.si_value),
            # Bright photocurrent
            LogColumn("BPc[A]", "{:.4E}", lambda r, _: r.bright_photocurrent.si_value),
            # Dark photocurrent
            LogColumn("DPc[A]", "{:.4E}", lambda r, _: r.dark_photocurrent.si_value),
            # Extraction voltage
            LogColumn("ExVolt[V]", "{:.1f}", lambda r, _: r.extraction_voltage.si_value),
            # AMD power supply
            LogColumn("AMD_V[V]", "{:.3f}", lambda r, _: r.amd_electricity.voltage.si_value),
            LogColumn("AMD_I[A]", "{:.3f}", lambda r, _: r.amd_electricity.current.si_value),
            # イベント文字列
            LogColumn("Event", "{}", lambda _, e: e),
        ]

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
        stabilization_time = condition.stabilization_time.si_value
        integrated_count = int(condition.integration_count.si_value)
        interval = condition.integration_interval.si_value

        # === Header Writing (Identical to reference) ===
        lf.write("#NEA activation monitor\n")
        lf.write("\n")
        lf.write(f"#Protocol:\t{lf.protocol}\n")
        lf.write("\n")

        lf.write("#Measurement\n")
        lf.write(f"#Number:\t{lf.number}\n")
        lf.write(f"#Date:\t{start_time.strftime('%Y/%m/%d')}\n")
        lf.write(f"#Time:\t{start_time.strftime('%H:%M:%S')}\n")
        lf.write(f"#Encode:\t{lf.encoding}\n")
        lf.write("\n")

        lf.write("#Condition\n")
        lf.write(f"#Wavelength:\t{wavelength:d}[nm]\n")
        lf.write(f"#InitLaserPower(SV):\t{laser_power_sv:d}[mW]\n")

        lf.write(f"#StabilizationTime:\t{stabilization_time:.1f}[s]\n")
        lf.write(f"#IntegratedTimes:\t{integrated_count:d}[-]\n")
        lf.write(f"#IntervalTime:\t{interval:.1f}[s]\n")
        lf.write("\n")

        lf.write("#Comment\n")
        lf.write(f"#{comment}\n")
        lf.write("\n")

        lf.write("#Data\n")
        header_row = "\t".join([c.header for c in self.columns])
        lf.write(header_row + "\n")

    def record_data(self, result: NEAActivationResult, event: str = "") -> None:
        """測定結果を1行記録"""
        row_data = []

        # 定義されたカラム順にデータを抽出・フォーマット
        for col in self.columns:
            # extractor関数を実行して値を取得
            raw_val = col.extractor(result, event)
            # 指定された書式で文字列化
            formatted_val = col.fmt.format(raw_val)
            row_data.append(formatted_val)

        # タブ区切りで書き込み
        self.file.write("\t".join(row_data) + "\n")
