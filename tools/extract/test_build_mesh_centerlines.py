"""Tests for build_mesh_centerlines.stations_from_points / inclination (T1)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.extract.build_mesh_centerlines import (  # noqa: E402
    inclination_from_horizontal_deg,
    stations_from_points,
)


def _cylinder_surface(axis: np.ndarray, length: float, radius: float,
                      n_along: int = 40, n_around: int = 40) -> np.ndarray:
    """Point cloud on the surface of a cylinder centered at origin along `axis`."""
    axis = axis / np.linalg.norm(axis)
    ref = np.array([1.0, 0.0, 0.0]) if abs(axis[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    e1 = ref - np.dot(ref, axis) * axis
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(axis, e1)
    pts = []
    for s in np.linspace(-length / 2, length / 2, n_along):
        for th in np.linspace(0, 2 * np.pi, n_around, endpoint=False):
            pts.append(s * axis + radius * (np.cos(th) * e1 + np.sin(th) * e2))
    return np.array(pts)


def test_inclination_bounds():
    assert inclination_from_horizontal_deg(np.array([0.0, 1.0, 0.0])) == 90.0
    assert inclination_from_horizontal_deg(np.array([1.0, 0.0, 0.0])) == 0.0


def test_vertical_cylinder_recovers_geometry():
    pts = _cylinder_surface(np.array([0.0, 1.0, 0.0]), length=1.0, radius=0.011)
    sts = stations_from_points(pts, 5)
    assert len(sts) >= 3
    for s in sts:
        incl = inclination_from_horizontal_deg(np.array([s["nx"], s["ny"], s["nz"]]))
        assert incl > 85.0  # vertical
    # bore ~ 2*radius = 22 mm, within a couple mm on interior stations
    interior = sts[1:-1]
    bores = [s["bore_m"] for s in interior]
    assert abs(np.median(bores) - 0.022) < 0.004


def test_inclined_cylinder_recovers_angle():
    # 21 deg above horizontal in the x-y plane
    theta = np.radians(21.0)
    axis = np.array([np.cos(theta), np.sin(theta), 0.0])
    pts = _cylinder_surface(axis, length=1.0, radius=0.011)
    sts = stations_from_points(pts, 5)
    # interior stations should recover ~21 deg (endpoints are one-sided)
    incls = [inclination_from_horizontal_deg(np.array([s["nx"], s["ny"], s["nz"]]))
             for s in sts[1:-1]]
    assert abs(np.median(incls) - 21.0) < 2.0
