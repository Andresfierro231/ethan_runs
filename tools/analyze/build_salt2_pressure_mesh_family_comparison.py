#!/usr/bin/env python3
"""Build AGENT-262 Salt2 medium/fine pressure-only mesh-family comparison."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_DIR = (
    ROOT
    / "work_products/2026-07/2026-07-10"
    / "2026-07-10_salt2_refined_pressure_smoke_and_8pm_batch"
    / "outputs"
)
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "work_products/2026-07/2026-07-13"
    / "2026-07-13_salt2_pressure_only_mesh_family_comparison"
)
LEVELS = ("medium", "fine")
PRESSURE_COLUMNS = [
    "section_mean_p_rgh_pa",
    "section_mean_total_pressure_pa",
    "dynamic_head_pa",
    "u_bulk_m_s",
    "flow_alignment",
]
FRICTION_METHODS = ("section_mean_total_pressure_gradient", "section_mean_static_gradient")
THERMAL_BLOCKER_TEXT = (
    "Thermal closure remains blocked by reconstructed-T corruption; AGENT-262 "
    "uses pressure/friction/momentum outputs only."
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: format_value(row.get(name)) for name in fieldnames})


def format_value(value: object) -> object:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
        return f"{value:.12g}"
    if value is None:
        return ""
    return value


def number(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return None if math.isnan(parsed) or math.isinf(parsed) else parsed


def delta_pct(fine: float | None, medium: float | None) -> float | None:
    if fine is None or medium is None or medium == 0:
        return None
    return 100.0 * (fine - medium) / abs(medium)


def abs_delta(fine: float | None, medium: float | None) -> float | None:
    if fine is None or medium is None:
        return None
    return fine - medium


def first_section_path(level_dir: Path) -> Path:
    matches = sorted(level_dir.glob("section_mean_pressure_*.csv"))
    if not matches:
        raise FileNotFoundError(f"No section_mean_pressure_*.csv under {level_dir}")
    return matches[0]


def load_level(input_dir: Path, level: str) -> dict[str, list[dict[str, str]]]:
    level_dir = input_dir / level
    return {
        "section": read_csv(first_section_path(level_dir)),
        "friction": read_csv(level_dir / "segment_friction.csv"),
        "momentum": read_csv(level_dir / "momentum_budget.csv"),
    }


def by_key(rows: Iterable[dict[str, str]], *keys: str) -> dict[tuple[str, ...], dict[str, str]]:
    return {tuple(row.get(key, "") for key in keys): row for row in rows}


def mesh_agreement_label(rel_delta_pct: float | None) -> str:
    if rel_delta_pct is None:
        return "not_comparable"
    value = abs(rel_delta_pct)
    if value <= 5:
        return "strong_medium_fine_agreement"
    if value <= 10:
        return "usable_medium_fine_agreement"
    if value <= 25:
        return "weak_medium_fine_agreement"
    return "poor_medium_fine_agreement"


def friction_sign_safe(row: dict[str, str]) -> bool:
    flags = row.get("flags", "")
    f_app = number(row.get("apparent_darcy_f"))
    dp_loss = number(row.get("dp_loss_ds_pa_per_m"))
    return (
        f_app is not None
        and dp_loss is not None
        and f_app > 0
        and dp_loss > 0
        and "negative_f_pressure_recovery_or_noise" not in flags
    )


def friction_verdict(medium: dict[str, str], fine: dict[str, str]) -> str:
    medium_safe = friction_sign_safe(medium)
    fine_safe = friction_sign_safe(fine)
    rel = delta_pct(number(fine.get("apparent_darcy_f")), number(medium.get("apparent_darcy_f")))
    if not medium_safe or not fine_safe:
        return "not_fit_safe_pressure_recovery_or_noise"
    if rel is not None and abs(rel) <= 10:
        return "fit_safe_pressure_gradient"
    return "sign_safe_but_mesh_delta_review"


def momentum_verdict(medium: dict[str, str], fine: dict[str, str]) -> str:
    med_f = number(medium.get("f_corrected"))
    fine_f = number(fine.get("f_corrected"))
    rel = delta_pct(fine_f, med_f)
    if med_f is None or fine_f is None or med_f <= 0 or fine_f <= 0:
        return "not_fit_safe_corrected_f_nonpositive"
    if rel is None or abs(rel) > 10:
        return "positive_corrected_f_but_mesh_delta_review"
    return "fit_safe_momentum_corrected"


def build_pressure_comparison(level_data: dict[str, dict[str, list[dict[str, str]]]]) -> list[dict[str, object]]:
    medium_rows = by_key(level_data["medium"]["section"], "label")
    fine_rows = by_key(level_data["fine"]["section"], "label")
    rows: list[dict[str, object]] = []
    for key in sorted(set(medium_rows) & set(fine_rows)):
        medium = medium_rows[key]
        fine = fine_rows[key]
        row: dict[str, object] = {
            "label": key[0],
            "span": medium.get("span", fine.get("span", "")),
            "medium_gate": medium.get("gate", ""),
            "fine_gate": fine.get("gate", ""),
            "medium_status": medium.get("status", ""),
            "fine_status": fine.get("status", ""),
        }
        for column in PRESSURE_COLUMNS:
            medium_value = number(medium.get(column))
            fine_value = number(fine.get(column))
            row[f"medium_{column}"] = medium_value
            row[f"fine_{column}"] = fine_value
            row[f"delta_{column}"] = abs_delta(fine_value, medium_value)
            row[f"delta_pct_{column}"] = delta_pct(fine_value, medium_value)
        rows.append(row)
    return rows


def build_friction_comparison(level_data: dict[str, dict[str, list[dict[str, str]]]]) -> list[dict[str, object]]:
    medium_rows = by_key(level_data["medium"]["friction"], "span", "method")
    fine_rows = by_key(level_data["fine"]["friction"], "span", "method")
    rows: list[dict[str, object]] = []
    for key in sorted(set(medium_rows) & set(fine_rows)):
        medium = medium_rows[key]
        fine = fine_rows[key]
        med_f = number(medium.get("apparent_darcy_f"))
        fine_f = number(fine.get("apparent_darcy_f"))
        rel = delta_pct(fine_f, med_f)
        rows.append(
            {
                "span": key[0],
                "method": key[1],
                "medium_apparent_darcy_f": med_f,
                "fine_apparent_darcy_f": fine_f,
                "delta_apparent_darcy_f": abs_delta(fine_f, med_f),
                "delta_pct_apparent_darcy_f": rel,
                "mesh_agreement": mesh_agreement_label(rel),
                "medium_dp_loss_ds_pa_per_m": number(medium.get("dp_loss_ds_pa_per_m")),
                "fine_dp_loss_ds_pa_per_m": number(fine.get("dp_loss_ds_pa_per_m")),
                "medium_reynolds_number": number(medium.get("reynolds_number")),
                "fine_reynolds_number": number(fine.get("reynolds_number")),
                "medium_flags": medium.get("flags", ""),
                "fine_flags": fine.get("flags", ""),
                "sign_review": "positive_loss_both_meshes"
                if friction_sign_safe(medium) and friction_sign_safe(fine)
                else "pressure_recovery_or_noise_flagged",
                "fit_safety": friction_verdict(medium, fine),
            }
        )
    return rows


def build_momentum_comparison(level_data: dict[str, dict[str, list[dict[str, str]]]]) -> list[dict[str, object]]:
    medium_rows = by_key(level_data["medium"]["momentum"], "span")
    fine_rows = by_key(level_data["fine"]["momentum"], "span")
    rows: list[dict[str, object]] = []
    for key in sorted(set(medium_rows) & set(fine_rows)):
        medium = medium_rows[key]
        fine = fine_rows[key]
        med_f = number(medium.get("f_corrected"))
        fine_f = number(fine.get("f_corrected"))
        rel = delta_pct(fine_f, med_f)
        med_buoy = number(medium.get("buoyancy_fraction_of_raw_grad"))
        fine_buoy = number(fine.get("buoyancy_fraction_of_raw_grad"))
        rows.append(
            {
                "span": key[0],
                "medium_f_corrected": med_f,
                "fine_f_corrected": fine_f,
                "delta_f_corrected": abs_delta(fine_f, med_f),
                "delta_pct_f_corrected": rel,
                "mesh_agreement": mesh_agreement_label(rel),
                "medium_f_corrected_over_flam": number(medium.get("f_corrected_over_flam")),
                "fine_f_corrected_over_flam": number(fine.get("f_corrected_over_flam")),
                "medium_f_raw_buoyancy_embedded": number(medium.get("f_raw_buoyancy_embedded")),
                "fine_f_raw_buoyancy_embedded": number(fine.get("f_raw_buoyancy_embedded")),
                "medium_buoyancy_fraction_of_raw_grad": med_buoy,
                "fine_buoyancy_fraction_of_raw_grad": fine_buoy,
                "medium_inertial_grad_pa_m": number(medium.get("inertial_grad_pa_m")),
                "fine_inertial_grad_pa_m": number(fine.get("inertial_grad_pa_m")),
                "medium_Re": number(medium.get("Re")),
                "fine_Re": number(fine.get("Re")),
                "sign_review": "corrected_f_positive_both_meshes"
                if med_f is not None and fine_f is not None and med_f > 0 and fine_f > 0
                else "corrected_f_nonpositive_review",
                "buoyancy_review": "strong_buoyancy_correction"
                if (med_buoy is not None and abs(med_buoy) > 1.0)
                or (fine_buoy is not None and abs(fine_buoy) > 1.0)
                else "moderate_buoyancy_correction",
                "fit_safety": momentum_verdict(medium, fine),
            }
        )
    return rows


def build_fit_safety_summary(
    friction_rows: list[dict[str, object]], momentum_rows: list[dict[str, object]]
) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    for row in friction_rows:
        if row["method"] != "section_mean_static_gradient":
            continue
        summary.append(
            {
                "lane": "pressure_gradient_friction",
                "span": row["span"],
                "fit_safety": row["fit_safety"],
                "basis": row["sign_review"],
                "medium_f": row["medium_apparent_darcy_f"],
                "fine_f": row["fine_apparent_darcy_f"],
                "delta_pct": row["delta_pct_apparent_darcy_f"],
            }
        )
    for row in momentum_rows:
        summary.append(
            {
                "lane": "momentum_corrected_friction",
                "span": row["span"],
                "fit_safety": row["fit_safety"],
                "basis": f"{row['sign_review']}; {row['buoyancy_review']}",
                "medium_f": row["medium_f_corrected"],
                "fine_f": row["fine_f_corrected"],
                "delta_pct": row["delta_pct_f_corrected"],
            }
        )
    return summary


def make_readme(
    output_dir: Path,
    pressure_rows: list[dict[str, object]],
    friction_rows: list[dict[str, object]],
    momentum_rows: list[dict[str, object]],
    fit_rows: list[dict[str, object]],
) -> str:
    friction_safe = [
        row["span"]
        for row in fit_rows
        if row["lane"] == "pressure_gradient_friction" and row["fit_safety"] == "fit_safe_pressure_gradient"
    ]
    momentum_safe = [
        row["span"]
        for row in fit_rows
        if row["lane"] == "momentum_corrected_friction" and row["fit_safety"] == "fit_safe_momentum_corrected"
    ]
    flagged = [
        row["span"]
        for row in fit_rows
        if row["lane"] == "pressure_gradient_friction" and row["fit_safety"] != "fit_safe_pressure_gradient"
    ]
    return f"""# Salt2 Pressure-Only Mesh-Family Comparison

Task: `AGENT-262`

This package compares the AGENT-248 medium/fine pressure-only outputs for Salt2.
It uses existing section-pressure, segment-friction, and momentum-budget CSVs
only; no OpenFOAM extraction or solver-output mutation is performed.

## Findings

- Section-pressure sampling is present for `{len(pressure_rows)}` matched
  medium/fine stations across the six major spans.
- Pressure-gradient friction sign review admits only
  `{', '.join(friction_safe)}` as fit-safe pressure/friction rows. These rows
  are positive-loss in both medium and fine meshes with medium/fine apparent
  Darcy-friction changes below 10%.
- The pressure-gradient rows for `{', '.join(flagged)}` are not fit-safe because
  AGENT-248 flags pressure recovery or sign/noise behavior.
- Momentum-corrected friction is positive and medium/fine-consistent for
  `{', '.join(momentum_safe)}`. These are fit-safe for a momentum-corrected lane,
  but the rows with strong buoyancy correction should not be conflated with raw
  pressure-gradient friction.
- {THERMAL_BLOCKER_TEXT}

## Outputs

- `pressure_station_comparison.csv`
- `friction_mesh_comparison.csv`
- `momentum_mesh_comparison.csv`
- `fit_safety_summary.csv`
- `summary.json`

## Reproduce

```bash
python3.11 tools/analyze/build_salt2_pressure_mesh_family_comparison.py
python3.11 -m unittest tools.analyze.test_salt2_pressure_mesh_family_comparison
```

## Interpretation Boundary

This is a pressure-only fit-safety review. It does not repair reconstructed `T`,
does not admit thermal UA/HTC/Nu rows, and does not make a closure-observation
table admission change.
"""


def build_package(input_dir: Path, output_dir: Path) -> dict[str, object]:
    level_data = {level: load_level(input_dir, level) for level in LEVELS}
    pressure_rows = build_pressure_comparison(level_data)
    friction_rows = build_friction_comparison(level_data)
    momentum_rows = build_momentum_comparison(level_data)
    fit_rows = build_fit_safety_summary(friction_rows, momentum_rows)

    write_csv(
        output_dir / "pressure_station_comparison.csv",
        pressure_rows,
        [
            "label",
            "span",
            "medium_gate",
            "fine_gate",
            "medium_status",
            "fine_status",
            *[
                name
                for column in PRESSURE_COLUMNS
                for name in (
                    f"medium_{column}",
                    f"fine_{column}",
                    f"delta_{column}",
                    f"delta_pct_{column}",
                )
            ],
        ],
    )
    write_csv(
        output_dir / "friction_mesh_comparison.csv",
        friction_rows,
        [
            "span",
            "method",
            "medium_apparent_darcy_f",
            "fine_apparent_darcy_f",
            "delta_apparent_darcy_f",
            "delta_pct_apparent_darcy_f",
            "mesh_agreement",
            "medium_dp_loss_ds_pa_per_m",
            "fine_dp_loss_ds_pa_per_m",
            "medium_reynolds_number",
            "fine_reynolds_number",
            "medium_flags",
            "fine_flags",
            "sign_review",
            "fit_safety",
        ],
    )
    write_csv(
        output_dir / "momentum_mesh_comparison.csv",
        momentum_rows,
        [
            "span",
            "medium_f_corrected",
            "fine_f_corrected",
            "delta_f_corrected",
            "delta_pct_f_corrected",
            "mesh_agreement",
            "medium_f_corrected_over_flam",
            "fine_f_corrected_over_flam",
            "medium_f_raw_buoyancy_embedded",
            "fine_f_raw_buoyancy_embedded",
            "medium_buoyancy_fraction_of_raw_grad",
            "fine_buoyancy_fraction_of_raw_grad",
            "medium_inertial_grad_pa_m",
            "fine_inertial_grad_pa_m",
            "medium_Re",
            "fine_Re",
            "sign_review",
            "buoyancy_review",
            "fit_safety",
        ],
    )
    write_csv(
        output_dir / "fit_safety_summary.csv",
        fit_rows,
        ["lane", "span", "fit_safety", "basis", "medium_f", "fine_f", "delta_pct"],
    )

    summary = {
        "task_id": "AGENT-262",
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "pressure_station_rows": len(pressure_rows),
        "friction_rows": len(friction_rows),
        "momentum_rows": len(momentum_rows),
        "pressure_gradient_fit_safe_spans": [
            row["span"]
            for row in fit_rows
            if row["lane"] == "pressure_gradient_friction"
            and row["fit_safety"] == "fit_safe_pressure_gradient"
        ],
        "momentum_corrected_fit_safe_spans": [
            row["span"]
            for row in fit_rows
            if row["lane"] == "momentum_corrected_friction"
            and row["fit_safety"] == "fit_safe_momentum_corrected"
        ],
        "thermal_closure_status": "blocked",
        "thermal_blocker": THERMAL_BLOCKER_TEXT,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(
        make_readme(output_dir, pressure_rows, friction_rows, momentum_rows, fit_rows),
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    build_package(Path(args.input_dir), Path(args.output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
