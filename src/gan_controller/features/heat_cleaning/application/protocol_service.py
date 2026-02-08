from collections.abc import Callable
from dataclasses import dataclass

from gan_controller.features.heat_cleaning.application.validator import ProtocolValidator
from gan_controller.features.heat_cleaning.domain.repository import IProtocolRepository
from gan_controller.features.heat_cleaning.schemas.config import ProtocolConfig


@dataclass
class SaveContext:
    """保存に必要な情報"""

    name: str
    config: ProtocolConfig
    # ユーザーへの問いかけを行うコールバック関数を受け取る
    confirm_overwrite: Callable[[str], bool]


class ProtocolService:
    def __init__(self, repository: IProtocolRepository, validator: ProtocolValidator) -> None:
        self._repo = repository
        self._validator = validator

    def get_protocol_names(self) -> list[str]:
        """プロトコル名の一覧を取得"""
        return self._repo.list_names()

    def load_protocol(self, name: str) -> ProtocolConfig:
        """プロトコル設定をロード"""
        return self._repo.load(name)

    def save_protocol(self, context: SaveContext) -> tuple[bool, str]:
        """保存処理実行

        Returns: (成功したか, メッセージ)
        """
        # 1. バリデーション
        is_valid, msg = self._validator.validate_name(context.name)
        if not is_valid:
            return False, msg

        # 2. 重複チェックと確認
        if self._repo.exists(context.name) and not context.confirm_overwrite(context.name):
            return False, "キャンセルされました"

        # 3. 保存実行
        try:
            self._repo.save(context.name, context.config)
        except Exception as e:  # noqa: BLE001
            return False, f"保存失敗: {e}"
        else:
            return True, "保存しました"
