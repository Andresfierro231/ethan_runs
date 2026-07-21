"""Pytest tests for the heat source/sink ledger (AGENT-194, 2026-07-07).

Tests cover:
1. All 3 source_ids are present
2. wallHeatFlux_integral_W for heater group is positive
3. wallHeatFlux_integral_W for cooler group is negative
4. Net sum per source_id < 1% of |heater duty| (loose tolerance)
5. radiation_present is always False
6. Required columns are present

Run with:
    python -m pytest tools/analyze/test_heat_source_sink_ledger.py -v
    python -m pytest tools/analyze/test_*.py tools/extract/test_*.py -q  # full suite
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from collections import defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Module loading
# ---------------------------------------------------------------------------


def _load(mod_name: str, rel: str):
    spec = importlib.util.spec_from_file_location(mod_name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


ledger_mod = _load(
    "build_heat_source_sink_ledger",
    "tools/analyze/build_heat_source_sink_ledger.py",
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

LEDGER_CSV = (
    ROOT / "work_products" / "2026-07-07_heat_source_sink_ledger" / "heat_source_sink_ledger.csv"
)

REQUIRED_COLUMNS = [
    "source_id",
    "salt_label",
    "patch_group",
    "patch_names",
    "bc_type",
    "bc_sign_convention",
    "wallHeatFlux_integral_W",
    "span",
    "T_bulk_inlet_K",
    "T_bulk_outlet_K",
    "mdot_kg_s",
    "enthalpy_change_W",
    "residual_W",
    "residual_fraction",
    "radiation_present",
    "note",
]

EXPECTED_SOURCE_IDS = {
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
}


# ---------------------------------------------------------------------------
# Helpers to load the generated CSV
# ---------------------------------------------------------------------------


def load_ledger_csv() -> list[dict[str, str]]:
    if not LEDGER_CSV.exists():
        pytest.skip(f"Ledger CSV not found at {LEDGER_CSV}; run the script first")
    with LEDGER_CSV.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def rows_for_group(rows: list[dict], group: str) -> list[dict]:
    return [r for r in rows if r["patch_group"] == group]


def heater_sum_for_source(rows: list[dict], source_id: str) -> float:
    return sum(
        float(r["wallHeatFlux_integral_W"])
        for r in rows
        if r["source_id"] == source_id and r["patch_group"] == "heater"
        and r["wallHeatFlux_integral_W"].strip() not in {"", "nan", "NaN"}
    )


def net_sum_for_source(rows: list[dict], source_id: str) -> float:
    return sum(
        float(r["wallHeatFlux_integral_W"])
        for r in rows
        if r["source_id"] == source_id
        and r["wallHeatFlux_integral_W"].strip() not in {"", "nan", "NaN"}
    )


# ---------------------------------------------------------------------------
# Unit tests for helper functions (run without CFD data)
# ---------------------------------------------------------------------------


class TestClassifyPatch:
    """Tests for patch classification (pure/deterministic)."""

    def test_heater_patch_classified(self):
        result = ledger_mod.classify_patch("pipeleg_lower_04_straight")
        assert result == ("heater", "lower_leg"), f"Expected ('heater', 'lower_leg'), got {result}"

    def test_heater_patch_05_classified(self):
        result = ledger_mod.classify_patch("pipeleg_lower_05_straight")
        assert result == ("heater", "lower_leg")

    def test_heater_patch_06_classified(self):
        result = ledger_mod.classify_patch("pipeleg_lower_06_straight")
        assert result == ("heater", "lower_leg")

    def test_cooler_patch_classified(self):
        result = ledger_mod.classify_patch("pipeleg_upper_05_cooler")
        assert result == ("cooler", "cooling_branch")

    def test_reducer_classified_as_cooler(self):
        r4 = ledger_mod.classify_patch("pipeleg_upper_04_reducer")
        r6 = ledger_mod.classify_patch("pipeleg_upper_06_reducer")
        assert r4 == ("cooler", "cooling_branch")
        assert r6 == ("cooler", "cooling_branch")

    def test_test_section_classified(self):
        result = ledger_mod.classify_patch("pipeleg_left_04_test_section")
        assert result == ("test_section", "upcomer")

    def test_ambient_lower_leg(self):
        for patch in [
            "pipeleg_lower_01_fitting",
            "pipeleg_lower_02_straight",
            "pipeleg_lower_03_bend",
            "pipeleg_lower_07_bend",
            "pipeleg_lower_08_straight",
            "pipeleg_lower_09_fitting",
        ]:
            result = ledger_mod.classify_patch(patch)
            assert result == ("ambient_wall", "lower_leg"), f"Failed for {patch}: {result}"

    def test_ambient_downcomer(self):
        for patch in ["pipeleg_right_01_lower", "pipeleg_right_02_middle", "pipeleg_right_03_upper"]:
            result = ledger_mod.classify_patch(patch)
            assert result == ("ambient_wall", "downcomer"), f"Failed for {patch}: {result}"

    def test_ncc_non_junction_skipped(self):
        result = ledger_mod.classify_patch("ncc_pipeleg_lower_01_fitting_start")
        assert result is None, f"Expected None for NCC non-junction patch, got {result}"

    def test_junction_classified(self):
        result = ledger_mod.classify_patch("junction_lower_left")
        assert result == ("junction_other", "junction")

    def test_junction_stub_classified(self):
        result = ledger_mod.classify_patch("junction_lower_left_left_stub")
        assert result == ("junction_other", "junction")

    def test_ncc_junction_classified(self):
        # ncc_junction patches contain "junction" in name → classified as junction_other
        result = ledger_mod.classify_patch("ncc_junction_lower_left_right_end")
        assert result == ("junction_other", "junction")


class TestParseWallHeatFlux:
    """Tests for wallHeatFlux.dat parser using a synthetic file."""

    def _write_dat(self, tmp_path, content: str) -> Path:
        f = tmp_path / "wallHeatFlux.dat"
        f.write_text(content, encoding="utf-8")
        return f

    def test_single_timestep_returns_last(self, tmp_path):
        content = (
            "# Wall heat-flux\n"
            "# Time patch min max Q q\n"
            "1.0 patch_a 0.0 10.0 5.0 3.0\n"
            "1.0 patch_b 0.0 -5.0 -2.5 -1.5\n"
        )
        f = self._write_dat(tmp_path, content)
        result = ledger_mod.parse_wallheatflux_latest(f)
        assert abs(result["patch_a"] - 5.0) < 1e-9
        assert abs(result["patch_b"] - (-2.5)) < 1e-9

    def test_two_timesteps_returns_last(self, tmp_path):
        content = (
            "# header\n"
            "1.0 patch_a 0.0 10.0 5.0 3.0\n"
            "2.0 patch_a 0.0 20.0 15.0 8.0\n"
        )
        f = self._write_dat(tmp_path, content)
        result = ledger_mod.parse_wallheatflux_latest(f)
        assert abs(result["patch_a"] - 15.0) < 1e-9

    def test_ncc_patch_with_zero_q(self, tmp_path):
        content = "1.0 ncc_pipeleg_lower_01 0.0 0.0 0.0 0.0\n"
        f = self._write_dat(tmp_path, content)
        result = ledger_mod.parse_wallheatflux_latest(f)
        assert result.get("ncc_pipeleg_lower_01") == 0.0

    def test_missing_file_returns_empty(self, tmp_path):
        result = ledger_mod.parse_wallheatflux_latest(tmp_path / "missing.dat")
        assert result == {}


class TestParseBCTypes:
    """Tests for 0/T BC type parser."""

    def _write_T(self, tmp_path, content: str) -> Path:
        f = tmp_path / "T"
        f.write_text(content, encoding="utf-8")
        return f

    def test_extract_simple_bc_type(self, tmp_path):
        content = """
        "pipeleg_lower_04_straight"
        {
            type            rcExternalTemperature;
            h               uniform 4.0;
        }
        """
        f = self._write_T(tmp_path, content)
        result = ledger_mod.parse_bc_types(f)
        assert result.get("pipeleg_lower_04_straight") == "rcExternalTemperature"

    def test_extract_zero_gradient(self, tmp_path):
        content = """
        "ncc_pipeleg_lower_01_fitting_start"
        {
            type            zeroGradient;
        }
        """
        f = self._write_T(tmp_path, content)
        result = ledger_mod.parse_bc_types(f)
        assert result.get("ncc_pipeleg_lower_01_fitting_start") == "zeroGradient"

    def test_multiple_patches(self, tmp_path):
        content = """
        "patch_a"
        {
            type rcExternalTemperature;
        }
        "patch_b"
        {
            type externalTemperature;
        }
        """
        f = self._write_T(tmp_path, content)
        result = ledger_mod.parse_bc_types(f)
        assert result.get("patch_a") == "rcExternalTemperature"
        assert result.get("patch_b") == "externalTemperature"

    def test_missing_file_returns_empty(self, tmp_path):
        result = ledger_mod.parse_bc_types(tmp_path / "T_missing")
        assert result == {}


class TestAggregateCheck:
    """Tests for aggregate check function using synthetic rows."""

    def _make_row(self, source_id: str, group: str, q: float) -> dict:
        return {
            "source_id": source_id,
            "patch_group": group,
            "wallHeatFlux_integral_W": str(q),
        }

    def test_heater_sum_correct(self):
        rows = [
            self._make_row("s1", "heater", 100.0),
            self._make_row("s1", "cooler", -80.0),
            self._make_row("s1", "ambient_wall", -15.0),
        ]
        checks = ledger_mod.compute_aggregate_check(rows)
        assert len(checks) == 1
        assert abs(checks[0]["heater_sum_W"] - 100.0) < 1e-6

    def test_net_sum_correct(self):
        rows = [
            self._make_row("s1", "heater", 100.0),
            self._make_row("s1", "cooler", -80.0),
            self._make_row("s1", "ambient_wall", -15.0),
        ]
        checks = ledger_mod.compute_aggregate_check(rows)
        assert abs(checks[0]["net_sum_all_groups_W"] - 5.0) < 1e-6

    def test_exact_balance_passes_gate(self):
        rows = [
            self._make_row("s1", "heater", 100.0),
            self._make_row("s1", "cooler", -99.9),
            self._make_row("s1", "ambient_wall", -0.1),
        ]
        checks = ledger_mod.compute_aggregate_check(rows)
        assert checks[0]["passes_01pct_gate"] is True

    def test_large_imbalance_fails_gate(self):
        rows = [
            self._make_row("s1", "heater", 100.0),
            self._make_row("s1", "cooler", -50.0),
        ]
        checks = ledger_mod.compute_aggregate_check(rows)
        assert checks[0]["passes_01pct_gate"] is False


# ---------------------------------------------------------------------------
# Integration tests against generated CSV
# (skipped if CSV does not exist)
# ---------------------------------------------------------------------------


class TestLedgerCSV:
    """Integration tests reading the generated ledger CSV."""

    @pytest.fixture(scope="class")
    def rows(self):
        return load_ledger_csv()

    def test_all_three_source_ids_present(self, rows):
        """All 3 Salt Jin mainline source_ids must appear in the ledger."""
        found = {r["source_id"] for r in rows}
        missing = EXPECTED_SOURCE_IDS - found
        assert not missing, f"Missing source_ids: {missing}"

    def test_required_columns_present(self, rows):
        """Every required column must be in the CSV header."""
        if not rows:
            pytest.skip("No rows in CSV")
        actual_cols = set(rows[0].keys())
        missing = set(REQUIRED_COLUMNS) - actual_cols
        assert not missing, f"Missing columns: {missing}"

    def test_heater_group_positive_q(self, rows):
        """wallHeatFlux_integral_W for the heater patch_group must be > 0
        (positive = heat into fluid) for all source_ids."""
        heater_rows = rows_for_group(rows, "heater")
        assert heater_rows, "No heater rows found in ledger"
        for row in heater_rows:
            q = float(row["wallHeatFlux_integral_W"])
            assert q > 0, (
                f"Heater group has non-positive Q={q} for {row['source_id']}"
            )

    def test_cooler_group_negative_q(self, rows):
        """wallHeatFlux_integral_W for the cooler patch_group must be < 0
        (negative = heat out of fluid) for all source_ids."""
        cooler_rows = rows_for_group(rows, "cooler")
        assert cooler_rows, "No cooler rows found in ledger"
        for row in cooler_rows:
            q = float(row["wallHeatFlux_integral_W"])
            assert q < 0, (
                f"Cooler group has non-negative Q={q} for {row['source_id']}"
            )

    def test_net_sum_within_1pct_of_heater(self, rows):
        """Net sum of all wallHeatFlux_integral_W per source_id must be < 1% of
        |heater duty|.  Loose tolerance — exact balance is not expected for
        quasi-steady CFD at finite time."""
        for source_id in EXPECTED_SOURCE_IDS:
            heater = heater_sum_for_source(rows, source_id)
            net = net_sum_for_source(rows, source_id)
            if abs(heater) < 1e-6:
                pytest.skip(f"Heater sum near zero for {source_id}")
            frac = abs(net / heater)
            assert frac < 0.01, (
                f"Net balance for {source_id}: |net/heater|={frac:.4f} > 1%"
                f" (net={net:.2f} W, heater={heater:.2f} W)"
            )

    def test_radiation_present_always_false(self, rows):
        """radiation_present must be False for every row."""
        assert rows, "No rows in ledger"
        for row in rows:
            val = row["radiation_present"]
            # CSV stores it as 'False' string
            assert val in {"False", "false", "0", ""}, (
                f"radiation_present={val!r} for {row['source_id']} / {row['patch_group']}"
            )

    def test_exactly_three_source_ids(self, rows):
        """Ledger must contain exactly 3 source_ids (Salt 2/3/4 Jin)."""
        found = {r["source_id"] for r in rows}
        assert len(found) == 3, f"Expected 3 source_ids, got {len(found)}: {found}"

    def test_heater_source_id_is_lower_leg(self, rows):
        """All heater rows must be on the lower_leg span."""
        heater_rows = rows_for_group(rows, "heater")
        for row in heater_rows:
            assert row["span"] == "lower_leg", (
                f"Heater span={row['span']} for {row['source_id']}"
            )

    def test_cooler_span_is_cooling_branch(self, rows):
        """All cooler rows must be on the cooling_branch span."""
        cooler_rows = rows_for_group(rows, "cooler")
        for row in cooler_rows:
            assert row["span"] == "cooling_branch", (
                f"Cooler span={row['span']} for {row['source_id']}"
            )

    def test_mdot_positive_for_all_rows(self, rows):
        """mdot_kg_s must be a positive number for all rows that have it."""
        for row in rows:
            val = row.get("mdot_kg_s", "").strip()
            if val in {"", "nan", "NaN"}:
                continue
            mdot = float(val)
            assert mdot > 0, (
                f"mdot_kg_s={mdot} not positive for {row['source_id']}"
            )

    def test_salt_label_matches_source_id(self, rows):
        """salt_label must match the number embedded in source_id."""
        for row in rows:
            sid = row["source_id"]
            label = row["salt_label"]
            if "test_2" in sid:
                assert label == "salt_2", f"label={label} for {sid}"
            elif "test_3" in sid:
                assert label == "salt_3", f"label={label} for {sid}"
            elif "test_4" in sid:
                assert label == "salt_4", f"label={label} for {sid}"

    def test_patch_names_not_empty(self, rows):
        """patch_names must be non-empty for every row."""
        for row in rows:
            assert row["patch_names"].strip(), (
                f"Empty patch_names for {row['source_id']} / {row['patch_group']}"
            )
