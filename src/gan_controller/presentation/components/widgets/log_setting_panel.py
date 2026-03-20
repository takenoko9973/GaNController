from PySide6.QtCore import QEvent, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)


class CommonLogSettingPanel(QGroupBox):
    """ログ設定の共通UIコンポーネント"""

    _main_layout: QVBoxLayout

    chk_date_update: QCheckBox
    chk_major_update: QCheckBox
    comment_edit: QLineEdit

    next_num_label: QLabel
    _preview_refresh_timer: QTimer

    # 設定変更通知用シグナル
    config_changed = Signal()
    # プレビュー更新要求用シグナル
    preview_refresh_requested = Signal()

    def __init__(self, title: str = "Log Setting", parent: QWidget | None = None) -> None:
        super().__init__(title, parent)
        self._init_ui()
        self._init_signals()
        self._init_timer()

    def _init_ui(self) -> None:
        self._main_layout = QVBoxLayout(self)
        self.setLayout(self._main_layout)

        checks_layout = QHBoxLayout()
        self.chk_date_update = QCheckBox("日付フォルダ更新")
        self.chk_major_update = QCheckBox("メジャー番号更新")

        self.next_num_label = QLabel("0.0")
        self.next_num_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.next_num_label.setStyleSheet("""
            background-color: white;
            border: 1px solid #ccc;
            padding: 2px 4px;
            font-family: monospace;
        """)

        checks_layout.addWidget(self.chk_date_update)
        checks_layout.addWidget(self.chk_major_update)
        checks_layout.addStretch()
        checks_layout.addWidget(QLabel("Log Number :"))
        checks_layout.addWidget(self.next_num_label)

        comment_layout = QHBoxLayout()
        self.comment_edit = QLineEdit()
        self.comment_edit.setPlaceholderText("Comment...")
        comment_layout.addWidget(QLabel("コメント :"))
        comment_layout.addWidget(self.comment_edit)

        self._main_layout.addLayout(checks_layout)
        self._main_layout.addLayout(comment_layout)

    def _init_signals(self) -> None:
        self.chk_date_update.toggled.connect(self._on_changed)
        self.chk_major_update.toggled.connect(self._on_changed)

    def _on_changed(self) -> None:
        self.config_changed.emit()

    def _init_timer(self) -> None:
        self._preview_refresh_timer = QTimer(self)
        self._preview_refresh_timer.setInterval(3000)
        self._preview_refresh_timer.timeout.connect(self._emit_preview_refresh_if_needed)
        self._preview_refresh_timer.start()

    def _emit_preview_refresh_if_needed(self) -> None:
        if self.isVisible() and self.isEnabled():
            self.preview_refresh_requested.emit()

    def showEvent(self, event: QEvent) -> None:  # noqa: N802
        super().showEvent(event)
        self._emit_preview_refresh_if_needed()

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.EnabledChange and self.isEnabled():
            self._emit_preview_refresh_if_needed()

    def set_preview_text(self, text: str) -> None:
        """ログファイル名プレビューを設定"""
        self.next_num_label.setText(text)

    # =======================================================================================

    def insert_widget(self, index: int, widget: QWidget) -> None:
        """
        GroupBox内レイアウトの指定の行に挿入

        レイアウト
        0: Date/Major Checkboxes
        1: Comment
        """
        self._main_layout.insertWidget(index, widget)

    # =======================================================================================

    def get_values(self) -> dict:
        """現在のUIの値を辞書形式で返す"""
        return {
            "update_date_folder": self.chk_date_update.isChecked(),
            "update_major_number": self.chk_major_update.isChecked(),
            "comment": self.comment_edit.text(),
        }

    def set_values(self, update_date: bool, major_update: bool, comment: str) -> None:
        """値をUIにセットする"""
        self.blockSignals(True)
        self.chk_date_update.setChecked(update_date)
        self.chk_major_update.setChecked(major_update)
        self.comment_edit.setText(comment)
        self.blockSignals(False)

        self.config_changed.emit()
