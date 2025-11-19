import tomllib
from pathlib import Path

import tomli_w  # なぜかtomllibに書き込みがないため、サードパーティ製を使用

from heater_amd_controller.models.protocol import ProtocolConfig


class ProtocolManager:
    NEW_PROTOCOL_NAME = "新しいプロトコル..."
    SAVE_DIR = Path("protocols")  # 保存先ディレクトリ

    def __init__(self) -> None:
        # 保存ディレクトリがなければ作成
        self.SAVE_DIR.mkdir(exist_ok=True)

    def get_protocol_names(self) -> list[str]:
        """保存されているファイル名の一覧を取得し、最後に「新しいプロトコル...」を追加して返す"""
        files = list(self.SAVE_DIR.glob("*.toml"))
        names = [f.stem for f in files]  # 拡張子(.toml)を除く
        names.sort()

        # 最後に新規作成用の項目を追加
        names.append(self.NEW_PROTOCOL_NAME)
        return names

    def get_protocol(self, name: str) -> ProtocolConfig:
        """名前を指定してファイルを読み込む"""
        # 「新しいプロトコル」が選ばれたらデフォルト値を返す
        if name == self.NEW_PROTOCOL_NAME:
            return ProtocolConfig.default()

        file_path = self.SAVE_DIR / f"{name}.toml"

        if not file_path.exists():
            return ProtocolConfig.default()  # ファイルがない場合

        try:
            with file_path.open("rb") as f:
                data_dict = tomllib.load(f)

            # 辞書からデータクラスを復元
            # ※本来はバリデーションが必要ですが簡易的に実装
            return ProtocolConfig(**data_dict)

        except Exception as e:  # noqa: BLE001
            print(f"読み込みエラー: {e}")
            return ProtocolConfig.default()

    def save_protocol(self, name: str, data: ProtocolConfig) -> bool:
        """データをTOMLファイルとして保存する"""
        try:
            # 名前をデータにも反映
            data.name = name

            file_path = self.SAVE_DIR / f"{name}.toml"

            # 辞書化して保存
            with file_path.open("wb") as f:
                tomli_w.dump(data.to_dict(), f)

        except Exception as e:  # noqa: BLE001
            print(f"保存エラー: {e}")
            return False

        return True
