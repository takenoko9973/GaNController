import datetime
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from gan_controller.common.io.log_manager import LogFile
from gan_controller.features.heat_cleaning.domain.models import HCExperimentResult
from gan_controller.features.heat_cleaning.schemas.config import ProtocolConfig


@dataclass
class LogColumn:
    """1つのログ列を定義する構造体"""

    header: str  # ヘッダー名
    fmt: str  # フォーマット文字列 (例: "{:.4E}")

    # 値取り出し形式 (引数: Result, Event文字列)
    extractor: Callable[[HCExperimentResult], Any]


class HCLogRecorder:
    """NEA実験データの記録を担当するクラス (Recorder)"""

    def __init__(self, log_file: LogFile, config: ProtocolConfig) -> None:
        self.file = log_file
        self.config = config

        # ログデータ項目定義
        self.columns: list[LogColumn] = [
            LogColumn("Time[s]", "{:.1f}", lambda r: r.total_timestamp.base_value),
            LogColumn("Temp(TC)[deg.C]", "{:.1f}", lambda r: r.case_temperature.base_value),
            # Pressure
            LogColumn("Pressure(EXT)[Pa]", "{:.2E}", lambda r: r.ext_pressure.base_value),
            LogColumn("Pressure(SIP)[Pa]", "{:.2E}", lambda r: r.sip_pressure.base_value),
        ]
        # HC
        if self.config.condition.hc_enabled:
            self.columns.extend(
                [
                    LogColumn(
                        "Volt[V]",
                        "{:.2f}",
                        lambda r: r.hc_electricity.voltage.base_value,
                    ),
                    LogColumn(
                        "Current[A]",
                        "{:.2f}",
                        lambda r: r.hc_electricity.current.base_value,
                    ),
                    LogColumn(
                        "Power[W]",
                        "{:.2f}",
                        lambda r: r.hc_electricity.power.base_value,
                    ),
                ]
            )
        # AMD
        if self.config.condition.amd_enabled:
            self.columns.extend(
                [
                    LogColumn(
                        "Volt(AMD)[V]",
                        "{:.2f}",
                        lambda r: r.amd_electricity.voltage.base_value,
                    ),
                    LogColumn(
                        "Current(AMD)[A]",
                        "{:.2f}",
                        lambda r: r.amd_electricity.current.base_value,
                    ),
                    LogColumn(
                        "Power(AMD)[W]",
                        "{:.2f}",
                        lambda r: r.amd_electricity.power.base_value,
                    ),
                ]
            )

        self.columns.append(LogColumn("Event", "{:}", lambda _: ""))

    def record_header(self, start_time: datetime.datetime) -> None:
        """ヘッダー情報を記録"""
        lf = self.file

        # パラメータの取得 (Quantity -> float/int)
        hc_enabled = self.config.condition.hc_enabled
        hc_current = self.config.condition.hc_current.base_value
        amd_enabled = self.config.condition.amd_enabled
        amd_current = self.config.condition.amd_current.base_value

        comment = self.config.log.comment

        # === Header Writing (Identical to reference) ===
        lf.write("#Heat Cleaning monitor\n")
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
        if hc_enabled:
            lf.write(f"#HC_CURRENT:\t{hc_current}[A]\n")
        if amd_enabled:
            lf.write(f"#AMD_CURRENT:\t{amd_current}[A]\n")
        # シーケンス
        for index, sequence in enumerate(self.config.get_sequences()):
            lf.write(f"#Sequence{index + 1}:\t{sequence}\n")
        lf.write("\n")

        lf.write("#Comment\n")
        lf.write(f"#{comment}\n")
        lf.write("\n")

        lf.write("#Data\n")
        header_row = "\t".join([c.header for c in self.columns])
        lf.write(header_row + "\n")

    def record_data(self, result: HCExperimentResult) -> None:
        """測定結果を1行記録"""
        row_data = []

        # 定義されたカラム順にデータを抽出・フォーマット
        for col in self.columns:
            # extractor関数を実行して値を取得
            raw_val = col.extractor(result)
            # 指定された書式で文字列化
            formatted_val = col.fmt.format(raw_val)
            row_data.append(formatted_val)

        # タブ区切りで書き込み
        self.file.write("\t".join(row_data) + "\n")
