from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.extract import openfoam_cell_volumes as volumes


def write_list(path: Path, klass: str, obj: str, rows: list[str], note: str = "") -> None:
    path.write_text(
        f"""FoamFile
{{
    format      ascii;
    class       {klass};
{note}
    location    "constant/polyMesh";
    object      {obj};
}}

{len(rows)}
(
{chr(10).join(rows)}
)
""",
        encoding="utf-8",
    )


def write_cube_mesh(poly_mesh: Path) -> None:
    poly_mesh.mkdir(parents=True)
    write_list(
        poly_mesh / "points",
        "vectorField",
        "points",
        [
            "(0 0 0)",
            "(1 0 0)",
            "(1 1 0)",
            "(0 1 0)",
            "(0 0 1)",
            "(1 0 1)",
            "(1 1 1)",
            "(0 1 1)",
        ],
    )
    write_list(
        poly_mesh / "faces",
        "faceList",
        "faces",
        [
            "4(0 3 2 1)",
            "4(4 5 6 7)",
            "4(0 1 5 4)",
            "4(3 7 6 2)",
            "4(0 4 7 3)",
            "4(1 2 6 5)",
        ],
    )
    write_list(poly_mesh / "owner", "labelList", "owner", ["0", "0", "0", "0", "0", "0"])
    write_list(poly_mesh / "neighbour", "labelList", "neighbour", [])


def write_two_cube_mesh(poly_mesh: Path) -> None:
    poly_mesh.mkdir(parents=True)
    write_list(
        poly_mesh / "points",
        "vectorField",
        "points",
        [
            "(0 0 0)",
            "(1 0 0)",
            "(1 1 0)",
            "(0 1 0)",
            "(0 0 1)",
            "(1 0 1)",
            "(1 1 1)",
            "(0 1 1)",
            "(2 0 0)",
            "(2 1 0)",
            "(2 0 1)",
            "(2 1 1)",
        ],
    )
    write_list(
        poly_mesh / "faces",
        "faceList",
        "faces",
        [
            "4(1 2 6 5)",
            "4(0 3 2 1)",
            "4(4 5 6 7)",
            "4(0 1 5 4)",
            "4(3 7 6 2)",
            "4(0 4 7 3)",
            "4(1 2 9 8)",
            "4(5 10 11 6)",
            "4(1 8 10 5)",
            "4(2 6 11 9)",
            "4(8 9 11 10)",
        ],
    )
    write_list(poly_mesh / "owner", "labelList", "owner", ["0", "0", "0", "0", "0", "0", "1", "1", "1", "1", "1"])
    write_list(poly_mesh / "neighbour", "labelList", "neighbour", ["1"])


def add_owner_note(poly_mesh: Path, n_points: int, n_cells: int, n_faces: int, n_internal_faces: int) -> None:
    owner = poly_mesh / "owner"
    text = owner.read_text(encoding="utf-8")
    text = text.replace(
        "    class       labelList;\n",
        (
            "    class       labelList;\n"
            f'    note        "nPoints:{n_points}  nCells:{n_cells}  '
            f'nFaces:{n_faces}  nInternalFaces:{n_internal_faces}";\n'
        ),
    )
    owner.write_text(text, encoding="utf-8")


class OpenFoamCellVolumeTests(unittest.TestCase):
    def test_single_cube_volume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mesh = Path(tmp) / "constant/polyMesh"
            write_cube_mesh(mesh)
            result, summary = volumes.compute_cell_volumes_from_mesh(mesh)
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result[0], 1.0)
        self.assertEqual(summary["negative_volume_cells"], 0)

    def test_two_cell_owner_neighbour_volume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mesh = Path(tmp) / "constant/polyMesh"
            write_two_cube_mesh(mesh)
            result, summary = volumes.compute_cell_volumes_from_mesh(mesh)
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result[0], 1.0)
        self.assertAlmostEqual(result[1], 1.0)
        self.assertEqual(summary["n_internal_faces"], 1)
        self.assertEqual(summary["negative_volume_cells"], 0)

    def test_streaming_path_matches_in_memory_path_with_header_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mesh = Path(tmp) / "constant/polyMesh"
            write_two_cube_mesh(mesh)
            add_owner_note(mesh, n_points=12, n_cells=2, n_faces=11, n_internal_faces=1)
            in_memory, _ = volumes.compute_cell_volumes_from_mesh(mesh)
            streaming, summary = volumes.compute_cell_volumes_streaming_from_mesh(mesh)
        self.assertEqual(summary["algorithm"], "streaming_faces_owner_neighbour")
        self.assertEqual(len(streaming), len(in_memory))
        for left, right in zip(streaming, in_memory):
            self.assertAlmostEqual(left, right)

    def test_write_cell_volume_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "volumes.csv"
            volumes.write_cell_volume_csv(out, [1.0, 2.5])
            text = out.read_text(encoding="utf-8")
        self.assertIn("cell_id,cellVolume_m3", text)
        self.assertIn("1,2.5", text)

    def test_package_metadata_rows_cover_queued_cases(self) -> None:
        rows = volumes.mesh_metadata_rows()
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        self.assertTrue(all(row["points_exists"] == "true" for row in rows))
        self.assertTrue(all(row["parser_status"] == "production_scale_mesh_not_parsed_on_login_node" for row in rows))

    def test_build_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = volumes.build_package(Path(tmp) / "pkg")
            self.assertEqual(payload["summary"]["mesh_rows"], 3)
            self.assertFalse(payload["summary"]["production_volume_export_run"])


if __name__ == "__main__":
    unittest.main()
