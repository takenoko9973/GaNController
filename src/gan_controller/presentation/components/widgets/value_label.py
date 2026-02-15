from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget

# フォーマッター型定義
FormatterType = str | Callable[[Any], str]


class ValueLabel(QLabel):
    """数値や時間を表示するための枠付きラベル"""

    def __init__(
        self,
        value: Any = "",  # noqa: ANN401
        formatter: FormatterType | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.setStyleSheet("""
            background-color: white;
            border: 1px solid #ccc;
            padding: 2px 4px;
            font-family: Monospace;
        """)

        self._default_formatter = formatter
        self.setValue(value)

    def setValue(self, value: Any, formatter: FormatterType | None = None) -> None:  # noqa: ANN401, N802
        # 表示形式に特別な指定があれば、それでフォーマット
        fmt = formatter if formatter is not None else self._default_formatter

        if callable(fmt):
            # 関数やラムダ式パターン
            # value をそのまま関数に渡して文字列化を委譲
            text = fmt(value)

        elif isinstance(fmt, str) and fmt:
            # フォーマット指定子
            try:
                text = format(value, fmt)
            except ValueError:
                text = str(value)

        else:
            # 指定なし
            text = str(value)

        self.setText(text)
