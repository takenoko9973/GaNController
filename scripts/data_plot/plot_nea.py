import math
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Any, ClassVar

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


class LabelPriority(IntEnum):
    """ラベルの描画・配置の優先度 (数値が大きいほど優先)"""

    LOG_EVENT = 1
    POINT = 2
    SPAN = 3


@dataclass
class LabelItem:
    """描画するラベルの情報を保持するデータクラス"""

    event: str
    label: str
    color: str
    priority: LabelPriority
    target_x: float
    x_bounds: tuple[float, float] | None = None  # (min_x, max_x) 制限範囲
    y_hint: float | None = None

    # 決定された描画座標・配置情報
    final_x: float = 0.0
    final_y: float = 0.0
    ha: str = "center"
    va: str = "center"


class LabelLayoutEngine:
    """ラベルの最適な配置座標を計算するレイアウトエンジン"""

    # ==========================================================
    # 調整用定数パラメータ群
    # ==========================================================

    # Y軸の探索候補 (0.0=下端, 1.0=上端)。上端、下端、中央から順に探索する
    DEFAULT_Y_CANDIDATES: ClassVar[list[float]] = [
        0.95,
        0.85,
        0.75,
        0.65,
        0.5,
        0.05,
        0.15,
        0.25,
        0.35,
        1.0,
        0.0,
    ]

    # X軸方向のシフト候補 (テキスト幅に対する倍率。0.0はシフトなし)
    X_SHIFT_MULTIPLIERS: ClassVar[list[float]] = [0.0, -0.3, 0.3, -0.5, 0.5, -1.5, 1.5, -2.5, 2.5]

    # グラフ端の余白係数 (テキスト幅に対する倍率)
    EDGE_MARGIN_RATIO = 0.05

    # 解決したと見なすペナルティの閾値 (他ラベル・データ線との被りがない状態)
    ACCEPTABLE_PENALTY = 100.0

    # 各種ペナルティの重み
    PENALTY_OVERLAP_BOX = 10000.0  # 他のラベルと被る
    PENALTY_OVERLAP_VLINE = 8000.0  # 他のイベントの縦線と被る
    PENALTY_MAIN_DATA_CRITICAL = 8000.0  # メインデータと激しく被る (距離 < 0.1)
    PENALTY_MAIN_DATA_HIGH = 5000.0  # メインデータとやや被る (距離 < 0.2)
    PENALTY_MAIN_DATA_SLOPE = 10.0  # メインデータとの距離に応じた基本ペナルティ
    PENALTY_SUB_DATA_CRITICAL = 1000.0  # サブデータと激しく被る
    PENALTY_SUB_DATA_HIGH = 100.0  # サブデータとやや被る
    PENALTY_SUB_DATA_SLOPE = 5.0  # サブデータとの距離に応じた基本ペナルティ
    PENALTY_X_SHIFT = 50.0  # X軸方向の移動距離ペナルティ (大きいほど動きにくくなる)

    # ==========================================================

    def __init__(
        self,
        ax: plt.Axes,
        time_s: pd.Series,
        main_data_s: pd.Series,
        is_log_main: bool,
        pressure_data_s: pd.Series,
        is_log_press: bool,
        ylim_press: tuple[float, float],
        vertical_lines: list[float],
        fontsize: int,
        initial_obstacles: list[dict[str, float]] | None = None,
    ) -> None:
        self.ax = ax
        self.time_arr = time_s.to_numpy()
        self.main_data_arr = main_data_s.to_numpy()
        self.pressure_data_arr = pressure_data_s.to_numpy()

        self.is_log_main = is_log_main
        self.is_log_press = is_log_press

        self.ylim_press = ylim_press
        self.vertical_lines = vertical_lines
        self.fontsize = fontsize

        self.xlim = ax.get_xlim()
        self.ylim_main = ax.get_ylim()

        # 凡例などの初期障害物を登録
        self.placed_boxes: list[dict[str, float]] = initial_obstacles if initial_obstacles else []

    def _get_exact_text_dimensions(self, text: str) -> tuple[float, float]:
        """Matplotlibのレンダラを利用して、LaTeXを含むテキストの正確な描画サイズを計算する"""
        renderer = self.ax.figure.canvas.get_renderer()  # ty:ignore[possibly-missing-attribute]

        # ダミー描画を行ってBounding Boxを取得
        t = self.ax.text(0, 0, text, fontsize=self.fontsize)
        bbox_disp = t.get_window_extent(renderer=renderer)

        # X軸幅はデータ座標系に変換
        bbox_data = bbox_disp.transformed(self.ax.transData.inverted())
        width_data = bbox_data.width

        # Y軸高さは Axesの相対座標系 (0.0~1.0) に変換
        bbox_axes = bbox_disp.transformed(self.ax.transAxes.inverted())
        height_axes = bbox_axes.height

        t.remove()  # ダミー描画を削除
        return width_data, height_axes

    def _get_x_shift_candidates(self, item: LabelItem, text_width: float) -> list[float]:
        """元座標および左右への退避(シフト)候補を生成し、制限範囲内でフィルタリングする"""
        candidates = [item.target_x]

        for mult in self.X_SHIFT_MULTIPLIERS[1:]:
            test_x = item.target_x + (text_width * mult)
            if item.x_bounds and not (item.x_bounds[0] <= test_x <= item.x_bounds[1]):
                continue
            candidates.append(test_x)

        return candidates

    def _adjust_x_bounds(self, x: float, text_width: float) -> tuple[float, str]:
        """X座標がグラフ領域の端をはみ出さないように補正し、水平アライメントを返す"""
        margin = text_width * self.EDGE_MARGIN_RATIO
        if x - text_width / 2 < self.xlim[0]:
            return self.xlim[0] + margin, "left"
        if x + text_width / 2 > self.xlim[1]:
            return self.xlim[1] - margin, "right"
        return x, "center"

    def _get_horizontal_bounds(
        self, test_x: float, text_width: float, ha: str
    ) -> tuple[float, float]:
        """水平アライメントに基づく矩形の左右座標を返す"""
        if ha == "center":
            return test_x - text_width / 2, test_x + text_width / 2
        if ha == "left":
            return test_x, test_x + text_width
        return test_x - text_width, test_x

    def _get_y_bounds(self, ty: float, text_height: float) -> tuple[str, float, float]:
        """Y座標の高さに基づいて、垂直アライメントと矩形の上下座標を返す"""
        if ty > 0.6:  # noqa: PLR2004
            return "top", ty, ty - text_height
        if ty < 0.4:  # noqa: PLR2004
            return "bottom", ty + text_height, ty
        return "center", ty + text_height / 2, ty - text_height / 2

    def _calculate_data_penalty(
        self,
        left: float,
        right: float,
        top: float,
        bottom: float,
        data_arr: np.ndarray,
        ylim: tuple[float, float],
        is_log: bool,
        critical_weight: float,
        high_weight: float,
        slope_weight: float,
    ) -> float:
        """X軸の区間内のデータ線と、矩形枠との被りペナルティを計算する"""
        idx_start = np.searchsorted(self.time_arr, left)
        idx_end = np.searchsorted(self.time_arr, right, side="right")

        if idx_start >= len(self.time_arr):
            idx_start = len(self.time_arr) - 1

        if idx_start == idx_end:
            idx = (np.abs(self.time_arr - (left + right) / 2.0)).argmin()
            vals = np.array([data_arr[idx]])
        else:
            vals = data_arr[idx_start:idx_end]

        ymin, ymax = ylim
        if is_log:
            valid_mask = vals > 0
            if not np.any(valid_mask):
                return 0.0
            vals = vals[valid_mask]

            log_ymin = math.log10(ymin) if ymin > 0 else -15
            log_ymax = math.log10(ymax) if ymax > 0 else -14

            if log_ymax <= log_ymin:
                y_rels = np.full_like(vals, 0.5, dtype=float)
            else:
                y_rels = (np.log10(vals) - log_ymin) / (log_ymax - log_ymin)
        elif ymax <= ymin:
            y_rels = np.full_like(vals, 0.5, dtype=float)
        else:
            y_rels = (vals - ymin) / (ymax - ymin)

        # 矩形領域 [bottom, top] と各データポイントとのY方向の最短距離を計算
        dists = np.where(
            (y_rels >= bottom) & (y_rels <= top),
            0.0,
            np.where(y_rels > top, y_rels - top, bottom - y_rels),
        )

        min_dist = np.min(dists)

        if min_dist <= 0.0:
            return critical_weight  # データ線が矩形を完全に横切っている
        if min_dist < 0.05:  # noqa: PLR2004
            return high_weight  # データ線が矩形に極めて近い
        return (1.0 - min_dist) * slope_weight

    def _calculate_penalty(
        self,
        item: LabelItem,
        test_x: float,  # noqa: ARG002
        ty: float,  # noqa: ARG002
        dx: float,
        text_width: float,
        bbox: dict[str, float],
        check_vline: bool,
    ) -> float:
        """指定された座標・矩形におけるペナルティスコアを計算する"""
        penalty = 0.0

        # 1. 既存ラベルとの重なり判定
        for pbox in self.placed_boxes:
            if not (
                bbox["right"] < pbox["left"]
                or bbox["left"] > pbox["right"]
                or bbox["top"] < pbox["bottom"]
                or bbox["bottom"] > pbox["top"]
            ):
                penalty += self.PENALTY_OVERLAP_BOX
                break

        # 2. 縦線(イベントライン)との重なり判定 (x軸方向にシフトしていなければ考慮しない)
        if check_vline:
            for vline_x in self.vertical_lines:
                if bbox["left"] < vline_x < bbox["right"]:
                    if abs(vline_x - item.target_x) < 1e-6 and abs(dx) < 1e-6:  # noqa: PLR2004
                        continue
                    penalty += self.PENALTY_OVERLAP_VLINE

        # 3. メインデータ線 (区間全体) との被り判定
        penalty += self._calculate_data_penalty(
            bbox["left"],
            bbox["right"],
            bbox["top"],
            bbox["bottom"],
            self.main_data_arr,
            self.ylim_main,
            self.is_log_main,
            self.PENALTY_MAIN_DATA_CRITICAL,
            self.PENALTY_MAIN_DATA_HIGH,
            self.PENALTY_MAIN_DATA_SLOPE,
        )

        # 4. サブデータ線 (区間全体) との被り判定
        penalty += self._calculate_data_penalty(
            bbox["left"],
            bbox["right"],
            bbox["top"],
            bbox["bottom"],
            self.pressure_data_arr,
            self.ylim_press,
            self.is_log_press,
            self.PENALTY_SUB_DATA_CRITICAL,
            self.PENALTY_SUB_DATA_HIGH,
            self.PENALTY_SUB_DATA_SLOPE,
        )

        # 5. 元のX座標からの移動距離に対するペナルティ
        penalty += (abs(dx) / text_width) * self.PENALTY_X_SHIFT

        return penalty

    def compute_layout(self, labels: list[LabelItem]) -> None:  # noqa: C901
        """ルールに基づき、各ラベルの最適な描画座標を決定する"""
        labels.sort(key=lambda x: (-x.priority.value, x.target_x))

        for item in labels:
            text_width, text_height = self._get_exact_text_dimensions(item.label)
            y_candidates = [item.y_hint] if item.y_hint is not None else self.DEFAULT_Y_CANDIDATES

            best_penalty = float("inf")
            best_pos = None
            solved = False

            # フェーズ1: Y軸のみの移動 (イベントラインとの被りを無視)
            test_x, ha = self._adjust_x_bounds(item.target_x, text_width)
            left, right = self._get_horizontal_bounds(test_x, text_width, ha)

            for ty in y_candidates:
                va, top, bottom = self._get_y_bounds(ty, text_height)
                bbox = {"left": left, "right": right, "bottom": bottom, "top": top}

                penalty = self._calculate_penalty(
                    item, test_x, ty, 0.0, text_width, bbox, check_vline=False
                )

                if penalty < best_penalty:
                    best_penalty = penalty
                    best_pos = (test_x, ty, ha, va, bbox)

                if penalty < self.ACCEPTABLE_PENALTY:
                    solved = True
                    break

            # フェーズ2: Y軸の移動で解決しない場合、X軸の移動を試行 (イベントラインとの被りを考慮)
            if not solved:
                x_shifts = self._get_x_shift_candidates(item, text_width)
                for test_x_raw in x_shifts:
                    test_x, ha = self._adjust_x_bounds(test_x_raw, text_width)
                    left, right = self._get_horizontal_bounds(test_x, text_width, ha)

                    for ty in y_candidates:
                        va, top, bottom = self._get_y_bounds(ty, text_height)
                        bbox = {"left": left, "right": right, "bottom": bottom, "top": top}

                        dx = test_x - item.target_x
                        penalty = self._calculate_penalty(
                            item, test_x, ty, dx, text_width, bbox, check_vline=True
                        )

                        if penalty < best_penalty:
                            best_penalty = penalty
                            best_pos = (test_x, ty, ha, va, bbox)

                        if penalty < self.ACCEPTABLE_PENALTY:
                            solved = True
                            break
                    if solved:
                        break

            # フェーズ3: 決定された座標(最良の妥協点)の保存
            if best_pos:
                test_x, ty, ha, va, bbox = best_pos
                self.placed_boxes.append(bbox)
                item.final_x = test_x
                item.final_y = ty
                item.ha = ha
                item.va = va


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
    COLOR_EVENT_DEFAULT = "green"
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
        self._draw_events(builder, time_m, metric_data, is_log_scale=(scale == ScaleEnum.LOG))

        builder.ax1.yaxis.set_major_formatter(FuncFormatter(format_sci_mathtext))

        fig = builder.finalize()
        self._save_figure(fig, filename)
        plt.close(fig)

    # ==========================================
    # イベント・ラベル描画ロジック群
    # ==========================================
    def _generate_auto_cs_spans(self) -> list[dict[str, Any]]:
        """AMDの電力が正(>0)の区間を自動計算し、spanのリストとして返す"""
        v_col = "AMD_V[V]" if "AMD_V[V]" in self.log_df.columns else "Volt(AMD)[V]"
        i_col = "AMD_I[A]" if "AMD_I[A]" in self.log_df.columns else "Current(AMD)[A]"

        if v_col not in self.log_df.columns or i_col not in self.log_df.columns:
            return []

        # v_data = pd.to_numeric(self.log_df[v_col], errors="coerce").fillna(0)
        # i_data = pd.to_numeric(self.log_df[i_col], errors="coerce").fillna(0)
        # time_data = pd.to_numeric(self.log_df["Time[s]"], errors="coerce")

        v_data = self.log_df[v_col]
        i_data = self.log_df[i_col]
        time_data = self.log_df["Time[s]"]

        power = v_data * i_data
        is_cs = power > 1  # 1W以上出力していたら、Csとみなす
        diff = is_cs.astype(int).diff()

        starts = time_data[diff == 1].tolist()
        ends = time_data[diff == -1].tolist()

        if not is_cs.empty and is_cs.iloc[0]:
            starts.insert(0, time_data.iloc[0])
        if not is_cs.empty and is_cs.iloc[-1]:
            ends.append(time_data.iloc[-1])

        auto_spans = []
        for start_s, end_s in zip(starts, ends, strict=True):
            if end_s - start_s > 1.0:
                auto_spans.append({"event": "Cs", "start": start_s, "end": end_s})

        if auto_spans:
            longest_span = max(auto_spans, key=lambda s: s["end"] - s["start"])
            longest_span.update({"label": "Cs"})

        return auto_spans

    # === 各イベントのラベルを抽出 ===

    def _extract_span_labels(self, ax: plt.Axes) -> list[LabelItem]:
        items = []
        all_spans = self.nea_config.spans + self._generate_auto_cs_spans()
        for span in all_spans:
            event = span["event"]
            color = self.nea_config.colors.get(event, self.COLOR_EVENT_DEFAULT)
            start_m, end_m = span["start"] / 60, span["end"] / 60
            ax.axvspan(start_m, end_m, color=color, alpha=self.ALPHA_EVENT_SPAN)

            if "label" in span:
                dx_m = span.get("dx", 0.0) / 60
                items.append(
                    LabelItem(
                        event=event,
                        label=span["label"],
                        color=color,
                        priority=LabelPriority.SPAN,
                        target_x=((start_m + end_m) / 2.0) + dx_m,
                        x_bounds=(start_m, end_m),  # Spanの描画範囲を制限として渡す
                        y_hint=span.get("y"),
                    )
                )
        return items

    def _extract_point_labels(self, ax: plt.Axes) -> list[LabelItem]:
        items = []
        for pt in self.nea_config.points:
            event = pt["event"]
            color = self.nea_config.colors.get(event, self.COLOR_EVENT_DEFAULT)
            time_m = pt["time"] / 60
            dx_m = pt.get("dx", 0.0) / 60
            ax.axvline(time_m, color=color, linestyle=self.STYLE_EVENT_POINT, alpha=0.8)

            if "label" in pt:
                items.append(
                    LabelItem(
                        event=event,
                        label=pt["label"],
                        color=color,
                        priority=LabelPriority.POINT,
                        target_x=time_m + dx_m,
                        y_hint=pt.get("y"),
                    )
                )
        return items

    def _extract_log_event_labels(self, ax: plt.Axes) -> list[LabelItem]:
        items = []
        if "Event" not in self.log_df.columns:
            return items

        rows = self.log_df.dropna(subset=["Event"])
        for _, row in rows[rows["Event"].astype(str).str.strip() != ""].iterrows():
            event_label = str(row["Event"]).strip()
            time_m = row["Time[s]"] / 60

            color = self.COLOR_EVENT_DEFAULT
            for key, c in self.nea_config.colors.items():
                if key in event_label:
                    color = c
                    break

            ax.axvline(time_m, color=color, linestyle=self.STYLE_EVENT_POINT, alpha=0.8)
            items.append(
                LabelItem(
                    event=event_label,
                    label=event_label,
                    color=color,
                    priority=LabelPriority.LOG_EVENT,
                    target_x=time_m,
                )
            )
        return items

    def _draw_events(
        self, builder: GraphBuilder, time_m: pd.Series, metric_data: pd.Series, is_log_scale: bool
    ) -> None:
        ax = builder.ax1

        labels_to_draw = (
            self._extract_span_labels(ax)
            + self._extract_point_labels(ax)
            + self._extract_log_event_labels(ax)
        )

        if not labels_to_draw:
            return

        # 縦線の位置を収集
        vertical_lines = [pt["time"] / 60 for pt in self.nea_config.points]

        if "Event" in self.log_df.columns:
            rows = self.log_df.dropna(subset=["Event"])
            for _, row in rows[rows["Event"].astype(str).str.strip() != ""].iterrows():
                vertical_lines.append(row["Time[s]"] / 60)

        all_spans = self.nea_config.spans + self._generate_auto_cs_spans()
        for span in all_spans:
            vertical_lines.extend([span["start"] / 60, span["end"] / 60])

        vertical_lines = list(set(vertical_lines))

        # 凡例の事前レンダリングと障害物(initial_obstacles)の生成
        initial_obstacles = []
        if builder.labels:
            # 仮描画して正確な座標を取得
            leg = ax.legend(
                builder.lines, builder.labels, loc="best", fontsize=builder.style.legend_fontsize
            )
            builder.fig.canvas.draw()
            bbox_disp = leg.get_window_extent()

            # ディスプレイ座標を判定用のデータ座標/Axes相対座標に変換
            bbox_axes = bbox_disp.transformed(ax.transAxes.inverted())
            bbox_data = bbox_disp.transformed(ax.transData.inverted())

            initial_obstacles.append(
                {
                    "left": bbox_data.x0,
                    "right": bbox_data.x1,
                    "bottom": bbox_axes.y0,
                    "top": bbox_axes.y1,
                }
            )
            leg.remove()  # 仮描画を削除 (finalize時に正規に描画される)

        engine = LabelLayoutEngine(
            ax=ax,
            time_s=time_m,
            main_data_s=metric_data,
            is_log_main=is_log_scale,
            pressure_data_s=self.log_df["Pressure(EXT)[Pa]"],
            is_log_press=True,
            ylim_press=self.YLIM_PRESSURE,
            vertical_lines=vertical_lines,
            fontsize=self.FONTSIZE_EVENT_LABEL,
            initial_obstacles=initial_obstacles,
        )
        engine.compute_layout(labels_to_draw)

        for item in labels_to_draw:
            ax.text(
                item.final_x,
                item.final_y,
                item.label,
                color=item.color,
                fontsize=self.FONTSIZE_EVENT_LABEL,
                ha=item.ha,
                va=item.va,
                transform=ax.get_xaxis_transform(),
            )
