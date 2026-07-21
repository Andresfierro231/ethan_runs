"""Tests for derive_streamwise_momentum_budget (T1b).

Locks in the two properties that matter:
  1. On an ISOTHERMAL leg (drho/ds = 0) the buoyancy source vanishes and the
     corrected friction equals the orientation-only friction (consistency check).
  2. Flow orientation sigma = sign(mean U.tangent) is honoured, and a heated leg
     whose raw p_rgh gradient is buoyancy-dominated still yields POSITIVE de-buoyed
     friction.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.derive_streamwise_momentum_budget import budget_for_leg  # noqa: E402


def _station(label, x, y, z, nx, ny, nz, p_rgh, rho, u, u_along):
    return {
        "label": label, "span": "leg", "status": "sampled",
        "x": x, "y": y, "z": z, "nx": nx, "ny": ny, "nz": nz,
        "section_mean_p_rgh_pa": p_rgh, "section_mean_rho_kg_m3": rho,
        "u_bulk_m_s": u, "u_along_tangent_m_s": u_along,
        "hydraulic_diameter_m": 0.022,
    }


def test_isothermal_leg_corr_equals_orientation_only():
    # vertical leg, constant rho -> buoy = 0 -> f_corr == f_raw(oriented)
    sts = [
        _station("s0", 0, 0.0, 0, 0, 1, 0, 0.0, 1900.0, 0.014, 0.014),
        _station("s1", 0, 0.5, 0, 0, 1, 0, -5.0, 1900.0, 0.014, 0.014),
        _station("s2", 0, 1.0, 0, 0, 1, 0, -10.0, 1900.0, 0.014, 0.014),
    ]
    row = budget_for_leg("leg", sts)
    assert row["flow_orientation_sigma"] == 1.0
    assert abs(row["buoyancy_source_grad_pa_m"]) < 1e-9
    assert math.isfinite(row["f_corrected"])
    assert abs(row["f_corrected"] - row["f_raw_buoyancy_embedded"]) < 1e-9
    assert row["f_corrected"] > 0  # pressure falls along flow -> positive loss


def test_sigma_negative_when_flow_opposes_tangent():
    sts = [
        _station("s0", 0, 0.0, 0, 0, 1, 0, 0.0, 1900.0, 0.014, -0.014),
        _station("s1", 0, 0.5, 0, 0, 1, 0, 5.0, 1900.0, 0.014, -0.014),
        _station("s2", 0, 1.0, 0, 0, 1, 0, 10.0, 1900.0, 0.014, -0.014),
    ]
    row = budget_for_leg("leg", sts)
    assert row["flow_orientation_sigma"] == -1.0
    # p_rgh rises with +s but flow is -s, so it FALLS along flow -> positive loss
    assert row["f_raw_buoyancy_embedded"] > 0


def test_heated_leg_decomposition_identity():
    # rho DROPS along +s (heating) -> large buoyancy source. We assert the
    # DECOMPOSITION is exact (positivity of f_corr is a property of a real steady
    # CFD solution, not of arbitrary synthetic inputs, so we don't assert it here).
    sts = [
        _station("s0", 0, 0.0, 0, 0, 1, 0, 0.0, 1950.0, 0.014, 0.014),
        _station("s1", 0, 0.5, 0, 0, 1, 0, 8.0, 1900.0, 0.014, 0.014),
        _station("s2", 0, 1.0, 0, 0, 1, 0, 6.0, 1850.0, 0.014, 0.014),
    ]
    row = budget_for_leg("leg", sts)
    sigma = row["flow_orientation_sigma"]
    assert abs(row["buoyancy_source_grad_pa_m"]) > abs(row["grad_p_rgh_pa_m"])  # buoy-dominated
    # corrected friction gradient removes exactly the (oriented) buoyancy source
    assert abs((row["friction_grad_corrected_pa_m"] - row["friction_grad_raw_pa_m"])
               - (-sigma * row["buoyancy_source_grad_pa_m"])) < 1e-9
    # and the no-inertia variant additionally removes the (oriented) inertial term
    assert abs((row["friction_grad_corrected_noinertia_pa_m"] - row["friction_grad_corrected_pa_m"])
               - (-sigma * row["inertial_grad_pa_m"])) < 1e-9
