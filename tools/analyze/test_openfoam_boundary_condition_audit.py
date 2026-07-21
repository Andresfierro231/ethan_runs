import unittest

from tools.analyze.build_openfoam_boundary_condition_audit import (
    iter_boundary_fields,
    numeric_close,
    parse_patch_blocks,
    restart_all_expected,
    scalar_for,
    value_for,
)


class OpenFoamBoundaryAuditTests(unittest.TestCase):
    def test_parse_root_boundary_blocks(self) -> None:
        text = """
        boundaryField
        {
            "wall_a"
            {
                type rcExternalTemperature;
                Q constant 12.5;
                thicknessLayers (0.001651 0.03556);
            }
            wall_b
            {
                type zeroGradient;
            }
        }
        """
        fields = iter_boundary_fields(text)
        self.assertEqual(len(fields), 1)
        patches = parse_patch_blocks(fields[0])
        self.assertEqual(set(patches), {"wall_a", "wall_b"})
        self.assertEqual(value_for(patches["wall_a"], "type"), "rcExternalTemperature")
        self.assertEqual(scalar_for(patches["wall_a"], "Q"), "12.5")

    def test_multiple_embedded_boundary_fields(self) -> None:
        text = """
        boundaryField
        {
            patch0
            {
                type externalTemperature;
            }
        }
        boundaryField
        {
            patch1
            {
                type rcExternalTemperature;
            }
        }
        """
        self.assertEqual(len(iter_boundary_fields(text)), 2)

    def test_numeric_close_and_restart_expected(self) -> None:
        self.assertTrue(numeric_close("97.4233333333333", "97.42333333333331"))
        restart = {"q_value_counts": {"97.4233333333333": 64}}
        self.assertTrue(restart_all_expected(restart, "97.42333333333331"))
        self.assertFalse(restart_all_expected({"q_value_counts": {"97.4": 63}}, "97.4"))

    def test_nested_q_value(self) -> None:
        block = """
            Q
            {
                type constant;
                value 97.4233333333333;
            }
        """
        self.assertEqual(scalar_for(block, "Q"), "97.4233333333333")


if __name__ == "__main__":
    unittest.main()
