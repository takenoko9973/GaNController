import re
from collections.abc import Callable
from dataclasses import dataclass

from gan_controller.features.heat_cleaning.domain.config import ProtocolConfig
from gan_controller.features.heat_cleaning.domain.interface import IProtocolRepository


@dataclass
class SaveContext:
    """保存操作に必要なコンテキスト情報"""

    name: str
    config: ProtocolConfig
    # ユーザーへの問いかけを行うコールバック関数を受け取る
    confirm_overwrite: Callable[[str], bool]


class ProtocolManager:
    def __init__(self, repository: IProtocolRepository) -> None:
        self._repo = repository

    def get_protocol_names(self) -> list[str]:
        """プロトコル名の一覧を取得"""
        return self._repo.list_names()

    def load_protocol(self, name: str) -> ProtocolConfig:
        """プロトコル設定をロード"""
        return self._repo.load(name)

    def save_protocol(self, context: SaveContext) -> tuple[bool, str]:
        """
        保存処理実行

        Returns: (成功したか, メッセージ)
        """
        # 1. バリデーション
        is_valid, msg = self._validate_name(context.name)
        if not is_valid:
            return False, msg

        # 2. 重複チェックと確認
        if self._repo.exists(context.name) and not context.confirm_overwrite(context.name):
            return False, "保存をキャンセルしました"

        # 3. 保存実行
        try:
            self._repo.save(context.name, context.config)
            return True, "保存しました"
        except Exception as e:  # noqa: BLE001
            return False, f"保存失敗: {e}"

    def _validate_name(self, name: str) -> tuple[bool, str]:
        if not name:
            return False, "プロトコル名を入力してください"

        # 禁止文字チェック
        invalid_chars = ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]
        if any(char in name for char in invalid_chars):
            return False, "プロトコル名に使用できない文字が含まれています"

        if not re.fullmatch(r"[A-Z0-9]+", name):
            return False, "プロトコル名は英大文字(A-Z)と数字(0-9)のみ使用可能です"

        return True, ""
