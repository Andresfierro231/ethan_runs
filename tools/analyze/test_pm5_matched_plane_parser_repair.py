import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_pm5_matched_plane_parser_repair import parse_legacy_vtk_with_field_arrays


class PM5MatchedPlaneParserRepairTests(unittest.TestCase):
    def test_field_attributes_scalar_and_vector(self):
        content = """# vtk DataFile Version 2.0
sampleSurface
ASCII
DATASET POLYDATA
POINTS 4 float
0 0 0 1 0 0 1 1 0 0 1 0
POLYGONS 1 5
4 0 1 2 3
CELL_DATA 1
FIELD attributes 3
T 1 1 float
440
rho 1 1 float
1960
U 3 1 float
0.1 0.2 0.3
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.vtk"
            path.write_text(content)
            parsed = parse_legacy_vtk_with_field_arrays(path)
        self.assertEqual(parsed["cell_fields"]["T"].shape, (1,))
        self.assertEqual(parsed["cell_fields"]["rho"][0], 1960.0)
        self.assertEqual(parsed["cell_fields"]["U"].shape, (1, 3))
        self.assertAlmostEqual(parsed["cell_fields"]["U"][0][2], 0.3)


if __name__ == "__main__":
    unittest.main()
