import json
import unittest
from pathlib import Path

from src.ui.settings_dialog import _flag_guide_header, _mini_navi_flag_section_title
from src.utils.guide_data import get_zone_guide


FLAG_KEY = "act8_lunaristemple2_enter+act8_solaristemple2_enter"


class Act8HarbourBridgeStandardFlagsTest(unittest.TestCase):
    def test_editors_label_flag_guide_as_standard_route_only(self):
        self.assertEqual(
            _flag_guide_header("act8_area13"),
            '🚩 Flag-specific guide (standard route, when the flags below are set)',
        )
        self.assertEqual(
            _mini_navi_flag_section_title("act8_area13", FLAG_KEY),
            f"Standard route, when flag is set: {FLAG_KEY}",
        )

    def test_other_zone_flag_labels_are_unchanged(self):
        self.assertEqual(_flag_guide_header("act2_area7"), '🚩 Flag-specific guide')
        self.assertEqual(
            _mini_navi_flag_section_title("act2_area7", "some_flag"),
            "By flag: some_flag",
        )

    def test_standard_route_has_both_temples_flag_frame(self):
        guide_data = json.loads(Path("guide_data.json").read_text(encoding="utf-8"))
        flags = guide_data["act8_area13"]["visits"]["1"].get("flags", {})
        self.assertIn(FLAG_KEY, flags)
        self.assertIsInstance(flags[FLAG_KEY], dict)

    def test_composite_flag_guide_is_used_only_on_standard_route(self):
        guide_data = {
            "act8_area13": {
                "visits": {
                    "1": {
                        "objective": "standard default",
                        "flags": {FLAG_KEY: {"objective": "standard both temples"}},
                    }
                },
                "routes": {
                    "underbelly": {
                        "visits": {"1": {"objective": "underbelly default"}}
                    }
                },
            }
        }
        both_flags = {"act8_lunaristemple2_enter", "act8_solaristemple2_enter"}

        standard = get_zone_guide(
            guide_data,
            "act8_area13",
            config={"poe1_route_act8": "standard"},
            active_flags=both_flags,
        )
        underbelly = get_zone_guide(
            guide_data,
            "act8_area13",
            config={"poe1_route_act8": "underbelly"},
            active_flags=both_flags,
        )

        self.assertEqual(standard["objective"], "standard both temples")
        self.assertEqual(underbelly["objective"], "underbelly default")


if __name__ == "__main__":
    unittest.main()
