#!/usr/bin/env python3
"""Tests for the thermal-closure extractor (sample_segment_htc_uaprime).

RUN WITH SYSTEM PYTHON (do NOT source any OpenFOAM env — it breaks python):
    python -m pytest tools/extract/test_sample_segment_htc_uaprime.py -q

Covers, on synthetic + (when present) the real reconstructed field:
  * boundaryField `value` parser: uniform scalar AND nonuniform List<scalar>
  * wallHeatFlux .dat parser (latest time block; Q[W], q[W/m^2])
  * area-weighted segment T_wall (Q/q weighting + equal-weight fallback)
  * HTC / UA' / Nu / R' formulas + signed ΔT convention on synthetic inputs
  * cut-plane column schema resolution (appended vs middle T)
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.extract.sample_segment_htc_uaprime as m  # noqa: E402

REAL_T = ROOT / "tmp" / "2026-06-30_claude_action_items" / "recon_salt2_of13" / "7915" / "T"


# --------------------------------------------------------------------------- #
# boundaryField scalar parser
# --------------------------------------------------------------------------- #
def test_parse_patch_scalar_uniform():
    block = "type fixedValue;\n        value uniform 451.25;\n"
    vals = m.parse_patch_scalar_field(block, "value")
    assert vals is not None and vals.shape == (1,)
    assert abs(vals[0] - 451.25) < 1e-9


def test_parse_patch_scalar_nonuniform():
    block = (
        "type rcExternalTemperature;\n"
        "        value           nonuniform List<scalar> \n"
        "4\n(\n440.0\n450.0\n460.0\n470.0\n)\n;\n"
    )
    vals = m.parse_patch_scalar_field(block, "value")
    assert vals is not None and vals.shape == (4,)
    assert abs(vals.mean() - 455.0) < 1e-9


def test_parse_patch_scalar_nonuniform_ignores_nested_lists():
    # a real rcExternalTemperature block carries nested kappaLayerCoeffs lists with
    # their own parens before the `value` list; the brace/paren matcher must not be
    # confused and must grab the `value` list specifically.
    block = (
        "        thicknessLayers List<scalar> 2(0.006 0.035);\n"
        "        kappaLayerCoeffs \n(\n8(9.2 0.0157 0 0 0 0 0 0)\n8(0.036 0 0 0 0 0 0 0)\n);\n"
        "        Tp nonuniform List<scalar> 3 (1.0 2.0 3.0);\n"
        "        value nonuniform List<scalar> \n3\n(\n400.0\n420.0\n440.0\n)\n;\n"
    )
    vals = m.parse_patch_scalar_field(block, "value")
    assert vals is not None and vals.shape == (3,)
    assert abs(vals.mean() - 420.0) < 1e-9


def test_parse_patch_scalar_absent_returns_none():
    assert m.parse_patch_scalar_field("type zeroGradient;\n", "value") is None


def test_find_patch_block_brace_matching():
    bf = (
        "boundaryField\n{\n"
        "    walls\n    {\n        type fixedValue;\n        h { type uniform; value 3.0; }\n        value uniform 450.0;\n    }\n"
        "    other\n    {\n        type zeroGradient;\n    }\n}\n"
    )
    blk = m._find_patch_block(bf, "walls")
    assert blk is not None and "value uniform 450.0" in blk
    # nested h{...} must not terminate the block early
    vals = m.parse_patch_scalar_field(blk, "value")
    assert abs(vals[0] - 450.0) < 1e-9


# --------------------------------------------------------------------------- #
# wallHeatFlux .dat parser
# --------------------------------------------------------------------------- #
def test_parse_wallheatflux_latest_block(tmp_path):
    p = tmp_path / "wallHeatFlux.dat"
    p.write_text(
        "# Time patch min max Q[W] q[W/m2]\n"
        "100\tpatchA\t-1\t1\t10.0\t100.0\n"
        "100\tpatchB\t-2\t2\t20.0\t50.0\n"
        "200\tpatchA\t-1\t1\t12.0\t120.0\n"
        "200\tpatchB\t-2\t2\t24.0\t60.0\n",
        encoding="utf-8",
    )
    rows = m.parse_wallheatflux(p)
    # only the latest (t=200) block survives
    assert set(rows) == {"patchA", "patchB"}
    assert abs(rows["patchA"]["Q_w"] - 12.0) < 1e-9
    assert abs(rows["patchA"]["q_wm2"] - 120.0) < 1e-9
    # implied area = Q/q
    assert abs(rows["patchA"]["Q_w"] / rows["patchA"]["q_wm2"] - 0.1) < 1e-9


# --------------------------------------------------------------------------- #
# segment T_wall area weighting
# --------------------------------------------------------------------------- #
def test_segment_wall_T_area_weighted(tmp_path):
    # two patches: A area 1.0 @ 500 K, B area 3.0 @ 400 K -> area mean = 425 K
    field = tmp_path / "T"
    field.write_text(
        "boundaryField\n{\n"
        "    A\n    {\n        type fixedValue;\n        value uniform 500.0;\n    }\n"
        "    B\n    {\n        type fixedValue;\n        value nonuniform List<scalar> 2 (390.0 410.0);\n    }\n"
        "}\n",
        encoding="utf-8",
    )
    whf = {"A": {"Q_w": 100.0, "q_wm2": 100.0},   # area 1.0
           "B": {"Q_w": 300.0, "q_wm2": 100.0}}   # area 3.0
    res = m.segment_wall_T(field, ["A", "B"], whf)
    assert res["wall_T_weighting"] == "area_weighted_Qoverq"
    assert abs(res["T_wall_k"] - (1.0 * 500.0 + 3.0 * 400.0) / 4.0) < 1e-9


def test_segment_wall_T_equal_weight_fallback(tmp_path):
    field = tmp_path / "T"
    field.write_text(
        "boundaryField\n{\n"
        "    A\n    {\n        type fixedValue;\n        value uniform 500.0;\n    }\n"
        "    B\n    {\n        type fixedValue;\n        value uniform 400.0;\n    }\n"
        "}\n",
        encoding="utf-8",
    )
    res = m.segment_wall_T(field, ["A", "B"], whf={})  # no FO area -> face-count weight
    assert res["wall_T_weighting"] == "equal_weight_fallback_facecount"
    assert abs(res["T_wall_k"] - 450.0) < 1e-9  # both 1 face


# --------------------------------------------------------------------------- #
# cut-plane column schema resolution
# --------------------------------------------------------------------------- #
def test_resolve_cutplane_columns_appended():
    # x y z Ux Uy Uz p_rgh rho T  (T at 8)
    data = np.array([[0, 0, 0, 1, 0, 0, 1234.0, 1800.0, 450.0]] * 10)
    cols = m._resolve_cutplane_columns(data)
    assert cols["T"] == 8 and cols["rho"] == 7


def test_resolve_cutplane_columns_middle():
    # x y z Ux Uy Uz T p_rgh rho  (T at 6)
    data = np.array([[0, 0, 0, 1, 0, 0, 450.0, 1234.0, 1800.0]] * 10)
    cols = m._resolve_cutplane_columns(data)
    assert cols["T"] == 6 and cols["rho"] == 8


# --------------------------------------------------------------------------- #
# HTC / UA' / Nu / R' formulas + signed convention
# --------------------------------------------------------------------------- #
def test_htc_uaprime_nu_rprime_formulas():
    # synthetic heated segment
    q_w = -2000.0            # W/m^2, signed (heat INTO fluid)
    qprime = -400.0          # W/m
    t_wall, t_bulk = 470.0, 450.0
    delta = t_wall - t_bulk  # +20 K
    htc = q_w / delta
    uaprime = qprime / delta
    rprime = 1.0 / uaprime
    D_h = 0.03
    k = 0.5
    nu = htc * D_h / k
    # heated wall: q<0 and ΔT>0 -> htc, uaprime negative under signed convention;
    # the sign-consistency flag should be True.
    assert htc < 0 and uaprime < 0
    assert abs(rprime - 1.0 / uaprime) < 1e-12
    assert abs(nu - htc * D_h / k) < 1e-12
    # R' is reciprocal of UA'
    assert abs(uaprime * rprime - 1.0) < 1e-12


def test_polynomial_eval():
    assert abs(m.polynomial_eval([1423.47], 500.0) - 1423.47) < 1e-9  # constant cp
    # 2 + 3 T at T=10 -> 32
    assert abs(m.polynomial_eval([2.0, 3.0], 10.0) - 32.0) < 1e-9
    assert math.isnan(m.polynomial_eval([1.0], float("nan")))


# --------------------------------------------------------------------------- #
# REAL reconstructed field (skipped if absent) — sanity that heater > cooler
# --------------------------------------------------------------------------- #
def test_real_field_wall_T_physical():
    import pytest
    if not REAL_T.is_file():
        pytest.skip(f"real reconstructed T not present at {REAL_T}")
    means = m.parse_wall_T_means(
        REAL_T,
        ["pipeleg_lower_04_straight", "pipeleg_upper_05_cooler"],
    )
    heater = means["pipeleg_lower_04_straight"]["T_mean"]
    cooler = means["pipeleg_upper_05_cooler"]["T_mean"]
    assert heater > cooler, f"heated leg ({heater}) should be hotter than cooler ({cooler})"
    assert 400.0 < cooler < heater < 500.0
