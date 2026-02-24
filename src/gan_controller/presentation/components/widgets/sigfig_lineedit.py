import math

from PySide6.QtWidgets import QDoubleSpinBox, QWidget


class SignificantFigureSpinBox(QDoubleSpinBox):
    """有効数字でのフォーマットと動的ステップ幅調整を行うスピンボックス"""

    def __init__(self, sig_figs: int = 3, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sig_figs = max(1, sig_figs)  # 有効数字

        self.setDecimals(10)  # 内部精度
        self.setRange(-1e10, 1e10)

        # Enter押下またはフォーカスアウト時にのみ入力を確定・評価する
        self.setKeyboardTracking(False)

        self.valueChanged.connect(self._update_single_step)

        self.setValue(0.0)
        self._update_single_step(0.0)

    @property
    def significant_figures(self) -> int:
        """有効数字の桁数を取得する。"""
        return self._sig_figs

    @significant_figures.setter
    def significant_figures(self, value: int) -> None:
        """有効数字のオーダーを設定し、内部状態と表示を更新する。"""
        if value > 0 and self._sig_figs != value:
            self._sig_figs = value
            self._update_single_step(self.value())
            self.setValue(self.value())  # 表示の強制更新

    def _get_magnitude(self, value: float) -> int:
        """値のオーダーを計算して返す。"""
        return math.floor(math.log10(abs(value))) if value != 0.0 else 0

    def textFromValue(self, value: float) -> str:  # noqa: N802
        """内部数値を有効数字の文字列に変換して表示する。"""
        if value == 0.0:
            return f"0.{'0' * (self._sig_figs - 1)}" if self._sig_figs > 1 else "0"

        # 値のオーダーから必要な小数点以下の桁数を算出（マイナスにならないよう max で制限）
        magnitude: int = self._get_magnitude(value)
        decimal_places: int = max(0, self._sig_figs - 1 - magnitude)
        return f"{value:.{decimal_places}f}"

    def valueFromText(self, text: str) -> float:  # noqa: N802
        """入力文字列をパースし、有効数字で丸めた数値を返す。"""
        # Suffix(接尾辞)とPrefix(接頭辞)を取り除き、前後の空白を削除
        text = text.replace(self.suffix(), "").replace(self.prefix(), "").strip()

        try:
            value = float(text)
            if value == 0.0:
                return 0.0

            # オーダーから丸め位置を算出して適用
            magnitude: int = self._get_magnitude(value)
            round_digits: int = self._sig_figs - 1 - magnitude
            return round(value, round_digits)
        except ValueError:
            return 0.0

    def _update_single_step(self, value: float) -> None:
        """現在の値の桁数に合わせてステップ幅を動的に変更する。"""
        if value == 0.0:
            step = 10 ** -(self._sig_figs - 1)
        else:
            magnitude = math.floor(math.log10(abs(value)))
            step = 10 ** (magnitude - self._sig_figs + 1)

        self.setSingleStep(step)
