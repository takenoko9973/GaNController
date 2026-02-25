from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd
from matplotlib import pyplot as plt

from gan_controller.infrastructure.persistence.log_manager import LogFile
from scripts.data_plot.plot_util import AxisSide, GraphBuilder, PlotInfo, PlotStyleConfig


class BasePlotter(ABC):
    """共通のログ解析・描画基底クラス"""

    def __init__(self, logfile: LogFile, save_dir: Path, overwrite: bool = False) -> None:
        self.logfile = logfile
        self.save_dir = save_dir
        self.overwrite = overwrite

        self._log_df: pd.DataFrame | None = None
        self.conditions = self._parse_conditions()

    def extract_data(self) -> bool:
        """
        [Extract] ログファイルからデータを読み込む

        Returns:
            bool: データの読み込みに成功し、描画に必要な最低限の列が存在すれば True。
                  無効なデータの場合は False。

        """
        if self._log_df is not None:
            return True

        try:
            # データの読み込み
            self._log_df = pd.read_csv(
                self.logfile.path, comment="#", sep="\t", na_values=["NAN", "nan"]
            )
            self.conditions = self._parse_conditions()

            # データフレームが空でないか
            if self._log_df.empty:
                print(f"[ERROR] {self.logfile.path.name}: データ行が存在しません。")
                return False

            return True

        except pd.errors.EmptyDataError:
            print(
                f"[ERROR] {self.logfile.path.name}: "
                "ファイルが空、またはパース可能なデータがありません"
            )
            return False
        except Exception as e:  # noqa: BLE001
            print(
                f"[ERROR] {self.logfile.path.name}: 読み込み中に予期せぬエラーが発生しました ({e})"
            )
            return False

    @property
    def log_df(self) -> pd.DataFrame:
        if self._log_df is None:
            msg = "Data not loaded. Call extract_data() first."
            raise ValueError(msg)

        return self._log_df

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
        ylabel_right: str = "",
        ylim_left: tuple[float, float] | None = None,
        ylim_right: tuple[float, float] | None = None,
        style_config: PlotStyleConfig | None = None,
    ) -> None:
        if self._should_skip(filename):
            return

        # ビルダーの初期化と基本設定
        builder = GraphBuilder(style_config)
        builder.set_title(self.logfile.path.stem)
        builder.set_labels(xlabel, ylabel_left, ylabel_right)

        # X軸の範囲設定
        time_h = self.time_axis
        builder.set_xlim(time_h.min(), time_h.max())

        # Y軸の範囲設定
        if ylim_left:
            builder.set_base_ylim(AxisSide.LEFT, *ylim_left)
        if ylim_right:
            builder.set_base_ylim(AxisSide.RIGHT, *ylim_right)

        # データの追加とスケール(log/linear)の記録
        scales = {AxisSide.LEFT: set(), AxisSide.RIGHT: set()}
        for plot_info in plot_info_list:
            builder.add_plot(time_h, plot_info)
            scales[plot_info.axis].add(plot_info.scale)

        # スケールの適用 (混在時はlog優先)
        for side in [AxisSide.LEFT, AxisSide.RIGHT]:
            if len(scales[side]) >= 2:  # noqa: PLR2004
                print(f"[WARN] {side.value}軸に log/linear が混在しています。log優先で描画します。")
                builder.set_yscale(side, "log")
            elif len(scales[side]) == 1:
                builder.set_yscale(side, next(iter(scales[side])).value)

        # グラフの完成と保存
        fig = builder.finalize()
        self._save_figure(fig, filename)
        plt.close(fig)

    def _should_skip(self, filename: str) -> bool:
        save_path = self.save_dir / filename
        if save_path.exists() and not self.overwrite:
            print(f"[SKIP] {save_path.name} は既に存在します。")
            return True
        return False

    def _save_figure(self, fig: plt.Figure, filename: str) -> None:
        save_path = self.save_dir / filename
        fig.savefig(save_path, format="svg")
        print(f"[SAVE] {save_path.name} を保存しました。")
