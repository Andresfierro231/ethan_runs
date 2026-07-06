#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any, Iterable, Sequence

from tools.common import WORKSPACE_ROOT, csv_dump, json_dump, safe_float

ROOT = WORKSPACE_ROOT
SALT_DASHBOARD_CSV = ROOT / "reports" / "2026-06-17_ethan_nondimensional_dashboard_package" / "salt_dashboard.csv"
WATER_DASHBOARD_CSV = ROOT / "reports" / "2026-06-17_ethan_nondimensional_dashboard_package" / "water_dashboard.csv"


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def csv_dump_rows(path: Path, rows: list[dict[str, Any]], fieldnames: Sequence[str] | None = None) -> None:
    if fieldnames is None:
        if not rows:
            raise RuntimeError(f"cannot infer schema for empty table: {path}")
        fieldnames = list(rows[0].keys())
    csv_dump(path, fieldnames, rows)


def require_columns(rows: list[dict[str, str]], required: Sequence[str], table_name: str) -> None:
    if not rows:
        raise RuntimeError(f"{table_name} is empty")
    missing = [column for column in required if column not in rows[0]]
    if missing:
        raise RuntimeError(f"{table_name} missing required columns: {missing}")


def finite_float(value: Any, default: float = math.nan) -> float:
    parsed = safe_float(value)
    if parsed is None or not math.isfinite(parsed):
        return default
    return float(parsed)


def safe_mean(values: Iterable[float]) -> float:
    payload = [value for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return float(sum(payload) / len(payload))


def safe_sum(values: Iterable[float]) -> float:
    payload = [value for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return float(sum(payload))


def normalized_residual(residual_value: float, reference_value: float) -> float:
    if not math.isfinite(residual_value) or not math.isfinite(reference_value) or abs(reference_value) == 0.0:
        return math.nan
    return float(abs(residual_value) / abs(reference_value))


def sign_token(value: float, zero_tol: float = 0.0) -> str:
    if not math.isfinite(value):
        return "nan"
    if value > zero_tol:
        return "positive"
    if value < -zero_tol:
        return "negative"
    return "zero"


def filter_rows(rows: list[dict[str, str]], source_ids: set[str] | None) -> list[dict[str, str]]:
    if not source_ids:
        return rows
    return [row for row in rows if row.get("source_id") in source_ids]


def load_salt_dashboard_rows(source_ids: set[str] | None = None) -> list[dict[str, str]]:
    rows = load_csv_rows(SALT_DASHBOARD_CSV)
    require_columns(rows, ["source_id", "display_label", "package_root"], "salt_dashboard.csv")
    return filter_rows(rows, source_ids)


def load_water_dashboard_rows(source_ids: set[str] | None = None) -> list[dict[str, str]]:
    rows = load_csv_rows(WATER_DASHBOARD_CSV)
    require_columns(rows, ["source_id", "display_label", "package_root"], "water_dashboard.csv")
    return filter_rows(rows, source_ids)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    json_dump(path, payload)
