from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from gan_controller.features.heat_cleaning.schemas.config import HCLogConfig


class HCLogSettingPanel(QGroupBox):
    """シーケンス設定用ウィジェット"""

    chk_date_update: QCheckBox
    chk_major_update: QCheckBox
    comment_edit: QLineEdit

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Log Setting", parent)

        self._init_ui()

    def _init_ui(self) -> None:
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

    # =============================================================================

    def get_config(self) -> HCLogConfig:
        return HCLogConfig(
            update_date_folder=self.chk_date_update.isChecked(),
            update_major_number=self.chk_major_update.isChecked(),
            comment=self.comment_edit.text(),
        )

    def set_config(self, config: HCLogConfig) -> None:
        self.chk_date_update.setChecked(config.update_date_folder)
        self.chk_major_update.setChecked(config.update_major_number)
        self.comment_edit.setText(config.comment)
