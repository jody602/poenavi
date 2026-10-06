"""English PoE2 client support for Expedition reward and Abyss desecration screen reading."""

import pytest
from PySide6.QtWidgets import QApplication

from src.poetore.expedition_rewards import SafeRewardNameResolver, load_reward_alias_bundle
from src.poetore.game_language import (
    ENGLISH,
    JAPANESE,
    ocr_language_tag,
    screen_reading_game_language,
)
from src.poetore.poe2 import desecration_tiers
from src.poetore.poe2.desecration_ocr import resolve_ocr_variants


@pytest.fixture
def english_tiers():
    desecration_tiers.set_text_language(ENGLISH)
    yield
    desecration_tiers.set_text_language(JAPANESE)


@pytest.fixture
def qapp():
    return QApplication.instance() or QApplication([])


def test_game_language_defaults_to_english_and_maps_to_ocr_tags():
    assert screen_reading_game_language({}) == ENGLISH
    assert screen_reading_game_language(
        {"poetore": {"screen_reading": {"game_language": "ja"}}}
    ) == JAPANESE
    assert screen_reading_game_language(
        {"poetore": {"screen_reading": {"game_language": "fr"}}}
    ) == ENGLISH
    assert ocr_language_tag(ENGLISH) == "en-US"
    assert ocr_language_tag(JAPANESE) == "ja-JP"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("3x Exalted Orb", "Exalted Orb"),
        ("lx Divine Orb", "Divine Orb"),
        ("2x Orb of Annulment", "Orb of Annulment"),
        ("Uncut Skill Gem (Level 19)", "Uncut Skill Gem (Level 19)"),
        ("1x Level 20 Uncut Spirit Gem", "Uncut Spirit Gem (Level 20)"),
    ],
)
def test_english_reward_names_resolve_to_trade_names(text, expected):
    aliases, version = load_reward_alias_bundle(language=ENGLISH)
    resolved = SafeRewardNameResolver(aliases, version).resolve(text)
    assert resolved is not None
    assert resolved[1] == expected


def test_english_reward_resolver_rejects_ambiguous_or_unknown_text():
    aliases, version = load_reward_alias_bundle(language=ENGLISH)
    resolver = SafeRewardNameResolver(aliases, version)
    # The level decides the price, so a gem without one must not be guessed.
    assert resolver.resolve("Uncut Skill Gem") is None
    assert resolver.resolve("some unrelated text") is None


def test_japanese_reward_names_still_resolve():
    aliases, version = load_reward_alias_bundle()
    resolved = SafeRewardNameResolver(aliases, version).resolve("3x 高貴なオーブ")
    assert resolved is not None and resolved[1] == "Exalted Orb"


def test_reward_dictionary_version_differs_per_language():
    assert load_reward_alias_bundle(language=ENGLISH)[1] != load_reward_alias_bundle()[1]


def test_english_desecration_choices_resolve_tiers_and_ranges(english_tiers):
    grouped = (
        ("58% increased Damage against Enemies with Fully Broken Armour",) * 4,
        ("60% increased Physical Damage",) * 4,
        ("Adds 18 to 28 Cold damage to Attacks",) * 4,
    )
    resolution = resolve_ocr_variants(grouped, ("one_hand_mace",))
    assert resolution.tiers_by_category["one_hand_mace"] == (1, 7, 6)
    assert resolution.ranges_by_category["one_hand_mace"] == (
        ("41–59%",), ("50–64%",), ("17–20", "26–32"),
    )


def test_english_desecration_handles_soft_wrapped_lines(english_tiers):
    result = desecration_tiers.resolve_desecration_choice_fuzzy(
        "58% increased Damage against Enemies\nwith Fully Broken Armour", "one_hand_mace",
    )
    assert result.tier == 1


def test_english_out_of_range_value_is_not_guessed(english_tiers):
    result = desecration_tiers.resolve_desecration_choice_fuzzy(
        "99% increased Damage against Enemies with Fully Broken Armour", "one_hand_mace",
    )
    assert result.tier is None and not result.tier_candidates


def test_switching_language_back_restores_japanese_matching(english_tiers):
    desecration_tiers.set_text_language(JAPANESE)
    result = desecration_tiers.resolve_desecration_choice_fuzzy(
        "完全アーマー破壊状態の敵に対するダメージが58%増加する", "one_hand_mace",
    )
    assert result.tier == 1
    desecration_tiers.set_text_language(ENGLISH)
    result = desecration_tiers.resolve_desecration_choice_fuzzy(
        "完全アーマー破壊状態の敵に対するダメージが58%増加する", "one_hand_mace",
    )
    assert result.tier is None


def test_settings_dialogs_expose_game_language(qapp):
    from src.ui.desecration_settings_dialog import DesecrationSettingsDialog
    from src.ui.expedition_settings_dialog import ExpeditionSettingsDialog

    expedition = ExpeditionSettingsDialog(game_language=JAPANESE)
    assert expedition.game_language() == JAPANESE
    expedition.game_language_combo.setCurrentIndex(
        expedition.game_language_combo.findData(ENGLISH)
    )
    assert expedition.game_language() == ENGLISH
    assert ExpeditionSettingsDialog().game_language() == ENGLISH
    desecration = DesecrationSettingsDialog()
    assert desecration.game_language() == ENGLISH
    expedition.close()
    desecration.close()
