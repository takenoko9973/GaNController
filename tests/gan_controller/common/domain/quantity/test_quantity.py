import pytest

from gan_controller.core.domain.quantity import Quantity, Time, Value


class TestQuantity:
    def test_percent(self) -> None:
        q = Quantity(12.3, "%")
        assert q.base_value == pytest.approx(0.123)
        assert q.value_as("%") == pytest.approx(12.3)

    def test_meter(self) -> None:
        """メートルが機能するか (ミリと勘違いされないかどうか)"""
        q = Quantity(200, "m")
        assert q.unit == "m"
        assert q.display_prefix == ""
        assert q.base_value == 200
        assert q.value_as("m") == 200000

        q = Quantity(200, "mm")
        assert q.unit == "m"
        assert q.display_prefix == "m"
        assert q.base_value == 0.2
        assert q.value_as("m") == 200

    def test_second_basic(self) -> None:
        q = Quantity(2, "s")
        assert q.base_value == 2
        assert format(q, ".1f") == "2.0 s"

    def test_millisecond(self) -> None:
        q = Quantity(1, "ms")
        assert q.base_value == 0.001
        assert format(q, ".1f") == "1.0 ms"

    def test_minute_normalization(self) -> None:
        q = Quantity(2, "mins")
        assert q.base_value == 120
        assert q.unit == "s"
        assert format(q, ".1f") == "2.0 min"

    def test_hour_normalization(self) -> None:
        q = Quantity(0.5, "hours")
        assert q.base_value == 1800
        assert q.unit == "s"
        assert format(q, ".1f") == "0.5 hour"

    def test_quantity_format(self) -> None:
        """f-stringでのフォーマット指定テスト"""
        q = Quantity(1.23456, "mins")

        # 小数点2桁指定
        formatted = f"{q:.2f}"
        assert formatted == "1.23 min"

    def test_quantity_invalid_unit(self) -> None:
        """存在しない単位でのエラーテスト"""
        with pytest.raises(ValueError, match="Invalid unit"):
            Quantity(10, "invalid_unit")

    def test_quantity_invalid_prefix_combination(self) -> None:
        """許可されていない単位と接頭辞の組み合わせテスト"""
        # "min" は allowed_units={"s"} なので、m (メートル) には使えない
        # "minm" -> prefix="min", base="m"
        with pytest.raises(ValueError, match="cannot be used with unit 'm'"):
            Quantity(10, "minm")
        with pytest.raises(ValueError, match="cannot be used with unit 'V'"):
            Quantity(10, "%V")


class TestFactory:
    def test_factory_time(self) -> None:
        q = Time(3)
        assert q.base_value == 3
        assert format(q, ".1f") == "3.0 s"

    def test_factory_time_ms(self) -> None:
        q = Time(1, "m")
        assert q.base_value == 0.001
        assert format(q, ".1f") == "1.0 ms"

    def test_factory_minute(self) -> None:
        q = Time(3, "min")
        assert q.base_value == 180
        assert format(q, ".1f") == "3.0 min"

    def test_factory_hour(self) -> None:
        q = Time(2, "hour")
        assert q.base_value == 7200
        assert format(q, ".1f") == "2.0 hour"

    def test_dimensionless(self) -> None:
        q = Value(3)
        assert q.base_value == 3
        assert format(q, ".1f") == "3.0"

        q = Value(12, "%")
        assert q.base_value == 0.12
        assert format(q, ".1f") == "12.0 %"
