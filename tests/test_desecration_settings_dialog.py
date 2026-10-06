from PySide6.QtCore import QObject, QRect, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QDialog, QGroupBox, QLabel, QScrollArea

from src.poetore.poe2.ndlocr_pack import PackStatus
from src.ui.desecration_settings_dialog import (
    DEFAULT_EXAMPLE_IMAGE_PATH,
    EXAMPLE_POPUP_IMAGE_SIZE,
    EXAMPLE_POPUP_SIZE,
    DesecrationRegionSelector,
    DesecrationSettingsDialog,
)


def test_desecration_settings_uses_poetore_dialog_theme_and_footer_roles(qtbot):
    dialog = DesecrationSettingsDialog()
    qtbot.addWidget(dialog)

    assert dialog.property("dialogTheme") == "poetore"
    assert dialog.property("dialogAccent") == "#65FFCA"
    assert dialog.title_label.property("uiRole") == "title"
    assert dialog.title_label.text() == 'Abyss Desecrated Mod Tier Check Settings'
    assert dialog.cancel_button.property("buttonRole") == "secondary"
    assert dialog.save_button.property("buttonRole") == "primary"
    assert dialog.footer_layout.itemAt(1).widget() is dialog.cancel_button
    assert dialog.footer_layout.itemAt(2).widget() is dialog.save_button
    assert "#65FFCA" in dialog.styleSheet()
    assert "#B0FF7B" not in dialog.styleSheet()
    assert dialog.enabled_checkbox.styleSheet() == ""
    assert dialog.show_ranges_checkbox.styleSheet() == ""


def test_desecration_region_selector_keeps_protected_game_overlay_style(qtbot):
    selector = DesecrationRegionSelector(QRect(100, 200, 1000, 800))
    qtbot.addWidget(selector)

    assert selector.property("dialogTheme") is None
    assert selector.styleSheet() == "font-size: 36px; font-weight: bold;"


class FakePackController(QObject):
    status_changed = Signal(object)

    def __init__(self, status):
        super().__init__()
        self.status = status
        self.retry_count = 0

    def retry(self):
        self.retry_count += 1


def test_desecration_settings_defaults_to_alt_r_and_keeps_open_region_optional(qtbot):
    dialog = DesecrationSettingsDialog(
        screen_reading_enabled=True,
        client_rect_getter=lambda: QRect(0, 0, 1920, 1080),
    )
    qtbot.addWidget(dialog)
    config, hotkey, enabled = dialog.settings()
    assert hotkey == "alt+r"
    assert enabled is True
    assert "inventory_open_region" not in config
    assert (
        "capture shortcut disabled"
        in dialog._section_widgets["inventory_open_region"][0].text()
    )


def test_desecration_settings_preserves_two_independent_regions(qtbot):
    opened = {"left": 0.2, "top": 0.1, "right": 0.7, "bottom": 0.5}
    closed = {"left": 0.3, "top": 0.2, "right": 0.8, "bottom": 0.6}
    dialog = DesecrationSettingsDialog(
        desecration_config={
            "inventory_open_region": opened,
            "inventory_closed_region": closed,
        },
    )
    qtbot.addWidget(dialog)
    config, _hotkey, _enabled = dialog.settings()
    assert config["inventory_open_region"] == opened
    assert config["inventory_closed_region"] == closed


def test_desecration_hotkey_accepts_ctrl_alt_shift_combinations(qtbot):
    dialog = DesecrationSettingsDialog(hotkey="ctrl+alt+shift+r")
    qtbot.addWidget(dialog)

    widget = dialog.hotkey_widget
    assert widget.ctrl_button.isChecked()
    assert widget.alt_button.isChecked()
    assert widget.shift_button.isChecked()
    assert not widget.no_modifier_button.isChecked()
    assert dialog.settings()[1] == "ctrl+alt+shift+r"


def test_desecration_settings_saves_optional_tier_ranges(qtbot):
    dialog = DesecrationSettingsDialog()
    qtbot.addWidget(dialog)
    assert dialog.show_ranges_checkbox.isChecked()
    assert dialog.settings()[0]["show_tier_ranges"] is True

    dialog.show_ranges_checkbox.setChecked(False)
    assert dialog.settings()[0]["show_tier_ranges"] is False


def test_desecration_settings_groups_required_flow_before_optional_display(qtbot):
    dialog = DesecrationSettingsDialog()
    qtbot.addWidget(dialog)

    groups = dialog.findChildren(QGroupBox)
    assert [group.title() for group in groups] == [
        '1. Basic Settings',
        '2. High-Accuracy OCR',
        '3. Capture Area',
        '4. Display Settings',
    ]
    assert dialog.findChild(QScrollArea, "desecrationSettingsScroll") is not None

    basic = dialog.findChild(QGroupBox, "basicSettingsGroup")
    ranges = dialog.findChild(QGroupBox, "readRegionsGroup")
    display = dialog.findChild(QGroupBox, "displaySettingsGroup")
    assert basic.isAncestorOf(dialog.enabled_checkbox)
    assert basic.isAncestorOf(dialog.hotkey_widget)
    assert ranges.isAncestorOf(dialog.findChild(QLabel, "inventory_open_regionTitle"))
    assert ranges.isAncestorOf(dialog.example_thumbnail)
    assert display.isAncestorOf(dialog.show_ranges_checkbox)
    assert dialog.findChild(QGroupBox, "exampleGroup") is None


def test_desecration_settings_shows_pack_download_progress_and_ready_state(qtbot):
    controller = FakePackController(PackStatus("downloading", done=1, total=4))
    dialog = DesecrationSettingsDialog(ocr_pack_controller=controller)
    qtbot.addWidget(dialog)

    assert dialog.ocr_pack_status.text().endswith("25%")
    assert not dialog.ocr_pack_progress.isHidden()
    assert dialog.ocr_pack_progress.value() == 25

    controller.status = PackStatus("ready")
    controller.status_changed.emit(controller.status)
    assert "is available" in dialog.ocr_pack_status.text()
    assert not dialog.ocr_pack_progress.isVisible()


def test_desecration_settings_shows_retry_only_after_pack_error(qtbot):
    controller = FakePackController(PackStatus("error", "network"))
    dialog = DesecrationSettingsDialog(ocr_pack_controller=controller)
    qtbot.addWidget(dialog)

    assert 'Standard reading still works' in dialog.ocr_pack_status.text()
    assert not dialog.ocr_pack_retry.isHidden()
    dialog.ocr_pack_retry.click()
    assert controller.retry_count == 1


def test_desecration_settings_preserves_explicitly_disabled_tier_ranges(qtbot):
    dialog = DesecrationSettingsDialog(desecration_config={"show_tier_ranges": False})
    qtbot.addWidget(dialog)

    assert not dialog.show_ranges_checkbox.isChecked()
    assert dialog.settings()[0]["show_tier_ranges"] is False


def test_desecration_settings_explains_required_and_closed_regions(qtbot):
    dialog = DesecrationSettingsDialog()
    qtbot.addWidget(dialog)
    required = dialog.findChild(QLabel, "desecrationRequiredLabel")
    closed_note = dialog.findChild(QLabel, "desecrationClosedRegionNote")
    instruction = dialog.findChild(QLabel, "desecrationRegionInstruction")
    warning = dialog.findChild(QLabel, "screenSizeRegionWarning")
    assert required.text() == ' (required)'
    assert required.property("state") == "warning"
    assert "#F6C85F" in dialog.styleSheet()
    assert closed_note.text() == '* Closing the inventory shifts the position and causes reading to fail'
    assert instruction.text().endswith(
        'When reading, the "inventory open" area is tried first; if that fails, '
        'the "inventory closed" area is tried.'
    )
    assert warning.text() == (
        'If you change the PoE2 window size, positions shift and you will need to set this again.'
    )


def test_desecration_settings_warns_that_screen_reading_must_be_enabled(qtbot):
    dialog = DesecrationSettingsDialog()
    qtbot.addWidget(dialog)

    hint = dialog.findChild(QLabel, "screenReadingEnableRequiredHint")
    assert hint.text() == '* Check this box to use the feature'
    assert hint.property("state") == "warning"
    assert "#F6C85F" in dialog.styleSheet()
    assert "font-weight: 600" in dialog.styleSheet()


def test_desecration_default_example_image_is_bundled_and_loadable():
    QApplication.instance() or QApplication([])
    pixmap = QPixmap(str(DEFAULT_EXAMPLE_IMAGE_PATH))

    assert DEFAULT_EXAMPLE_IMAGE_PATH.is_file()
    assert not pixmap.isNull()
    assert pixmap.width() == 2577
    assert pixmap.height() == 698


def test_desecration_example_popup_image_is_one_and_a_half_times_larger(
    qtbot, monkeypatch
):
    captured = {}

    def capture_popup(popup):
        captured["popup"] = popup
        return QDialog.Rejected

    monkeypatch.setattr(QDialog, "exec", capture_popup)
    dialog = DesecrationSettingsDialog()
    qtbot.addWidget(dialog)

    dialog._show_example_popup()

    popup = captured["popup"]
    image = popup.findChild(QLabel, "desecrationExamplePopupImage")
    assert popup.size() == EXAMPLE_POPUP_SIZE
    assert popup.property("dialogTheme") == "poetore"
    assert EXAMPLE_POPUP_IMAGE_SIZE.width() == 860 * 1.5
    assert EXAMPLE_POPUP_IMAGE_SIZE.height() == 630 * 1.5
    assert image.pixmap().width() == 1290
