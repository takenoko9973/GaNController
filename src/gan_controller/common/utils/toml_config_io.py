import tomllib
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any, cast

import tomlkit
from pydantic import BaseModel
from tomlkit import TOMLDocument, item
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
            _append_fields_with_comments(doc, model_instance, new_data)

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


def _generate_new_document(model_instance: BaseModel, dump_data: dict[str, Any]) -> TOMLDocument:
    """Pydantic定義を元にコメント付きTOMLドキュメントを生成"""
    doc = tomlkit.document()
    _append_fields_with_comments(doc, model_instance, dump_data)
    return doc


def _append_fields_with_comments(
    container: Table | TOMLDocument, model_instance: BaseModel, current_data: dict[str, Any]
) -> None:
    """フィールドとコメントを再帰的に追加"""
    model_class = type(model_instance)
    for field_name, field_info in model_class.model_fields.items():
        if field_name not in current_data:
            continue

        sub_model = getattr(model_instance, field_name)
        value = current_data[field_name]
        description = field_info.description

        if isinstance(value, dict) and isinstance(sub_model, BaseModel):
            # ネストされたPydanticモデルの場合
            _process_nested_model(container, field_name, value, sub_model, description)
        else:
            # 通常の値 (またはBaseModelではない辞書)
            _process_simple_value(container, field_name, value, description)


def _process_nested_model(
    container: Table | TOMLDocument,
    key: str,
    value: dict,
    sub_model: BaseModel,
    description: str | None,
) -> None:
    """ネストされたモデル(テーブル)の再帰処理"""
    if key in container:
        # === 既存データの場合
        existing_table = container[key]

        if isinstance(existing_table, MutableMapping):
            _append_fields_with_comments(cast("Table", existing_table), sub_model, value)
        else:
            # 型不整合などの場合 (基本ありえないが上書きで対処)
            container[key] = value

    else:
        # === 新規データの場合
        new_table = tomlkit.table()

        if description:
            # あらかじめコメントをつけておく
            new_table.comment(description)

        # 再帰呼び出し
        _append_fields_with_comments(new_table, sub_model, value)
        container.add(key, new_table)


def _process_simple_value(
    container: Table | TOMLDocument,
    key: str,
    value: Any,  # noqa: ANN401
    description: str | None,
) -> None:
    """単純な値の更新または追加"""
    if key in container:
        # [既存] 値のみ更新 (既存コメントを維持)
        container[key] = value

    else:
        # [新規] 追加してコメント付与
        it: Item = item(value)
        if description:
            it.comment(description)

        container.add(key, it)
