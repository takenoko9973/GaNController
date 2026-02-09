from pathlib import Path

from gan_controller.common.constants import PROTOCOLS_DIR
from gan_controller.features.heat_cleaning.domain.config import ProtocolConfig
from gan_controller.features.heat_cleaning.domain.interface import IProtocolRepository


class ProtocolRepository(IProtocolRepository):
    def __init__(self, base_dir: Path = PROTOCOLS_DIR) -> None:
        self.base_dir = base_dir

    def list_names(self) -> list[str]:
        """保存されているプロトコル名一覧を取得"""
        if not self.base_dir.exists():
            return []

        return [p.stem for p in self.base_dir.glob("*.toml")]

    def load(self, name: str) -> ProtocolConfig:
        """プロトコル読み込み"""
        try:
            return ProtocolConfig.load(f"{name}.toml", config_dir=self.base_dir)
        except Exception as e:  # noqa: BLE001
            # 読み込みに失敗したら、初期値を返す
            print(f"Failed to load protocol {name}: {e}")
            return ProtocolConfig()

    def save(self, name: str, config: ProtocolConfig) -> None:
        """プロトコル保存"""
        config.save(f"{name}.toml", config_dir=self.base_dir)

    def exists(self, name: str) -> bool:
        """存在確認"""
        return name in self.list_names()
