"""Tests for sample_bend_minor_loss.compute_minor_loss (T7)."""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.extract.sample_bend_minor_loss import compute_minor_loss  # noqa: E402


def _state(p_rgh, rho, q, y, n=100):
    # dynamic head q fixes an effective u; store both consistently
    u = math.sqrt(2 * q / rho) if rho > 0 and q > 0 else 0.0
    return {"p_rgh_pa": p_rgh, "rho_kg_m3": rho, "dynamic_head_pa": q,
            "u_bulk_m_s": u, "y_mean_m": y, "n_faces": n}


def test_buoyancy_source_subtracted_equal_elevation():
    # same elevation, same rho -> buoy term 0; loss = -(dp_rgh + dq)
    a = _state(10.0, 1900.0, 0.06, 0.30)
    b = _state(9.0, 1900.0, 0.06, 0.30)
    r = compute_minor_loss(a, b, "corner")
    assert abs(r["buoyancy_term_pa"]) < 1e-9
    assert abs(r["signed_loss_pa"] - 1.0) < 1e-9  # -(−1 + 0) = 1
    assert r["K_minor_loss"] > 0


def test_buoyancy_removed_across_elevation_change():
    # rho differs across an elevation change: buoy term must be gh*drho, subtracted
    a = _state(10.0, 1900.0, 0.06, 0.20)
    b = _state(10.0, 1920.0, 0.06, 0.30)
    r = compute_minor_loss(a, b, "corner")
    gh = -9.81 * 0.25
    assert abs(r["buoyancy_term_pa"] - gh * 20.0) < 1e-6
    # loss = -(0 + buoy + 0) = -buoy
    assert abs(r["signed_loss_pa"] + gh * 20.0) < 1e-6


def test_recirc_zone_K_undefined():
    a = _state(10.0, 1900.0, 0.0, 0.30)
    b = _state(9.0, 1900.0, 0.0, 0.30)
    r = compute_minor_loss(a, b, "corner")
    assert r["status"].startswith("K_undefined")
    assert math.isnan(r["K_minor_loss"])


def test_area_change_uses_throat_max_qref():
    a = _state(10.0, 1900.0, 0.02, 0.30)   # large bore, low q
    b = _state(9.0, 1900.0, 0.20, 0.30)    # throat, high q
    r = compute_minor_loss(a, b, "connector_expansion_contraction")
    assert r["q_ref_basis"] == "throat_max"
    assert abs(r["q_ref_pa"] - 0.20) < 1e-9
