from gan_controller.features.heat_cleaning.domain.sequence import Decrease, HeatCleaning, Rising


class TestSequence:
    def test_current_rising(self) -> None:
        """昇温シーケンスのテスト"""
        seq = Rising(duration_sec=10.0, exponent=1)
        max_current = 10.0  # 10A

        # 開始直後
        assert seq.current(max_current, 0.0) == 0.0
        assert seq.current(max_current, 5.0) == 5.0  # noqa: PLR2004
        assert seq.current(max_current, 10.0) == 10.0  # noqa: PLR2004

    def test_current_constant(self) -> None:
        """HeatCleaningシーケンスのテスト"""
        seq = HeatCleaning(duration_sec=5.0, exponent=1)
        max_current = 20.0

        assert seq.current(max_current, 0.0) == 20.0  # noqa: PLR2004
        assert seq.current(max_current, 2.5) == 20.0  # noqa: PLR2004
        assert seq.current(max_current, 5.0) == 20.0  # noqa: PLR2004

    def test_current_decrease(self) -> None:
        """降温シーケンスのテスト"""
        seq = Decrease(duration_sec=10.0, exponent=1)
        max_current = 5.0  # 10A

        # 開始直後
        assert seq.current(max_current, 0.0) == 5.0  # noqa: PLR2004
        assert seq.current(max_current, 5.0) == 2.5  # noqa: PLR2004
        assert seq.current(max_current, 10.0) == 0.0
