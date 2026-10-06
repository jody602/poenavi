import pytest
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from src.ui import app_info_widget
from src.ui.settings_dialog import SettingsDialog


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def test_patreon_support_button_opens_configured_url(monkeypatch, qapp):
    opened_urls = []
    monkeypatch.setattr(app_info_widget.webbrowser, "open", opened_urls.append)
    dialog = SettingsDialog(current_config={})

    buttons = {
        button.text(): button
        for button in dialog.findChildren(QPushButton)
    }
    assert 'Support on OFUSE' in buttons
    assert 'Support on Ko-fi' in buttons
    assert 'Support on Patreon' in buttons

    buttons['Support on Patreon'].click()

    assert opened_urls == ["https://www.patreon.com/cw/Buri8857"]
    dialog.close()


def test_app_information_update_button_uses_injected_callback(qapp):
    calls = []
    dialog = SettingsDialog(
        current_config={},
        update_check_callback=lambda: calls.append("checked"),
    )

    button = dialog.findChild(QPushButton, "appInfoUpdateButton")
    assert button is not None
    assert button.text() == 'Check for Updates'
    assert button.isEnabled()

    button.click()

    assert calls == ["checked"]
    dialog.close()


def test_app_information_displays_ndlocr_attribution(qapp):
    dialog = SettingsDialog(current_config={})

    label = dialog.findChild(QLabel, "ndlocrLicenseLabel")
    assert label is not None
    assert "NDLOCR-Lite 1.3.1" in label.text()
    assert "National Diet Library" in label.text()
    assert "CC BY 4.0" in label.text()
    assert "Not endorsed by or affiliated with" in label.text()
    dialog.close()
