import datetime

from heater_amd_controller.logics.hardware_manager import SensorData
from heater_amd_controller.models.protocol_config import ProtocolConfig
from heater_amd_controller.models.sequence import Sequence
from heater_amd_controller.utils.log_file import LogFile


class HCLogger:
    """Heat Cleaning ログ出力ロジック"""

    def __init__(self, log_file: LogFile, config: ProtocolConfig) -> None:
        self.log_file = log_file
        self.config = config

    def write_header(self, start_time: datetime.datetime, sequences: list[Sequence]) -> None:
        """ヘッダー情報の書き込み"""
        self.log_file.write("#Heat Cleaning monitor\n")
        self.log_file.write("\n")

        self.log_file.write(f"#Protocol:\t{self.config.name}\n")
        self.log_file.write("\n")

        self.log_file.write("#Measurement\n")
        self.log_file.write(f"#Number:\t{self.log_file.number}\n")
        self.log_file.write(f"#Date:\t{start_time.strftime('%Y/%m/%d')}\n")
        self.log_file.write(f"#Time:\t{start_time.strftime('%H:%M:%S')}\n")
        self.log_file.write("#ProgramVersion:\t1.1\n")
        # self.log_file.write(f"#Encode:\t{config.common.encode}\n")
        self.log_file.write("\n")

        # 設定値
        self.log_file.write("#Condition\n")
        if self.config.hc_enabled:
            self.log_file.write(f"#HC_CURRENT:\t{self.config.hc_current}[A]\n")
        if self.config.amd_enabled:
            self.log_file.write(f"#AMD_CURRENT:\t{self.config.amd_current}[A]\n")
        # シーケンス
        for index, sequence in enumerate(sequences):
            self.log_file.write(f"#Sequence{index + 1}:\t{sequence}\n")
        self.log_file.write("\n")

        # コメント
        self.log_file.write("#Comment\n")
        self.log_file.write(f"#{self.config.comment}\n")
        self.log_file.write("\n")

        # カラム名
        self.log_file.write("#Data\n")
        columns = [
            "Time[s]",
            "Temp(TC)[deg.C]",
            "Pressure(EXT)[Pa]",
            "Pressure(SIP)[Pa]",
        ]
        if self.config.hc_enabled:
            columns.extend(["Volt[V]", "Current[A]", "Power[W]"])
        if self.config.amd_enabled:
            columns.extend(["Volt(AMD)[V]", "Current(AMD)[A]", "Power(AMD)[W]"])

        self.log_file.write("\t".join(columns) + "\n")

    def write_record(self, elapsed_time: float, data: SensorData) -> None:
        """1行分のデータを書き込み"""
        log_items = [
            f"{elapsed_time:.1f}",
            f"{data.temperature:.1f}",
            f"{data.pressure_ext:.2E}",
            f"{data.pressure_sip:.2E}",
        ]

        if self.config.hc_enabled:
            log_items.extend(
                [f"{data.hc_voltage:.3f}", f"{data.hc_current:.3f}", f"{data.hc_power:.2f}"]
            )

        if self.config.amd_enabled:
            log_items.extend(
                [f"{data.amd_voltage:.3f}", f"{data.amd_current:.3f}", f"{data.amd_power:.2f}"]
            )

        self.log_file.write("\t".join(log_items) + "\n")
