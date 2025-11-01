from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd
from matplotlib import pyplot as plt

from heater_amd_controller.utils.log_file import LogFile

from .plot_util import AxisSide, PlotInfo, plot_twinx_multi_y


class BasePlotter(ABC):
    """共通のログ解析・描画基底クラス"""

    def __init__(self, logfile: LogFile, save_dir: Path, overwrite: bool = False) -> None:
        self.logfile = logfile
        self.save_dir = save_dir
        self.overwrite = overwrite

        self.log_df = pd.read_csv(self.logfile.path, comment="#", sep="\t")
        self.conditions = self._parse_conditions()

    @property
    def time_axis(self) -> pd.Series:
        return self.log_df["Time[s]"] / 3600  # hour

    def _parse_conditions(self) -> dict[str, dict[str, str]]:
        """ログファイル内の先頭コメントから条件を抽出"""
        sections: dict[str, dict[str, str]] = {}

        current_section = None
        with self.logfile.path.open(encoding="utf-8") as f:
            for line in f:
                if line.startswith("#Data"):
                    break
                if not line.startswith("#"):
                    continue

                text = line.strip("#").strip()

                # 空行・区切り行をスキップ
                if not text:
                    continue

                # セクション開始行
                if not ("\t" in text or ":" in text):
                    current_section = text
                    sections[current_section] = {}
                    continue

                # 通常の key-value 行
                if current_section is None:
                    continue  # セクション外なら無視

                if current_section == "Comment":
                    sections[current_section]["comment"] += text.strip()
                elif ":" in text:
                    key, val = text.split(":", 1)
                    sections[current_section][key.strip()] = val.strip()
                elif "\t" in text:
                    key, val = text.split("\t", 1)
                    sections[current_section][key.strip()] = val.strip()

        return sections

    @abstractmethod
    def plot(self) -> None:
        """プロトコルごとの描画メイン"""

    def _plot_save(
        self,
        filename: str,
        plot_info_list: list[PlotInfo],
        xlabel: str,
        ylabel_left: str,
        ylabel_right: str | None = None,
        ylim_left: tuple[float, float] | None = None,
        ylim_right: tuple[float, float] | None = None,
        plot_size: tuple[int, int] = (900, 500),
    ) -> None:
        if self._should_skip(filename):
            return

        fig, _, _ = self._plot_generate(
            plot_info_list, xlabel, ylabel_left, ylabel_right, ylim_left, ylim_right, plot_size
        )

        self._save_figure(fig, filename)
        plt.close(fig)

    def _plot_generate(
        self,
        plot_info_list: list[PlotInfo],
        xlabel: str,
        ylabel_left: str,
        ylabel_right: str | None = None,
        ylim_left: tuple[float, float] | None = None,
        ylim_right: tuple[float, float] | None = None,
        plot_size: tuple[int, int] = (900, 500),
    ) -> tuple[plt.Figure, plt.Axes, plt.Axes | None]:
        """汎用的な2軸グラフ生成処理"""
        fig, ax1, ax2 = plot_twinx_multi_y(
            self.time_axis,
            plot_info_list,
            plot_size,
            xlabel,
            ylabel_left,
            ylabel_right or "",
            self.logfile.path.stem,
        )

        # =========================

        time_h = self.time_axis
        ax1.set_xlim(time_h.min(), time_h.max())

        if ylim_left:
            ax1.set_ylim(*ylim_left)
        if ylim_right and ax2:
            ax2.set_ylim(*ylim_right)

        # =========================

        # 重複チェック
        scales = {AxisSide.LEFT: set(), AxisSide.RIGHT: set()}
        for plot_info in plot_info_list:
            scales[plot_info.axis].add(plot_info.scale)

        if len(scales[AxisSide.LEFT]) >= 2:  # noqa: PLR2004
            # linter, logが両方ある場合
            print("[WARN] 右軸に log/linear が混在しています。log優先で描画します。")
            ax1.set_yscale("log")
        else:
            ax1.set_yscale(
                next(iter(scales[AxisSide.LEFT])).value if scales[AxisSide.LEFT] else "linear"
            )

        if ax2:
            if len(scales[AxisSide.RIGHT]) >= 2:  # noqa: PLR2004
                # linter, logが両方ある場合
                print("[WARN] 右軸に log/linear が混在しています。log優先で描画します。")
                ax2.set_yscale("log")
            else:
                ax2.set_yscale(
                    next(iter(scales[AxisSide.RIGHT])).value if scales[AxisSide.RIGHT] else "linear"
                )

        return fig, ax1, ax2

    def _should_skip(self, filename: str) -> bool:
        save_path = self.save_dir / filename
        if save_path.exists() and not self.overwrite:
            print(f"[SKIP] {save_path.name} は既に存在します。")
            return True

        return False

    def _save_figure(self, fig: plt.Figure, filename: str) -> None:
        save_path = self.save_dir / filename
        if save_path.exists() and not self.overwrite:
            print(f"[SKIP] {save_path.name} は既に存在します。")
            plt.close(fig)
            return

        fig.tight_layout()
        # plt.show()
        fig.savefig(self.save_dir / filename, format="svg")
        print(f"[SAVE] {save_path.name} を保存しました。")
