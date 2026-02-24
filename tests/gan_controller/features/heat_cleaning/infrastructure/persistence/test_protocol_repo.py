from pathlib import Path

import pytest

from gan_controller.features.heat_cleaning.domain.config import ProtocolConfig
from gan_controller.features.heat_cleaning.domain.interface import IProtocolRepository
from gan_controller.features.heat_cleaning.infrastructure.persistence.repository import (
    ProtocolRepository,
)


class TestFileProtocolRepository:
    @pytest.fixture
    def repo(self, tmp_path: Path) -> IProtocolRepository:
        # tmp_path は pytest が提供する一時ディレクトリ。テスト終了後に自動で削除される。
        return ProtocolRepository(base_dir=tmp_path)

    def test_save_and_load(self, repo: IProtocolRepository) -> None:
        # 1. 保存のテスト
        config = ProtocolConfig()  # デフォルト設定
        name = "TEST01"

        repo.save(name, config)

        assert repo.exists(name) is True

        # 2. 読み込みのテスト
        loaded_config = repo.load(name)
        assert isinstance(loaded_config, ProtocolConfig)
        assert loaded_config == config

    def test_list_names(self, repo: IProtocolRepository) -> None:
        # 空の状態
        assert repo.list_names() == []

        # 2つ保存してみる
        repo.save("A_PROTOCOL", ProtocolConfig())
        repo.save("B_PROTOCOL", ProtocolConfig())

        names = repo.list_names()
        assert len(names) == 2
        assert "A_PROTOCOL" in names
        assert "B_PROTOCOL" in names
