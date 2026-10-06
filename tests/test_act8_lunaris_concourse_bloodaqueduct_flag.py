import json
import unittest
from pathlib import Path

from src.ui.settings_dialog import _flag_guide_header, _mini_navi_flag_section_title
from src.utils.guide_data import get_zone_guide


FLAG_KEY = "act8_bloodaqueduct_enter"


class Act8LunarisConcourseBloodAqueductFlagTest(unittest.TestCase):
    def test_editors_label_flag_guide_as_standard_route_only(self):
        self.assertEqual(
            _flag_guide_header("act8_area14"),
            '🚩 Flag-specific guide (standard route, when the flags below are set)',
        )
        self.assertEqual(
            _mini_navi_flag_section_title("act8_area14", FLAG_KEY),
            f"Standard route, when flag is set: {FLAG_KEY}",
        )

    def test_standard_route_has_blood_aqueduct_flag_frame(self):
        guide_data = json.loads(Path("guide_data.json").read_text(encoding="utf-8"))
        flags = guide_data["act8_area14"]["visits"]["1"].get("flags", {})
        self.assertIn(FLAG_KEY, flags)
        self.assertIn("浴場", flags[FLAG_KEY]["objective"])
        self.assertIn("浴場", flags[FLAG_KEY]["mini_navi"]["text"])

    def test_flag_guide_is_used_only_on_standard_route(self):
        guide_data = {
            "act8_area14": {
                "visits": {
                    "1": {
                        "objective": "standard default",
                        "flags": {FLAG_KEY: {"objective": "after blood aqueduct"}},
                    },
                    "2": {"objective": "standard visit 2"},
                },
                "routes": {
                    "underbelly": {
                        "visits": {"1": {"objective": "underbelly default"}}
                    }
                },
            }
        }

        standard = get_zone_guide(
            guide_data,
            "act8_area14",
            visit=2,
            config={"poe1_route_act8": "standard"},
            active_flags={FLAG_KEY},
        )
        underbelly = get_zone_guide(
            guide_data,
            "act8_area14",
            config={"poe1_route_act8": "underbelly"},
            active_flags={FLAG_KEY},
        )

        self.assertEqual(standard["objective"], "after blood aqueduct")
        self.assertEqual(underbelly["objective"], "underbelly default")

    def test_blood_aqueduct_entry_sets_progress_flag(self):
        source = Path("src/ui/main_window.py").read_text(encoding="utf-8")
        self.assertIn('if zone_id == "act8_area17":', source)
        self.assertIn('self.set_progress_flag("act8_bloodaqueduct_enter")', source)


if __name__ == "__main__":
    unittest.main()
