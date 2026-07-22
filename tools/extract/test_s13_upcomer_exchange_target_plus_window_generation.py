from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.extract import build_s13_upcomer_exchange_target_plus_window_generation as builder


class S13TargetPlusWindowGenerationTests(unittest.TestCase):
    def test_case_specs_target_plus_times(self) -> None:
        expected = {
            "salt_2": ("7915", "7916"),
            "salt_3": ("7618", "7619"),
            "salt_4": ("10000", "10001"),
        }
        self.assertEqual({case.case_id: (case.restart_time_s, case.target_plus_time_s) for case in builder.CASES}, expected)

    def test_patch_control_dict_sets_target_plus_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "controlDict"
            path.write_text(
                "\n".join(
                    [
                        "startFrom       startTime;",
                        "stopAt          endTime;",
                        "endTime         10000;",
                        "writeControl    timeStep;",
                        "writeInterval   20;",
                        "purgeWrite      21;",
                        "timeFormat      fixed;",
                        "timePrecision   6;",
                    ]
                )
                + "\n"
            )
            builder.patch_control_dict(path, "10001")
            values = builder.control_values(
                path,
                ["startFrom", "stopAt", "endTime", "writeControl", "writeInterval", "purgeWrite", "timeFormat", "timePrecision"],
            )
        self.assertEqual(values["startFrom"], "latestTime")
        self.assertEqual(values["endTime"], "10001")
        self.assertEqual(values["writeControl"], "adjustableRunTime")
        self.assertEqual(values["writeInterval"], "1")
        self.assertEqual(values["purgeWrite"], "0")

    def test_copy_items_include_coded_function_cache(self) -> None:
        self.assertIn("dynamicCode", builder.COPY_ITEMS)
        self.assertIn("system", builder.COPY_ITEMS)
        self.assertIn("constant", builder.COPY_ITEMS)


if __name__ == "__main__":
    unittest.main()
