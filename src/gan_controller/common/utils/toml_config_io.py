import tomllib
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any, cast

import tomlkit
from pydantic import BaseModel
from tomlkit.items import Item, Table


def load_toml_config[T: BaseModel](model_cls: type[T], path: str | Path) -> T:
    """TOMLファイルからPydanticモデルを読み込む"""
    path_obj = Path(path)
    if not path_obj.exists():
        return model_cls()

    try:
        with path_obj.open("rb") as f:
            data = tomllib.load(f)
        return model_cls.model_validate(data)
    except Exception as e:  # noqa: BLE001
        print(f"Config load error ({model_cls.__name__}): {e}")
        return model_cls()


def save_toml_config(model_instance: BaseModel, path: str | Path) -> None:
    """PydanticモデルをTOMLファイルに保存する (コメント保持)"""
    path_obj = Path(path)
    new_data = model_instance.model_dump(mode="json")

    try:
        if path_obj.exists():
            # 既存ファイルがある場合は読み込んで更新 (コメント構造を維持するため)
            with path_obj.open("r", encoding="utf-8") as f:
                doc = tomlkit.load(f)
            _recursive_update(doc, new_data)

        else:
            # 新規作成 (Pydanticのdescriptionからコメント生成)
            doc = _generate_new_document(model_instance, new_data)

        # 書き込み
        with path_obj.open("w", encoding="utf-8") as f:
            tomlkit.dump(doc, f)

    except Exception as e:  # noqa: BLE001
        print(f"Config save error ({model_instance.__class__.__name__}): {e}")


# ==========================================
#  Internal Helpers
# ==========================================


def _generate_new_document(
    model_instance: BaseModel, dump_data: dict[str, Any]
) -> tomlkit.TOMLDocument:
    """Pydantic定義を元にコメント付きTOMLドキュメントを生成"""
    doc = tomlkit.document()
    _append_fields_with_comments(doc, model_instance, dump_data)
    return doc


def _append_fields_with_comments(
    container: Table | tomlkit.TOMLDocument, model_instance: BaseModel, current_data: dict[str, Any]
) -> None:
    """フィールドとコメントを再帰的に追加"""
    model_class = type(model_instance)
    for field_name, field_info in model_class.model_fields.items():
        if field_name not in current_data:
            continue

        value = current_data[field_name]

        # 値が辞書ならネストされたモデルとみなす
        if isinstance(value, dict):
            # 対応するサブモデルのインスタンスを取得 (description取得)
            sub_model = getattr(model_instance, field_name)

            if isinstance(sub_model, BaseModel):
                table = tomlkit.table()

                _append_fields_with_comments(table, sub_model, value)  # 再帰的に検索

                container.add(field_name, table)
                if field_info.description:
                    cast("Item", container[field_name]).comment(field_info.description)

                continue

        # 通常の値 (float, int, str, Quantity由来のfloatなど) の処理
        container.add(field_name, cast("Any", value))
        if field_info.description:
            cast("Item", container[field_name]).comment(field_info.description)


def _recursive_update(doc: MutableMapping, new_data: dict) -> None:
    """構造を維持して値を更新"""
    for key, value in new_data.items():
        if key in doc and isinstance(doc[key], MutableMapping) and isinstance(value, dict):
            _recursive_update(doc[key], value)
        else:
            doc[key] = value
