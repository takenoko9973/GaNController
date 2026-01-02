import datetime
import tomllib
from pathlib import Path

import tomlkit
from pydantic import BaseModel, Field
from tomlkit.items import Table


# gm10 セクション
class GM10Config(BaseModel):
    ext_ch: int = Field(default=-1, description="真空度(EXT)測定Ch番号")
    sip_ch: int = Field(default=-1, description="SIP測定Ch番号")
    hv_ch: int = Field(default=-1, description="HV制御出力Ch番号")
    pc_ch: int = Field(default=-1, description="フォトカレント測定Ch番号")
    tc_ch: int = Field(default=-1, description="TC測定Ch番号")


# pfr_100l50 セクション
class PFR100l50Config(BaseModel):
    unit: int = Field(default=0)
    v_limit: float = Field(default=18, description="最大印加電圧[V]")
    ovp: float = Field(default=19, description="過電圧保護値[V]")
    ocp: float = Field(default=5.0, description="過電流保護値[A]")


class IBeamConfig(BaseModel):
    beam_ch: int = Field(default=2, description="ビームチャンネル")


# ======================================================================================


# [common] セクション
class CommonConfig(BaseModel):
    log_dir: str = Field(default="logs", description="ログディレクトリ")
    encode: str = Field(default="utf-8", description="ログファイルエンコード")
    tz_offset_hours: int = Field(default=9, description="タイムゾーン (JST)")

    def get_tz(self) -> datetime.timezone:
        return datetime.timezone(datetime.timedelta(hours=self.tz_offset_hours))


# [devices] セクション
class DevicesConfig(BaseModel):
    # [devices] 直下のキー
    gm10_visa: str = Field(
        default="TCPIP0::192.168.x.x::34434::SOCKET", description="Logger (gm10)"
    )
    hps_visa: str = Field(
        default="TCPIP0::192.168.x.x::2268::SOCKET", description="Heater Power Supply (pfr_100l50)"
    )
    aps_visa: str = Field(
        default="TCPIP0::192.168.x.x::2268::SOCKET", description="AMD Power Supply (pfr_100l50)"
    )
    pwux_com_port: int = Field(default=0, description="PWUX (Temp) COMポート番号")
    ibeam_com_port: int = Field(default=0, description="Laser (ibeam) COMポート番号")

    # ネストされたテーブル
    gm10: GM10Config = Field(default_factory=GM10Config, description="Logger (gm10)")
    hps: PFR100l50Config = Field(default_factory=PFR100l50Config, description="Heater Power Supply")
    amd: PFR100l50Config = Field(default_factory=PFR100l50Config, description="AMD Power Supply")
    ibeam: IBeamConfig = Field(default_factory=IBeamConfig, description="Toptica IBeam laser")


# ======================================================================================


class AppConfig(BaseModel):
    common: CommonConfig = Field(default_factory=CommonConfig)
    devices: DevicesConfig = Field(default_factory=DevicesConfig)

    @classmethod
    def load(cls, path: str | Path = "config.toml") -> "AppConfig":
        path_obj = Path(path)

        # ファイルが存在しない場合
        if not path_obj.exists():
            print(f"設定ファイルが見つかりません: {path} -> 新規作成します")
            default_config = cls()  # デフォルト値で初期化
            default_config.save(path)  # ファイルを作成しておく
            return default_config

        # ファイルが存在する場合
        try:
            with path_obj.open("rb") as f:
                data = tomllib.load(f)

            return cls.model_validate(data)

        except Exception as e:  # noqa: BLE001
            print(f"エラー: 設定ファイルの読み込みまたは検証に失敗しました: {e}")
            return cls()

    def save(self, path: Path | str = "config.toml") -> None:
        """設定ファイルを保存。ファイルがない場合は新規作成"""
        path_obj = Path(path)
        new_data = self.model_dump()

        try:
            if path_obj.exists():
                # 既存ファイルがある場合は読み込み
                with path_obj.open("r", encoding="utf-8") as f:
                    doc = tomlkit.load(f)
                self._recursive_update(doc, new_data)

            else:
                # 新規作成
                doc = self._generate_new_document()

            # 書き込み
            with path_obj.open("w", encoding="utf-8") as f:
                tomlkit.dump(doc, f)

        except Exception as e:
            print(f"Config saving failed: {e}")
            raise

    def _generate_new_document(self) -> tomlkit.TOMLDocument:
        """自身のPydantic定義を元に、コメント付きのTOMLドキュメントを生成する"""
        doc = tomlkit.document()
        self._append_fields_with_comments(doc, self)
        return doc

    def _append_fields_with_comments(
        self, container: Table | tomlkit.TOMLDocument, model_instance: BaseModel
    ) -> None:
        """descriptionをコメントに設定しつつファイル構成"""
        for field_name, field_info in model_instance.model_fields.items():
            value = getattr(model_instance, field_name)

            if isinstance(value, BaseModel):
                # --- ネストされたモデル (セクション) の場合 ---
                # 新しいテーブル(セクション)を作成
                table = tomlkit.table()

                # 再帰的に中身を追加
                self._append_fields_with_comments(table, value)

                # コンテナに追加
                container.add(field_name, table)

                # セクション自体のコメント
                if field_info.description:
                    container[field_name].comment(field_info.description)

            else:
                # --- 通常の値の場合 ---
                container.add(field_name, value)

                # Field(description="...") があればコメントを追加
                if field_info.description:
                    container[field_name].comment(field_info.description)

    def _recursive_update(self, doc: dict | tomlkit.TOMLDocument, new_data: dict) -> None:
        """tomlkitのオブジェクト構造(コメント情報など)を壊さないように、辞書全体を置換せず、キーごとに値をセットする"""
        for key, value in new_data.items():
            # キーが存在し、かつ双方が辞書(セクション)の場合は再帰的に更新
            if key in doc and isinstance(doc[key], dict) and isinstance(value, dict):
                self._recursive_update(doc[key], value)
            else:
                # 値を更新 (tomlkitがフォーマットを維持してくれる)
                doc[key] = value
