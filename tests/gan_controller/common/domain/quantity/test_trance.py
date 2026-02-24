from gan_controller.core.domain.quantity import Quantity


class TestQuantityConversion:
    def test_time_conversions(self) -> None:
        """時間単位間の相互変換テスト"""
        # 1 hour
        q_hour = Quantity(1.0, "hours")

        # hour -> min
        val_min = q_hour.value_as("min")
        assert val_min == 60.0

        # hour -> s
        val_sec = q_hour.value_as("")  # prefix="" (SI単位)
        assert val_sec == 3600.0

        # min -> hour
        q_min = Quantity(90, "mins")
        val_hour = q_min.value_as("hour")
        assert val_hour == 1.5


class TestQuantityParserEdgeCases:
    def test_single_letter_units(self) -> None:
        """1文字単位のパーステスト (V, A, s, m 等)"""
        # "V" (Volt)
        q_v = Quantity(5, "V")
        assert q_v.unit == "V"
        assert q_v.display_prefix == ""

        # "A" (Ampere)
        q_a = Quantity(2, "A")
        assert q_a.unit == "A"

        # "s" (Second)
        q_s = Quantity(10, "s")
        assert q_s.unit == "s"

    def test_prefix_unit_overlap(self) -> None:
        """接頭辞と単位が重なるケースの再確認"""
        # "m" -> メートル (prefix="", unit="m")
        q_m = Quantity(1, "m")
        assert q_m.unit == "m"
        assert q_m.display_prefix == ""
        assert q_m.base_value == 1.0

        # "ms" -> ミリ秒 (prefix="m", unit="s")
        q_ms = Quantity(1, "ms")
        assert q_ms.unit == "s"
        assert q_ms.display_prefix == "m"
        assert q_ms.base_value == 0.001

        # "mm" -> ミリメートル (prefix="m", unit="m")
        q_mm = Quantity(1, "mm")
        assert q_mm.unit == "m"
        assert q_mm.display_prefix == "m"
        assert q_mm.base_value == 0.001

    def test_dimensionless_units(self) -> None:
        """無次元量や特殊単位のテスト"""
        # "%"
        q_pct = Quantity(50, "%")
        assert q_pct.base_value == 0.5
        assert str(q_pct) == "50.0 %"

        # "ppm"
        q_ppm = Quantity(100, "ppm")
        assert q_ppm.base_value == 100 * 1e-6
        assert str(q_ppm) == "100.0 ppm"
