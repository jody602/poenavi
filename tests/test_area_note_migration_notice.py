from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication, QMainWindow

from src.ui.main_window import MainWindow
from src.utils.config_manager import ConfigManager


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def _window(config):
    window = MainWindow.__new__(MainWindow)
    QMainWindow.__init__(window)
    window.config = config
    return window


def test_area_note_migration_notice_is_shown_and_saved_once(qapp):
    window = _window({})
    message = MagicMock()

    with (
        patch("src.ui.main_window.QMessageBox", return_value=message),
        patch("src.ui.main_window.ConfigManager.save_config") as save_config,
    ):
        window._show_area_note_migration_notice_once()

    message.setWindowTitle.assert_called_once_with('📝 About Area Notes')
    shown_text = message.setText.call_args.args[0]
    assert "the guide data for each area\ncan no longer be edited" in shown_text
    assert "so PoENavi's auto-update works correctly" in shown_text
    assert "add notes to each area.\n\nSorry for the trouble, but if you edited guides before" in shown_text
    assert "JSON files in your old PoENavi folder" in shown_text
    assert "future updates will not erase your area notes" in shown_text
    message.exec.assert_called_once_with()
    assert window.config["area_note_migration_notice_shown"] is True
    save_config.assert_called_once_with(window.config)


def test_area_note_migration_notice_is_not_shown_again(qapp):
    window = _window({"area_note_migration_notice_shown": True})

    with (
        patch("src.ui.main_window.QMessageBox") as message_box,
        patch("src.ui.main_window.ConfigManager.save_config") as save_config,
    ):
        window._show_area_note_migration_notice_once()

    message_box.assert_not_called()
    save_config.assert_not_called()


def test_new_install_defaults_to_notice_already_shown(tmp_path, monkeypatch):
    monkeypatch.setenv(ConfigManager.ENV_USER_DATA_DIR, str(tmp_path / "user-data"))

    config = ConfigManager.load_config()

    assert config["area_note_migration_notice_shown"] is True


def test_existing_config_without_notice_flag_is_marked_for_one_time_notice(tmp_path, monkeypatch):
    user_data = tmp_path / "user-data"
    user_data.mkdir()
    (user_data / "config.json").write_text('{"setup_completed": true}', encoding="utf-8")
    monkeypatch.setenv(ConfigManager.ENV_USER_DATA_DIR, str(user_data))

    config = ConfigManager.load_config()

    assert config["area_note_migration_notice_shown"] is False
