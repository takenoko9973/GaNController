from gan_controller.features.heat_cleaning.application.validator import ProtocolValidator


def test_validate_name_success() -> None:
    """正しい名前ならTrueが返る"""
    is_valid, msg = ProtocolValidator.validate_name("TEST1")
    assert is_valid is True
    assert msg == ""


def test_validate_name_fail_invalid_char() -> None:
    """不正な文字が含まれていたらFalseが返る"""
    is_valid, msg = ProtocolValidator.validate_name("test-1")  # 小文字やハイフン
    assert is_valid is False
    assert "英大文字" in msg
