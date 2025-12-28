from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)


class NEAActLogSettingPanel(QGroupBox):
    """シーケンス設定用ウィジェット"""

    chk_date_update: QCheckBox
    chk_major_update: QCheckBox
    comment_edit: QLineEdit

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Log Setting", parent)

        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        checks_layout = QHBoxLayout()
        self.chk_date_update = QCheckBox("日付フォルダ更新")
        self.chk_major_update = QCheckBox("メジャー番号更新")
        checks_layout.addWidget(self.chk_date_update)
        checks_layout.addWidget(self.chk_major_update)
        checks_layout.addStretch()

        comment_layout = QHBoxLayout()
        self.comment_edit = QLineEdit()
        self.comment_edit.setPlaceholderText("Comment...")
        comment_layout.addWidget(QLabel("コメント :"))
        comment_layout.addWidget(self.comment_edit)

        main_layout.addLayout(checks_layout)
        main_layout.addLayout(comment_layout)
