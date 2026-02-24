import pytest
from pytestqt.qtbot import QtBot

from gan_controller.presentation.components.widgets.sigfig_lineedit import SignificantFigureSpinBox


class TestSignificantFigureSpinBox:
    """SignificantFigureSpinBoxのユニットテスト群"""

    @pytest.fixture
    def spinbox(self, qtbot: QtBot) -> SignificantFigureSpinBox:
        """テストごとにクリーンなウィジェットインスタンスを提供するフィクスチャ"""
        widget: SignificantFigureSpinBox = SignificantFigureSpinBox(sig_figs=3)
        qtbot.addWidget(widget)
        return widget

    def test_initialization(self, spinbox: SignificantFigureSpinBox) -> None:
        """初期化時のデフォルト値と設定を検証する"""
        assert spinbox.significant_figures == 3
        assert spinbox.value() == 0.0
        assert not spinbox.keyboardTracking()  # Enter/FocusOut確定が有効か

    def test_value_from_text_rounding(self, spinbox: SignificantFigureSpinBox) -> None:
        """入力された文字列が有効数字3桁に正しく丸められるか検証する"""
        # 通常の小数
        assert spinbox.valueFromText("1.234") == 1.23
        assert spinbox.valueFromText("1.235") == 1.24  # Pythonのround(偶数丸め)に依存

        # オーダーが異なる場合
        assert spinbox.valueFromText("12.34") == 12.3
        assert spinbox.valueFromText("0.01234") == 0.0123
        assert spinbox.valueFromText("1234") == 1230.0

    def test_value_from_text_invalid(self, spinbox: SignificantFigureSpinBox) -> None:
        """無効な文字列が入力された場合のエッジケース"""
        assert spinbox.valueFromText("abc") == 0.0
        assert spinbox.valueFromText("") == 0.0

    def test_text_from_value_formatting(self, spinbox: SignificantFigureSpinBox) -> None:
        """内部のfloat値が正しい有効数字の文字列としてフォーマットされるか検証する"""
        assert spinbox.textFromValue(1.23) == "1.23"
        assert spinbox.textFromValue(12.3) == "12.3"
        assert spinbox.textFromValue(1230.0) == "1230"  # #g フォーマットの挙動

        # ゼロの場合のパディング（sig_figs=3なら "0.00" になるのが理想だが、
        # 現在の実装ではPythonの #g 仕様に依存している部分の確認）
        assert spinbox.textFromValue(0.0) == "0.00"

    def test_dynamic_single_step(self, spinbox: SignificantFigureSpinBox) -> None:
        """値のオーダーに応じてステップ幅(singleStep)が変化するか検証する"""
        # 0.0 の場合 (有効数字3桁 -> 0.01ステップ)
        spinbox.setValue(0.0)
        assert spinbox.singleStep() == pytest.approx(0.01)

        # 1.23 の場合 (オーダー0 -> 0.01ステップ)
        spinbox.setValue(1.23)
        assert spinbox.singleStep() == pytest.approx(0.01)

        # 12.3 の場合 (オーダー1 -> 0.1ステップ)
        spinbox.setValue(12.3)
        assert spinbox.singleStep() == pytest.approx(0.1)

        # 0.0123 の場合 (オーダー-2 -> 0.0001ステップ)
        spinbox.setValue(0.0123)
        assert spinbox.singleStep() == pytest.approx(0.0001)

    def test_sig_figs_property_update(self, spinbox: SignificantFigureSpinBox) -> None:
        """有効数字プロパティを変更した際、ステップ幅などが再計算されるか検証する"""
        spinbox.setValue(1.234)  # 丸められて 1.23 になる

        # 有効数字を4桁に変更
        spinbox.significant_figures = 4
        assert spinbox.significant_figures == 4

        # プロパティ変更後、新しい精度でステップ幅が計算されるか
        # 1.23 (オーダー0, 4桁 -> 0.001ステップ)
        assert spinbox.singleStep() == pytest.approx(0.001)
