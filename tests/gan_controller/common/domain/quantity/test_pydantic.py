from typing import Annotated

import pytest
from pydantic import BaseModel, ValidationError

from gan_controller.common.domain.quantity import PydanticUnit, Quantity, Second


# テスト用のPydanticモデル定義
class ConfigModel(BaseModel):
    # 設定ファイル等では "分" 単位の数値として書かれていることを想定
    process_time: Annotated[Quantity[Second], *PydanticUnit("mins")]

    # "時間" 単位
    wait_time: Annotated[Quantity[Second], *PydanticUnit("hours")]

    # 通常のSI単位 (ミリ秒)
    pulse_width: Annotated[Quantity[Second], *PydanticUnit("ms")]


class TestQuantityPydantic:
    def test_deserialize_from_numbers(self) -> None:
        """数値からQuantityへの変換テスト"""
        data = {
            "process_time": 5,  # 5 mins
            "wait_time": 1.5,  # 1.5 hours
            "pulse_width": 100,  # 100 ms
        }
        model = ConfigModel(**data)

        # process_time (mins)
        assert model.process_time.value == 5.0  # noqa: PLR2004
        assert model.process_time.base_value == 300.0  # 5 * 60  # noqa: PLR2004
        assert str(model.process_time) == "5.0 min"  # 単位 s は隠蔽される

        # wait_time (hours)
        assert model.wait_time.value == 1.5  # noqa: PLR2004
        assert model.wait_time.base_value == 5400.0  # 1.5 * 3600  # noqa: PLR2004
        assert str(model.wait_time) == "1.5 hour"

        # pulse_width (ms)
        assert model.pulse_width.value == 100.0  # noqa: PLR2004
        assert model.pulse_width.base_value == 0.1  # noqa: PLR2004
        assert str(model.pulse_width) == "100.0 ms"

    def test_serialize_to_numbers(self) -> None:
        """Quantityから数値へのシリアライズテスト"""
        model = ConfigModel(
            process_time=Quantity(10, "mins"),
            wait_time=Quantity(2, "hours"),
            pulse_width=Quantity(50, "ms"),
        )

        # model_dump (dict) したときに、指定された単位の数値に戻ること
        dumped = model.model_dump()

        assert dumped["process_time"] == 10.0  # noqa: PLR2004
        assert dumped["wait_time"] == 2.0  # noqa: PLR2004
        assert dumped["pulse_width"] == 50.0  # noqa: PLR2004

    def test_validation_error(self) -> None:
        """不正な型が渡された場合のエラーテスト"""
        with pytest.raises(ValidationError):
            ConfigModel(process_time="invalid_string", wait_time=1, pulse_width=1)  # pyright: ignore[reportArgumentType]

    def test_unit_mismatch_check(self) -> None:
        """シリアライズ時に期待する単位と異なる場合のチェック (schemas.pyの実装依存)"""
        # PydanticUnit("mins") と指定されているフィールドに、
        # 内部的に単位が一致しないものを無理やり入れた場合の挙動確認
        # ※ Quantityの型チェックは実行時には緩いので、ロジックでの整合性を確認

        # Quantity[Second] なので物理量は合っているが、
        # シリアライザが unit="s" (base) を期待しているかどうかの確認
        q = Quantity(1, "km")  # 全く違う物理量(Length)

        # バリデータを通す段階では Quantity オブジェクトならそのままパスする実装の場合があるが、
        # serialize 時にチェックが入るか、あるいは validate 時にチェックされるか。
        # 現状の schemas.py の実装では、validate時は `isinstance` チェックのみでスルーパスするため、
        # 型ヒントを無視して代入はできてしまうが、serialize時にエラーになる可能性がある。

        # 今回の schemas.py の実装を確認すると、serialize 時に target_base との一致確認がある
        # process_time は "mins" -> base="s" なので "km" (base="m") はエラーになるはず

        with pytest.raises(ValueError, match="Unit mismatch"):
            # serialize関数を直接呼んでテストするか、model_dumpで確認
            ConfigModel(
                process_time=q, wait_time=Quantity(1, "hours"), pulse_width=Quantity(1, "ms")
            ).model_dump()
