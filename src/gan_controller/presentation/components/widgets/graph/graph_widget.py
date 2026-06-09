from typing import Literal

import numpy as np
from matplotlib.axes import Axes
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.ticker import AutoMinorLocator, FuncFormatter, ScalarFormatter
from PySide6.QtCore import QSize, QTimer
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QVBoxLayout, QWidget

from .graph_data import GraphData


class DebouncedFigureCanvas(FigureCanvasQTAgg):
    """リサイズ時の再描画を遅延させ、ウィンドウ操作を軽量化するCanvas"""

    def __init__(self, figure: Figure) -> None:
        super().__init__(figure)

        # 遅延実行用のタイマー
        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        # 100ms待機 (サイズ変更から規定の時間経ったら、グラフ再描画)
        self._resize_timer.setInterval(100)
        self._resize_timer.timeout.connect(self._perform_delayed_resize)

        # 最新の「サイズ」を保持
        self._pending_size: QSize | None = None

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        """グラフ描画を即時実行せず、QWidgetのサイズ変更だけ先に行って描画を予約する"""
        # サイズ情報を保存
        self._pending_size = event.size()

        # QtのWidgetとしてのサイズ変更は即座に行う
        QWidget.resizeEvent(self, event)

        # タイマーをリセット (サイズ変更からの時間計測)
        self._resize_timer.start()

    def _perform_delayed_resize(self) -> None:
        """タイマー発火後に呼ばれる描画処理"""
        if self._pending_size:
            # 保存しておいたサイズから、新しいイベントオブジェクトを作成
            dummy_old_size = QSize()  # 空白で良い
            new_event = QResizeEvent(self._pending_size, dummy_old_size)

            # Matplotlibの親クラスのresizeEventを呼び出す
            super().resizeEvent(new_event)


class DualAxisGraph(QWidget):
    """2軸データ(左・右) を表示するグラフウィジェット"""

    _FALLBACK_X_LIMITS = (0.0, 1.0)
    _DEFAULT_X_PADDING = 0.5
    _VISIBLE_X_PADDING_RATIO = 0.05

    _layout: QVBoxLayout

    figure: Figure
    canvas: DebouncedFigureCanvas

    ax_left: Axes
    ax_right: Axes

    _series_map: dict[str, dict]
    _visible_x_span: int | float | None

    _legend_loc: str
    _current_data_source: GraphData | None

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # レイアウト & キャンバス
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self.figure = Figure(figsize=(5, 4), dpi=100, layout="constrained")  # constrainedで自動調整
        self.canvas = DebouncedFigureCanvas(self.figure)
        self._layout.addWidget(self.canvas)

        # Axes
        self.ax_left = self.figure.add_subplot(111)
        self.ax_right = self.ax_left.twinx()

        # 内部状態管理
        # key: ラベル名, value: { 'line': Line2D, 'axis': 'left'|'right', ... }
        self._series_map: dict[str, dict] = {}
        self._visible_x_span: int | float | None = None  # x軸の表示幅

        self._legend_loc: str = "best"  # 凡例場所
        self._current_data_source: GraphData | None = None  # 現在表示しているデータ

        self._sci_formatter = FuncFormatter(self._sci_mathtext)
        self._init_styles()

    @staticmethod
    def _sci_mathtext(x, _) -> str:  # noqa: ANN001
        if x == 0:
            return r"$0$"
        exp = int(np.floor(np.log10(abs(x))))
        mant = x / 10**exp
        return rf"${mant:.1f} \times 10^{{{exp}}}$"

    def _init_styles(self) -> None:
        """グラフ全体の基本スタイル適用"""
        self.set_title("Graph")
        self.set_axis_labels(x_label="X Axis", left_label="Left Y Axis", right_label="Right Y Axis")
        self.set_legend_location()  # 凡例初期化

        # 軸・グリッド描画
        for ax in [self.ax_left, self.ax_right]:
            ax.yaxis.set_minor_locator(AutoMinorLocator(5))
            ax.tick_params(which="both", labelsize="medium", direction="in", top=True)
        self.set_grid_target("left")  # 初期は左軸にグリッドを合わせる

    # =========================================================================================
    # Data
    # =========================================================================================

    def add_series(
        self,
        label: str,
        target_axis: Literal["left", "right"] = "left",
        color: str = "blue",
        marker: str | None = None,
        linestyle: str | None = None,
        legend_label: str | None = None,
        **kwargs,
    ) -> None:
        # 表示軸
        ax = self.ax_left if target_axis == "left" else self.ax_right

        # 凡例名
        display_name = legend_label if legend_label is not None else label

        # オプション引数
        if marker is not None:
            kwargs["marker"] = marker
        if linestyle is not None:
            kwargs["linestyle"] = linestyle

        # 要素登録
        (line,) = ax.plot([], [], label=display_name, color=color, linewidth=1.5, **kwargs)
        self._series_map[label] = {"line": line, "target_axis": target_axis}

        self.set_legend_location()

    def _update_axes_limits(self) -> None:
        """現在のデータとvisible_x_spanに基づいて軸の表示範囲を更新"""
        if self._current_data_source is None:
            return

        df = self._current_data_source.get_data()
        if df.empty or "x" not in df.columns:
            return

        # Y軸のオートスケール
        self.ax_left.relim()
        self.ax_left.autoscale_view()
        self.ax_right.relim()
        self.ax_right.autoscale_view()

        x_limits = self._calculate_x_limits(df["x"].values)
        self.ax_left.set_xlim(*x_limits)

    def _calculate_x_limits(self, raw_x_data: np.ndarray) -> tuple[float, float]:
        """表示設定を反映した安全なX軸範囲を返す"""
        finite_x_data = self._finite_x_data(raw_x_data)
        if len(finite_x_data) == 0:
            # 有効なX値がない場合は、最低限描画できる既定範囲に戻す。
            return self._FALLBACK_X_LIMITS

        min_x, max_x = self._raw_x_limits(finite_x_data)
        return self._safe_x_limits(min_x, max_x)

    def _finite_x_data(self, raw_x_data: np.ndarray) -> np.ndarray:
        """X軸範囲の計算に使える有限値だけを返す"""
        x_data = np.asarray(raw_x_data, dtype=float)
        return x_data[np.isfinite(x_data)]  # NaNやinfは除外する。

    def _raw_x_limits(self, finite_x_data: np.ndarray) -> tuple[float, float]:
        """表示幅指定を反映した補正前のX軸範囲を返す"""
        if self._visible_x_span is not None and len(finite_x_data) > 1:
            # 表示幅指定がある場合は、最新点を右端にして範囲をスライドする。
            current_x = float(finite_x_data[-1])
            min_x = max(float(np.min(finite_x_data)), current_x - self._visible_x_span)
            return min_x, current_x

        # 全期間表示または1点のみの場合は、有効なX値全体を表示対象にする。
        return float(np.min(finite_x_data)), float(np.max(finite_x_data))

    def _safe_x_limits(self, min_x: float, max_x: float) -> tuple[float, float]:
        """Matplotlibが扱える有限かつ非ゼロ幅のX軸範囲に補正する"""
        if not np.isfinite(min_x) or not np.isfinite(max_x):
            return self._FALLBACK_X_LIMITS

        if min_x != max_x:
            return min_x, max_x

        # データ1点目や同一timestamp連続時は上下限が同じになり、表示範囲が特異になる。
        # 表示幅指定がある場合はその幅に合わせ、ない場合は小さな既定余白で描画可能にする。
        if self._visible_x_span is not None and self._visible_x_span > 0:
            pad = self._visible_x_span * self._VISIBLE_X_PADDING_RATIO
        else:
            pad = self._DEFAULT_X_PADDING

        if not np.isfinite(pad) or pad <= 0:
            pad = self._DEFAULT_X_PADDING

        return min_x - pad, max_x + pad

    def update_plot(self, data_source: GraphData) -> None:
        """データソースをもとにグラフを再描画"""
        # データソースを保持 (span変更時の即時反映用)
        self._current_data_source = data_source

        df = data_source.get_data()
        if df.empty or "x" not in df.columns:
            return

        # データ更新
        x_data = df["x"].values
        for label, meta in self._series_map.items():
            if label in df.columns:
                y_data = df[label].values
                meta["line"].set_data(x_data, y_data)

        # 軸範囲の更新
        self._update_axes_limits()
        self.canvas.draw_idle()

    def clear_view(self) -> None:
        """表示をクリア"""
        self._current_data_source = None

        # ラインの中身を空にする
        for series in self._series_map.values():
            series["line"].remove()

        self._series_map.clear()
        self.canvas.draw_idle()

    # =========================================================================================
    # Display Settings
    # =========================================================================================

    def set_title(self, title: str = "", fontsize: str = "x-small") -> None:
        """グラフタイトル設定"""
        self.ax_left.set_title(title, fontsize=fontsize)

    def set_axis_labels(
        self,
        /,
        x_label: str | None = None,
        left_label: str | None = None,
        right_label: str | None = None,
        axis_fontsize: str = "large",
    ) -> None:
        """軸ラベルの名前変更"""
        if x_label:
            self.ax_left.set_xlabel(x_label, fontsize=axis_fontsize)
        if left_label:
            self.ax_left.set_ylabel(left_label, fontsize=axis_fontsize)
        if right_label:
            self.ax_right.set_ylabel(right_label, fontsize=axis_fontsize)

    def set_axis_scale(
        self, target: Literal["left", "right"], scale: Literal["linear", "log"]
    ) -> None:
        """軸のスケール設定 (線形 or 対数)"""
        ax = self.ax_left if target == "left" else self.ax_right
        ax.set_yscale(scale)

    def set_legend_location(self, loc: str | None = None, fontsize: str = "x-small") -> None:
        """凡例の場所指定 (matplotlibのloc準拠: 'upper right', 'upper left' etc)"""
        self._legend_loc = loc if loc is not None else self._legend_loc

        # 左右の軸のLine2Dをまとめて1つの凡例にする
        lines_l, labels_l = self.ax_left.get_legend_handles_labels()
        lines_r, labels_r = self.ax_right.get_legend_handles_labels()

        # 上から 右軸グラフ -> 左軸グラフ の順に重なっているため、
        # 凡例は右軸グラフから作成 (左軸からの場合、右軸のグラフが上に乗っかってしまう)
        self.ax_right.legend(
            lines_l + lines_r, labels_l + labels_r, loc=self._legend_loc, fontsize=fontsize
        )

    def set_grid_target(self, target: Literal["left", "right"]) -> None:
        """グリッドをどちらの軸に合わせるか"""
        self.ax_left.grid(False)
        self.ax_right.grid(False)

        target_ax = self.ax_left if target == "left" else self.ax_right
        target_ax.grid(True, linestyle="--", alpha=0.6)

    def set_axis_formatter(self, target: Literal["left", "right"], use_scientific: bool) -> None:
        """軸の表示形式を切り替える"""
        ax = self.ax_left if target == "left" else self.ax_right

        if use_scientific:
            ax.yaxis.set_major_formatter(FuncFormatter(self._sci_mathtext))
        else:
            ax.yaxis.set_major_formatter(ScalarFormatter())

        self.canvas.draw_idle()

    def set_visible_x_span(self, visible_x_span: float | None) -> None:
        """
        グラフのX軸の表示幅を設定する。

        parameter:
            x_window (float | None): x軸の表示幅。データが増えると自動でスライドする。
                                           Noneの場合は全範囲を表示する。
        """
        self._visible_x_span = visible_x_span
        if self._current_data_source:
            # キャッシュされているデータを使って軸範囲だけ更新
            self._update_axes_limits()
            self.canvas.draw_idle()

    def set_series_legend_label(self, series_key: str, new_label: str) -> None:
        """凡例表示名を変更"""
        if series_key in self._series_map:
            line = self._series_map[series_key]["line"]
            line.set_label(new_label)

            # 凡例を再描画して反映
            self.set_legend_location()
            self.canvas.draw_idle()
        else:
            print(f"Attempted to rename unknown series: {series_key}")
