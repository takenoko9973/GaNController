import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter

from gan_controller.infrastructure.persistence.log_manager import LogFile
from scripts.data_plot.base_plotter import BasePlotter
from scripts.data_plot.plot_util import AxisSide, GraphBuilder, PlotInfo, PlotStyleConfig, ScaleEnum


@dataclass
class NEAPlotConfig:
    colors: dict[str, str]
    spans: list[dict[str, Any]]
    points: list[dict[str, Any]]


def format_sci_mathtext(x: float, _: int) -> str:
    """Y軸の数値を LaTeX形式の指数表記 (例: 1.2 x 10^3) に変換するヘルパー関数"""
    if x == 0:
        return r"$0$"
    exp = int(np.floor(np.log10(abs(x))))
    mant = x / 10**exp
    return rf"${mant:.1f} \times 10^{{{exp}}}$"


class NEAPlotter(BasePlotter):
    # 光電流 (PC) の設定
    COLOR_PC = "green"
    STYLE_PC = "o"

    # 量子効率 (QE) の設定
    COLOR_QE = "green"
    STYLE_QE = "o"

    # 圧力の設定 (PC/QE 共通)
    COLOR_PRESSURE = "black"
    YLIM_PRESSURE = (1e-9, 1e-5)

    # イベント領域・ラベルの設定
    COLOR_EVENT_DEFAULT = "gray"  # TOMLで色が指定されていない場合のデフォルト色
    ALPHA_EVENT_SPAN = 0.1  # 塗りつぶしの濃さ
    STYLE_EVENT_POINT = ":"  # 瞬間イベントの線のスタイル
    FONTSIZE_EVENT_LABEL = 16  # ラベルの文字サイズ

    def __init__(
        self,
        logfile: LogFile,
        save_dir: Path,
        nea_config: NEAPlotConfig,
        overwrite: bool = False,
        style_config: PlotStyleConfig | None = None,
    ) -> None:
        super().__init__(logfile, save_dir, overwrite)
        self.nea_config = nea_config
        self.style_config = style_config

    @property
    def time_axis(self) -> pd.Series:
        return self.log_df["Time[s]"] / 60  # minute

    def plot(self) -> None:
        if not self.extract_data():
            return

        self.plot_pc()
        self.plot_qe()

    # ==========================================
    # グラフごとの呼び出し口
    # ==========================================
    def plot_pc(self) -> None:
        """Photocurrent (PC) のプロット"""
        self._plot_metric(
            col_name="PC[A]",
            suffix="pc",
            ylabel="Photocurrent (A)",
            scale=ScaleEnum.LINEAR,
            metric_color=self.COLOR_PC,
            metric_style=self.STYLE_PC,
        )

    def plot_qe(self) -> None:
        """Quantum Efficiency (QE) のプロット"""
        self._plot_metric(
            col_name="QE[%]",
            suffix="qe",
            ylabel="Quantum Efficiency (%)",
            scale=ScaleEnum.LINEAR,
            metric_color=self.COLOR_QE,
            metric_style=self.STYLE_QE,
        )

    def _plot_metric(
        self,
        col_name: str,
        suffix: str,
        ylabel: str,
        scale: ScaleEnum,
        metric_color: str,
        metric_style: str,
    ) -> None:
        """指定された列 (PC or QE) のデータを抽出し、共通のフォーマットで描画する"""
        filename = f"{self.logfile.path.stem}_{suffix}.svg"
        if self._should_skip(filename):
            return

        df = self.log_df[self.log_df[col_name] > 0]
        if df.empty:
            print(f"[SKIP] {self.logfile.path.name}: {col_name} のデータが存在しません。")
            return

        time_m = df["Time[s]"] / 60
        metric_data = df[col_name]
        pressure_data = df["Pressure(EXT)[Pa]"]

        plot_info_list = [
            PlotInfo(
                metric_data,
                AxisSide.LEFT,
                ylabel.split(" ")[0],
                metric_color,
                style=metric_style,
                scale=scale,
            ),
            PlotInfo(
                pressure_data,
                AxisSide.RIGHT,
                "Pressure(EXT)",
                self.COLOR_PRESSURE,
                scale=ScaleEnum.LOG,
            ),
        ]

        builder = GraphBuilder(style_config=self.style_config)
        builder.set_title(self.logfile.path.stem)
        builder.set_labels("Time (min)", ylabel, "Pressure (Pa)")
        builder.set_xlim(time_m.min(), time_m.max())
        builder.set_base_ylim(AxisSide.RIGHT, *self.YLIM_PRESSURE)

        for plot_info in plot_info_list:
            builder.add_plot(time_m, plot_info)
            builder.set_yscale(plot_info.axis, plot_info.scale.value)

        # 軸の範囲を確定させてからイベントを描画
        builder.adjust_axes_limits()
        self._draw_events(builder.ax1, time_m, metric_data, is_log_scale=(scale == ScaleEnum.LOG))

        builder.ax1.yaxis.set_major_formatter(FuncFormatter(format_sci_mathtext))

        fig = builder.finalize()
        self._save_figure(fig, filename)
        plt.close(fig)

    # ==========================================
    # イベント描画に関するロジック群
    # ==========================================
    def _calculate_relative_y(
        self,
        target_x: float,
        time_m: pd.Series,
        metric_data: pd.Series,
        ymin: float,
        ymax: float,
        is_log_scale: bool,
    ) -> float | None:
        """指定したX座標におけるデータ線の相対的な高さ (0.0〜1.0) を計算する"""
        idx = (time_m - target_x).abs().idxmin()
        if pd.isna(idx):
            return None
        val = metric_data.loc[idx]

        if is_log_scale:
            if val <= 0 or ymin <= 0:
                return 0.5

            return (math.log10(val) - math.log10(ymin)) / (math.log10(ymax) - math.log10(ymin))

        return (val - ymin) / (ymax - ymin)

    def _generate_auto_cs_spans(self) -> list[dict[str, Any]]:
        """AMDの電力が正(>0)の区間を自動計算し、spanのリストとして返す"""
        # ログの仕様に合わせて列名を柔軟に取得
        v_col = "AMD_V[V]" if "AMD_V[V]" in self.log_df.columns else "Volt(AMD)[V]"
        i_col = "AMD_I[A]" if "AMD_I[A]" in self.log_df.columns else "Current(AMD)[A]"

        # 対象の列が存在しない場合はスキップ
        if v_col not in self.log_df.columns or i_col not in self.log_df.columns:
            return []

        # 計算用のデータを取得 (欠損値は 0 として扱う)
        v_data = pd.to_numeric(self.log_df[v_col], errors="coerce").fillna(0)
        i_data = pd.to_numeric(self.log_df[i_col], errors="coerce").fillna(0)
        time_data = pd.to_numeric(self.log_df["Time[s]"], errors="coerce")

        # 電力が > 0 の判定 (True/Falseのシリーズ)
        power = v_data * i_data
        is_cs = power > 0

        # 前の行との差分(diff)を取ることで、状態が切り替わった境界を検出
        diff = is_cs.astype(int).diff()

        starts = time_data[diff == 1].tolist()  # False -> True になった瞬間
        ends = time_data[diff == -1].tolist()  # True -> False になった瞬間

        # 最初からTrueだった場合、最初の時間を開始点にする
        if not is_cs.empty and is_cs.iloc[0]:
            starts.insert(0, time_data.iloc[0])

        # 最後までTrueだった場合、最後の時間を終了点にする
        if not is_cs.empty and is_cs.iloc[-1]:
            ends.append(time_data.iloc[-1])

        # 抽出した時間からSpanオブジェクト(辞書)を生成
        auto_spans = []
        for start_s, end_s in zip(starts, ends, strict=True):
            # 一瞬のノイズ(1秒未満など)は除外する
            if end_s - start_s > 1.0:
                auto_spans.append(
                    {
                        "event": "Cs",
                        "start": start_s,
                        "end": end_s,
                    }
                )

        if auto_spans:
            longest_span = max(auto_spans, key=lambda s: s["end"] - s["start"])
            # その最長の区間にのみラベルを付与する
            longest_span["label"] = "Cs"

        return auto_spans

    def _draw_spans(
        self, ax: plt.Axes, time_m: pd.Series, metric_data: pd.Series, is_log_scale: bool
    ) -> None:
        """区間のハイライトと、データ被りを回避する自動ラベル配置を描画する"""
        ymin, ymax = ax.get_ylim()
        last_label_end_x = {"top": -999.0, "bottom": -999.0}
        current_y_level = {"top": 0.95, "bottom": 0.05}

        all_spans = self.nea_config.spans + self._generate_auto_cs_spans()

        for span in all_spans:
            event = span["event"]
            color = self.nea_config.colors.get(event, self.COLOR_EVENT_DEFAULT)
            start_m = span["start"] / 60
            end_m = span["end"] / 60

            # 背景の塗りつぶし
            ax.axvspan(start_m, end_m, color=color, alpha=self.ALPHA_EVENT_SPAN)

            if "label" not in span:
                continue

            dx_m = span.get("dx", 0.0) / 60
            center_x = ((start_m + end_m) / 2.0) + dx_m

            if "y" in span:
                # TOMLで指定されている場合は絶対優先
                label_y = span["y"]
                va = "top" if label_y > 0.5 else "bottom"  # noqa: PLR2004
            else:
                # 自動位置計算
                rel_y = self._calculate_relative_y(
                    center_x, time_m, metric_data, ymin, ymax, is_log_scale
                )

                if rel_y is not None and rel_y > 0.6:  # noqa: PLR2004
                    pos_key, base_y, offset, va = "bottom", 0.05, 0.10, "bottom"
                else:
                    pos_key, base_y, offset, va = "top", 0.95, -0.10, "top"

                if (center_x - last_label_end_x[pos_key]) < 10.0:  # noqa: PLR2004
                    current_y_level[pos_key] = (
                        base_y + offset if current_y_level[pos_key] == base_y else base_y
                    )
                else:
                    current_y_level[pos_key] = base_y

                label_y = current_y_level[pos_key]
                last_label_end_x[pos_key] = center_x + len(span["label"]) * 0.5

            ax.text(
                center_x,
                label_y,
                span["label"],
                color=color,
                fontsize=self.FONTSIZE_EVENT_LABEL,
                ha="center",
                va=va,
                transform=ax.get_xaxis_transform(),
            )

    def _draw_points(self, ax: plt.Axes) -> None:
        """瞬間的なイベントの点線とラベルを描画する"""
        for pt in self.nea_config.points:
            event = pt["event"]
            color = self.nea_config.colors.get(event, self.COLOR_EVENT_DEFAULT)
            time_m = pt["time"] / 60
            dx_m = pt.get("dx", 0.0) / 60

            ax.axvline(time_m, color=color, linestyle=self.STYLE_EVENT_POINT, alpha=0.8)

            if "label" in pt:
                label_y = pt.get("y", 0.95)
                va = "top" if label_y > 0.5 else "bottom"  # noqa: PLR2004
                ax.text(
                    time_m + dx_m,
                    label_y,
                    pt["label"],
                    color=color,
                    fontsize=self.FONTSIZE_EVENT_LABEL,
                    ha="center",
                    va=va,
                    transform=ax.get_xaxis_transform(),
                )

    def _draw_log_events(
        self, ax: plt.Axes, time_m: pd.Series, metric_data: pd.Series, is_log_scale: bool
    ) -> None:
        """ログファイル内の Event 列に記録されているイベントを自動で描画する"""
        # "Event" 列が存在しない場合は何もしない
        if "Event" not in self.log_df.columns:
            return

        ymin, ymax = ax.get_ylim()

        # Event列にデータが入っている（NaNでない）行を抽出
        event_rows = self.log_df.dropna(subset=["Event"])
        # さらに、空文字や空白だけの行を除外
        event_rows = event_rows[event_rows["Event"].astype(str).str.strip() != ""]

        for _, row in event_rows.iterrows():
            event_time_m = row["Time[s]"] / 60
            event_label = str(row["Event"]).strip()

            # 登録されている色の中から、イベント名にマッチするものがあれば適用、なければデフォルト色
            color = self.COLOR_EVENT_DEFAULT
            for key_name, registered_color in self.nea_config.colors.items():
                if key_name in event_label:
                    color = registered_color
                    break

            # 縦線の描画
            ax.axvline(event_time_m, color=color, linestyle=self.STYLE_EVENT_POINT, alpha=0.8)

            # ラベルの被り回避ロジック（_draw_spansと同様の判定）
            rel_y = self._calculate_relative_y(
                event_time_m, time_m, metric_data, ymin, ymax, is_log_scale
            )

            if rel_y is not None and rel_y > 0.6:  # noqa: PLR2004
                label_y = 0.05
                va = "bottom"
            else:
                label_y = 0.95
                va = "top"

            ax.text(
                event_time_m,
                label_y,
                event_label,
                color=color,
                fontsize=self.FONTSIZE_EVENT_LABEL,
                ha="center",
                va=va,
                transform=ax.get_xaxis_transform(),
            )

    def _draw_events(
        self, ax: plt.Axes, time_m: pd.Series, metric_data: pd.Series, is_log_scale: bool
    ) -> None:
        """SpansとPointsの描画処理をまとめる"""
        self._draw_spans(ax, time_m, metric_data, is_log_scale)
        self._draw_points(ax)
        self._draw_log_events(ax, time_m, metric_data, is_log_scale)
