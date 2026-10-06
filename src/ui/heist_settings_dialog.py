"""PoE1 Grand Heist reward OCR settings dialog."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.ui.dialog_theme import POETORE_DIALOG_THEME, apply_dialog_theme
from src.ui.expedition_settings_dialog import ClickableImageLabel
from src.ui.high_accuracy_ocr_pack_group import HighAccuracyOcrPackGroup
from src.ui.settings_dialog import AutoHideHotkeyWidget

DEFAULT_EXAMPLE_IMAGE_PATH = (
    Path(__file__).resolve().parents[2]
    / "assets"
    / "images"
    / "heist_curio_manual_selection_example.png"
)


class HeistSettingsDialog(QDialog):
    """Configure the opt-in manual-selection Heist reward reader."""

    def __init__(
        self,
        parent=None,
        *,
        enabled: bool = False,
        hotkey: str = "alt+e",
        example_image_path=None,
        ocr_pack_controller=None,
    ):
        super().__init__(parent)
        self._example_image_path = Path(
            example_image_path or DEFAULT_EXAMPLE_IMAGE_PATH
        )
        self._ocr_pack_controller = ocr_pack_controller
        self.theme = POETORE_DIALOG_THEME
        self.setWindowTitle("Heist Reward OCR Settings")
        self.setMinimumSize(620, 700)
        apply_dialog_theme(self, self.theme)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 12)
        root.setSpacing(10)
        self.title_label = QLabel("Heist Reward OCR Settings")
        self.title_label.setProperty("uiRole", "title")
        root.addWidget(self.title_label)

        scroll = QScrollArea()
        scroll.setObjectName("heistSettingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content_widget = QWidget()
        content = QVBoxLayout(content_widget)
        content.setContentsMargins(4, 4, 4, 4)
        content.setSpacing(10)
        scroll.setWidget(content_widget)
        root.addWidget(scroll, 1)

        basic_group, basic = self._section_group("1. Basic Settings", "basicSettingsGroup")
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(8)
        self.enabled_checkbox = QCheckBox("Enable Heist reward OCR")
        self.enabled_checkbox.setChecked(bool(enabled))
        toggle_row.addWidget(self.enabled_checkbox)
        self.enable_required_hint = QLabel("* OCR and the hotkey only run while enabled")
        self.enable_required_hint.setObjectName("heistEnableRequiredHint")
        self.enable_required_hint.setProperty("uiRole", "muted")
        toggle_row.addWidget(self.enable_required_hint)
        toggle_row.addStretch()
        basic.addLayout(toggle_row)

        form = QFormLayout()
        form.setContentsMargins(0, 2, 0, 0)
        self.hotkey_widget = AutoHideHotkeyWidget(
            hotkey,
            theme=self.theme,
            allow_no_modifier=True,
            allow_multiple_modifiers=True,
            allow_shift=True,
        )
        self.hotkey_widget.key_button.setStyleSheet("")
        form.addRow("Capture shortcut:", self.hotkey_widget)
        basic.addLayout(form)
        content.addWidget(basic_group)

        pack_group = HighAccuracyOcrPackGroup(self._ocr_pack_controller, self)
        self.ocr_pack_status = pack_group.status_label
        self.ocr_pack_progress = pack_group.progress_bar
        self.ocr_pack_retry = pack_group.retry_button
        content.addWidget(pack_group)

        usage_group, usage = self._section_group("3. How to Capture", "readMethodGroup")
        instruction = QLabel(
            "After pressing the shortcut, drag from top-left to bottom-right over the reward name, "
            "base type, and all blue mods in the display panel.\n"
            "The selection confirms automatically when you release. Press Esc to cancel."
        )
        instruction.setObjectName("heistSelectionInstruction")
        instruction.setProperty("uiRole", "muted")
        instruction.setWordWrap(True)
        usage.addWidget(instruction)

        warning = QLabel(
            "For Rogue's Trinkets, include everything down to the last blue mod. For other rewards, "
            "including the name and base type is enough."
        )
        warning.setObjectName("heistSelectionWarning")
        warning.setProperty("state", "warning")
        warning.setWordWrap(True)
        usage.addWidget(warning)

        example_heading = QHBoxLayout()
        example_title = QLabel("Area Example")
        example_title.setObjectName("heistExampleHeading")
        example_title.setProperty("uiRole", "section")
        example_heading.addWidget(example_title)
        hint = QLabel("* Click the image to enlarge it")
        hint.setObjectName("heistExampleHint")
        hint.setProperty("uiRole", "muted")
        example_heading.addWidget(hint)
        example_heading.addStretch()
        usage.addLayout(example_heading)

        self.example_thumbnail = ClickableImageLabel()
        self.example_thumbnail.setObjectName("heistExampleThumbnail")
        self.example_thumbnail.setProperty("uiRole", "surface")
        self.example_thumbnail.setAlignment(Qt.AlignCenter)
        self.example_thumbnail.setFixedHeight(150)
        self.example_thumbnail.setCursor(Qt.PointingHandCursor)
        self.example_thumbnail.clicked.connect(self._show_example_popup)
        usage.addWidget(self.example_thumbnail)
        self._load_example_thumbnail()
        content.addWidget(usage_group)
        content.addStretch()

        footer = QHBoxLayout()
        footer.addStretch()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setProperty("buttonRole", "secondary")
        self.cancel_button.clicked.connect(self.reject)
        self.save_button = QPushButton("Save")
        self.save_button.setProperty("buttonRole", "primary")
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.accept)
        footer.addWidget(self.cancel_button)
        footer.addWidget(self.save_button)
        root.addLayout(footer)

        for widget_type in (QCheckBox, QGroupBox, QPushButton, QScrollArea):
            for widget in self.findChildren(widget_type):
                widget.setStyleSheet("")

    @staticmethod
    def _section_group(title: str, object_name: str):
        group = QGroupBox(title)
        group.setObjectName(object_name)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.setSpacing(8)
        return group, layout

    def settings(self) -> tuple[str, bool]:
        return self.hotkey_widget.key_text, self.enabled_checkbox.isChecked()

    def _load_example_thumbnail(self) -> None:
        pixmap = QPixmap(str(self._example_image_path))
        if pixmap.isNull():
            self.example_thumbnail.setText("Could not load the area example image.")
            return
        self.example_thumbnail.setPixmap(
            pixmap.scaled(QSize(550, 138), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        self.example_thumbnail.setToolTip("Click to enlarge")

    def _show_example_popup(self) -> None:
        popup = QDialog(self)
        popup.setWindowTitle("Heist Reward Area Example")
        popup.resize(900, 520)
        apply_dialog_theme(popup, self.theme)
        layout = QVBoxLayout(popup)
        guide = QLabel(
            "Select from the reward name and base type down to the last blue mod, like this."
        )
        guide.setProperty("uiRole", "muted")
        guide.setWordWrap(True)
        layout.addWidget(guide)
        image = QLabel()
        image.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(str(self._example_image_path))
        if pixmap.isNull():
            image.setText("Could not load the area example image.")
        else:
            image.setPixmap(
                pixmap.scaled(
                    QSize(850, 400), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
        layout.addWidget(image)
        close = QPushButton("Close")
        close.setProperty("buttonRole", "secondary")
        close.clicked.connect(popup.accept)
        layout.addWidget(close, alignment=Qt.AlignRight)
        popup.exec()
