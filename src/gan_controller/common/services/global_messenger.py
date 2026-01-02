from PySide6.QtCore import QObject, Signal


class GlobalMessenger(QObject):
    """アプリケーション全体で共有するシグナルを管理するメッセンジャー (Singleton)"""

    _instance = None
    _initialized = False

    # ステータスバーへの表示要求 (メッセージ, 表示時間ms)
    status_message_requested = Signal(str, int)

    def __new__(cls) -> "GlobalMessenger":
        """インスタンスがなければ生成し、あれば既存のものを返す"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初期化処理 (シングルトンなので1回だけ実行されるようにガード)"""
        # 既に初期化済みなら何もしない (ガードが無いとうまくいかない)
        if self._initialized:
            return

        super().__init__()
        self._initialized = True

    def show_status(self, message: str, timeout_ms: int = 5000) -> None:
        """ステータスバーへの表示をリクエストするヘルパーメソッド"""
        self.status_message_requested.emit(message, timeout_ms)
