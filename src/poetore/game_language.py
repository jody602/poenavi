"""Game client language used when reading text from the PoE2 screen."""

from __future__ import annotations

ENGLISH = "en"
JAPANESE = "ja"
DEFAULT_GAME_LANGUAGE = ENGLISH
GAME_LANGUAGE_LABELS = {ENGLISH: "English", JAPANESE: "Japanese"}
_OCR_LANGUAGE_TAGS = {ENGLISH: "en-US", JAPANESE: "ja-JP"}


def normalize_game_language(value) -> str:
    value = str(value or "").strip().casefold()
    return value if value in _OCR_LANGUAGE_TAGS else DEFAULT_GAME_LANGUAGE


def screen_reading_game_language(config) -> str:
    """Return the configured client language for Expedition/Abyss screen reading."""
    poetore = config.get("poetore", {}) if isinstance(config, dict) else {}
    poetore = poetore if isinstance(poetore, dict) else {}
    screen_reading = poetore.get("screen_reading", {})
    screen_reading = screen_reading if isinstance(screen_reading, dict) else {}
    return normalize_game_language(screen_reading.get("game_language"))


def ocr_language_tag(language: str) -> str:
    return _OCR_LANGUAGE_TAGS[normalize_game_language(language)]
