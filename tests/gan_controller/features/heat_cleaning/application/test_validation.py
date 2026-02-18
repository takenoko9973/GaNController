from unittest.mock import Mock

from gan_controller.features.heat_cleaning.application.protocol_manager import ProtocolManager
from gan_controller.features.heat_cleaning.domain.interface import IProtocolRepository


def _create_manager() -> ProtocolManager:
    """テスト用のProtocolManagerインスタンスを生成するヘルパー関数"""
    mock_repo = Mock(spec=IProtocolRepository)
    return ProtocolManager(mock_repo)


def test_validate_name_success() -> None:
    """正しい名前ならTrueが返る"""
    manager = _create_manager()
    is_valid, msg = manager._validate_name("TEST1")  # noqa: SLF001

    assert is_valid is True
    assert msg == ""


def test_validate_name_fail_invalid_char() -> None:
    """不正な文字が含まれていたらFalseが返る"""
    manager = _create_manager()
    is_valid, msg = manager._validate_name("test-1")  # 小文字やハイフン  # noqa: SLF001

    assert is_valid is False
    assert "英大文字" in msg


def test_validate_name_fail_empty() -> None:
    """空文字の場合はFalseが返る"""
    manager = _create_manager()
    is_valid, msg = manager._validate_name("")  # noqa: SLF001

    assert is_valid is False
    assert "入力してください" in msg


def test_validate_name_fail_forbidden_char() -> None:
    """OSで禁止されている文字が含まれていたらFalseが返る"""
    manager = _create_manager()
    is_valid, msg = manager._validate_name("TEST/1")  # noqa: SLF001

    assert is_valid is False
    assert "使用できない文字" in msg
