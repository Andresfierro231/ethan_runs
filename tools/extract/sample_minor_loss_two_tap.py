#!/usr/bin/env python3
"""Build a two-tap minor-loss table from preserved Salt CFD reductions.

This task is a CFD postprocessing reduction, not a 1D solver run. It consumes
existing feature endpoint total-pressure losses from
`work_products/2026-07-01_claude_bend_minor_loss/` and the July 8 pressure-term
ledger, then emits a stricter minor-loss table that separates:

- diagnostic apparent feature loss, `K_apparent`;
- a local feature-loss estimate after subtracting available adjacent straight
  distributed loss, `K_local`;
- flags for recirculation-adjacent features, missing tap length, and unavailable
  feature/reducer rows.

Important limitation:
    The preserved bend CSVs do not carry a full centerline tap-to-tap feature
    length. They carry only endpoint patch states and `dz_across_feature_m`.
    Therefore this reducer subtracts a documented lower-bound straight-loss
    estimate using `abs(dz_across_feature_m)` as a tap-separation proxy. The
    resulting `K_local` is still an upper-bound estimate, but it is stricter than
    the legacy `K_apparent` that subtracted no straight loss at all. Rows make
    this status explicit through `quality_flags` and
    `straight_loss_subtraction_status`.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT / "work_products" / "2026-07-08_minor_loss_two_tap"
PRESSURE_LEDGER = ROOT / "work_products" / "2026-07-08_pressure_term_ledger" / "pressure_term_ledger.csv"
BEND_DIR = ROOT / "work_products" / "2026-07-01_claude_bend_minor_loss"

SOURCE_IDS = [
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
]

CASE_ID_BY_SOURCE = {
    "viscosity_screening_salt_test_2_jin_coarse_mesh": "salt_2",
    "viscosity_screening_salt_test_3_jin_coarse_mesh": "salt_3",
    "viscosity_screening_salt_test_4_jin_coarse_mesh": "salt_4",
}

FEATURES = {
    "corner_lower_left": {
        "feature_type": "bend/junction_corner",
        "adjacent_spans": ["left_lower_leg", "lower_leg"],
        "downstream_span": "lower_leg",
    },
    "corner_lower_right": {
        "feature_type": "bend/junction_corner",
        "adjacent_spans": ["lower_leg", "right_leg"],
        "downstream_span": "right_leg",
    },
    "corner_upper_right": {
        "feature_type": "bend/junction_corner",
        "adjacent_spans": ["right_leg", "upper_leg"],
        "downstream_span": "upper_leg",
    },
    "corner_upper_left": {
        "feature_type": "bend/junction_corner",
        "adjacent_spans": ["upper_leg", "left_upper_leg"],
        "downstream_span": "left_upper_leg",
    },
    "test_section_complex": {
        "feature_type": "connector_expansion_contraction",
        "adjacent_spans": ["left_upper_leg", "test_section_span", "left_lower_leg"],
        "downstream_span": "left_lower_leg",
    },
}


@dataclass(frozen=True)
class SpanLedger:
    source_id: str
    case_id: str
    span: str
    distributed_mechanical_loss_pa_m: float
    q_ref_pa: float
    recirculation_flag: bool
    fit_eligible: bool
    fit_use_status: str
    quality_flags: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pressure-ledger", type=Path, default=PRESSURE_LEDGER)
    parser.add_argument("--bend-dir", type=Path, default=BEND_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def fnum(value: Any, default: float = math.nan) -> float:
    try:
        if value is None:
            return default
        text = str(value).strip()
        if text == "" or text.lower() in {"nan", "none", "na"}:
            return default
        return float(text)
    except ValueError:
        return default


def boolish(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_pressure_ledger(path: Path) -> dict[tuple[str, str], SpanLedger]:
    rows = read_csv(path)
    out: dict[tuple[str, str], SpanLedger] = {}
    for row in rows:
        source_id = row["source_id"]
        span = row["span"]
        out[(source_id, span)] = SpanLedger(
            source_id=source_id,
            case_id=row.get("case_id", CASE_ID_BY_SOURCE.get(source_id, "")),
            span=span,
            distributed_mechanical_loss_pa_m=fnum(row["distributed_mechanical_loss_pa_m"], 0.0),
            q_ref_pa=fnum(row["q_ref_pa"], math.nan),
            recirculation_flag=boolish(row.get("recirculation_flag", "")),
            fit_eligible=boolish(row.get("fit_eligible", "")),
            fit_use_status=row.get("fit_use_status", ""),
            quality_flags=row.get("quality_flags", ""),
        )
    return out


def load_bend_rows(bend_dir: Path, source_id: str) -> dict[str, dict[str, str]]:
    path = bend_dir / f"bend_minor_loss_{source_id}.csv"
    if not path.exists():
        return {}
    return {row["feature"]: row for row in read_csv(path)}


def finite_or_blank(value: float) -> float | str:
    return value if math.isfinite(value) else ""


def mean(values: Sequence[float]) -> float:
    vals = [v for v in values if math.isfinite(v)]
    if not vals:
        return math.nan
    return sum(vals) / len(vals)


def compute_adjacent_straight_loss(
    source_id: str,
    feature_name: str,
    dz_across_feature_m: float,
    pressure_index: Mapping[tuple[str, str], SpanLedger],
) -> dict[str, Any]:
    feature_def = FEATURES[feature_name]
    adjacent_spans = feature_def["adjacent_spans"]
    span_rows = [pressure_index.get((source_id, span)) for span in adjacent_spans]
    available = [row for row in span_rows if row is not None]
    fit_rows = [row for row in available if row.fit_eligible and not row.recirculation_flag]
    recirc_spans = [row.span for row in available if row.recirculation_flag]
    missing_spans = [span for span, row in zip(adjacent_spans, span_rows) if row is None]

    tap_proxy_m = abs(dz_across_feature_m) if math.isfinite(dz_across_feature_m) else math.nan
    if not math.isfinite(tap_proxy_m) or tap_proxy_m <= 0.0:
        return {
            "tap_length_proxy_m": finite_or_blank(tap_proxy_m),
            "straight_loss_gradient_pa_m": "",
            "adjacent_straight_loss_subtracted_pa": 0.0,
            "straight_loss_subtraction_status": "not_subtracted_missing_tap_length",
            "straight_loss_gradient_basis": "",
            "recirculation_adjacent_spans": ";".join(recirc_spans),
            "missing_adjacent_spans": ";".join(missing_spans),
        }

    if fit_rows:
        gradient = mean([row.distributed_mechanical_loss_pa_m for row in fit_rows])
        basis = "fit_eligible_adjacent_average"
    elif available:
        gradient = mean([row.distributed_mechanical_loss_pa_m for row in available])
        basis = "diagnostic_all_adjacent_average"
    else:
        gradient = math.nan
        basis = "no_adjacent_pressure_ledger_rows"

    if not math.isfinite(gradient):
        subtracted = 0.0
        status = "not_subtracted_missing_adjacent_gradient"
    else:
        subtracted = max(gradient * tap_proxy_m, 0.0)
        status = "subtracted_minimum_dz_proxy_straight_loss"
    return {
        "tap_length_proxy_m": tap_proxy_m,
        "straight_loss_gradient_pa_m": finite_or_blank(gradient),
        "adjacent_straight_loss_subtracted_pa": subtracted,
        "straight_loss_subtraction_status": status,
        "straight_loss_gradient_basis": basis,
        "recirculation_adjacent_spans": ";".join(recirc_spans),
        "missing_adjacent_spans": ";".join(missing_spans),
    }


def build_feature_row(
    source_id: str,
    feature_name: str,
    bend_row: Mapping[str, str] | None,
    pressure_index: Mapping[tuple[str, str], SpanLedger],
    bend_dir: Path,
) -> dict[str, Any]:
    feature_def = FEATURES[feature_name]
    case_id = CASE_ID_BY_SOURCE.get(source_id, "")
    downstream_span = feature_def["downstream_span"]
    downstream = pressure_index.get((source_id, downstream_span))
    base = {
        "source_id": source_id,
        "case_id": case_id,
        "run_class": "mainline_jin_continuation",
        "mesh_level": "coarse",
        "mesh_status": "coarse_no_gci",
        "feature": feature_name,
        "feature_type": feature_def["feature_type"],
        "downstream_span": downstream_span,
        "adjacent_spans": ";".join(feature_def["adjacent_spans"]),
        "join_key": f"{source_id}:{feature_name}:{downstream_span}",
        "pressure_ledger_join_key": f"{source_id}:{downstream_span}",
        "source_bend_minor_loss_csv": rel(bend_dir / f"bend_minor_loss_{source_id}.csv"),
    }
    if bend_row is None:
        base.update(
            {
                "status": "missing_preserved_two_tap_feature_output",
                "K_apparent": "",
                "K_local": "",
                "feature_total_pressure_loss_pa": "",
                "local_minor_loss_pa": "",
                "q_ref_local_pa": finite_or_blank(downstream.q_ref_pa if downstream else math.nan),
                "quality_flags": "feature_not_in_preserved_bend_minor_loss;requires_raw_two_tap_extraction;coarse_no_gci",
                "fit_eligible": "no",
                "validation_eligible": "yes",
                "notes": "Expected feature is present in case-analysis profile but absent from preserved July 1 bend-minor-loss CSV.",
            }
        )
        return base

    abs_loss_pa = fnum(bend_row.get("abs_loss_pa"), math.nan)
    q_ref_pa = fnum(bend_row.get("q_ref_pa"), math.nan)
    dz = fnum(bend_row.get("dz_across_feature_m"), math.nan)
    straight = compute_adjacent_straight_loss(source_id, feature_name, dz, pressure_index)
    subtracted = fnum(straight["adjacent_straight_loss_subtracted_pa"], 0.0)
    local_loss_pa = max(abs_loss_pa - subtracted, 0.0) if math.isfinite(abs_loss_pa) else math.nan
    k_apparent = abs_loss_pa / q_ref_pa if math.isfinite(abs_loss_pa) and q_ref_pa > 0 else math.nan
    k_local = local_loss_pa / q_ref_pa if math.isfinite(local_loss_pa) and q_ref_pa > 0 else math.nan

    flags = ["coarse_no_gci", "tap_length_proxy_abs_dz_not_centerline_length", "K_local_still_upper_bound"]
    if straight["recirculation_adjacent_spans"]:
        flags.append("recirculation_adjacent")
    if feature_name == "corner_upper_left":
        flags.append("downstream_span_recirculation_invalid_single_stream")
    if bend_row.get("status") != "computed":
        flags.append(f"legacy_status_{bend_row.get('status')}")
    if str(straight["straight_loss_subtraction_status"]).startswith("not_subtracted"):
        flags.append(str(straight["straight_loss_subtraction_status"]))

    base.update(
        {
            "status": "computed_from_preserved_two_tap_feature_rows",
            "start_patch": bend_row.get("start_patch", ""),
            "end_patch": bend_row.get("end_patch", ""),
            "delta_p_rgh_pa": finite_or_blank(fnum(bend_row.get("delta_p_rgh_pa"))),
            "buoyancy_term_pa": finite_or_blank(fnum(bend_row.get("buoyancy_term_pa"))),
            "delta_q_dyn_pa": finite_or_blank(fnum(bend_row.get("delta_q_dyn_pa"))),
            "feature_total_pressure_loss_pa": finite_or_blank(abs_loss_pa),
            "adjacent_straight_loss_subtracted_pa": finite_or_blank(subtracted),
            "local_minor_loss_pa": finite_or_blank(local_loss_pa),
            "q_ref_local_pa": finite_or_blank(q_ref_pa),
            "K_apparent": finite_or_blank(k_apparent),
            "K_local": finite_or_blank(k_local),
            "legacy_K_minor_loss": finite_or_blank(fnum(bend_row.get("K_minor_loss"))),
            "q_ref_basis": bend_row.get("q_ref_basis", ""),
            "tap_length_proxy_m": straight["tap_length_proxy_m"],
            "straight_loss_gradient_pa_m": straight["straight_loss_gradient_pa_m"],
            "straight_loss_gradient_basis": straight["straight_loss_gradient_basis"],
            "straight_loss_subtraction_status": straight["straight_loss_subtraction_status"],
            "recirculation_adjacent_spans": straight["recirculation_adjacent_spans"],
            "missing_adjacent_spans": straight["missing_adjacent_spans"],
            "downstream_span_fit_use_status": downstream.fit_use_status if downstream else "",
            "fit_eligible": "no",
            "validation_eligible": "yes",
            "quality_flags": ";".join(flags),
            "notes": (
                "K_apparent reproduces the preserved total-pressure feature loss. "
                "K_local subtracts a minimum adjacent straight-loss estimate based on abs(dz); "
                "full centerline tap length is unavailable in preserved evidence."
            ),
        }
    )
    return base


FIELDNAMES = [
    "source_id",
    "case_id",
    "run_class",
    "mesh_level",
    "mesh_status",
    "feature",
    "feature_type",
    "downstream_span",
    "adjacent_spans",
    "join_key",
    "pressure_ledger_join_key",
    "status",
    "start_patch",
    "end_patch",
    "delta_p_rgh_pa",
    "buoyancy_term_pa",
    "delta_q_dyn_pa",
    "feature_total_pressure_loss_pa",
    "adjacent_straight_loss_subtracted_pa",
    "local_minor_loss_pa",
    "q_ref_local_pa",
    "K_apparent",
    "K_local",
    "legacy_K_minor_loss",
    "q_ref_basis",
    "tap_length_proxy_m",
    "straight_loss_gradient_pa_m",
    "straight_loss_gradient_basis",
    "straight_loss_subtraction_status",
    "recirculation_adjacent_spans",
    "missing_adjacent_spans",
    "downstream_span_fit_use_status",
    "fit_eligible",
    "validation_eligible",
    "quality_flags",
    "source_bend_minor_loss_csv",
    "notes",
]


def build_rows(pressure_ledger: Path = PRESSURE_LEDGER, bend_dir: Path = BEND_DIR) -> list[dict[str, Any]]:
    pressure_index = load_pressure_ledger(pressure_ledger)
    rows: list[dict[str, Any]] = []
    for source_id in SOURCE_IDS:
        bend_rows = load_bend_rows(bend_dir, source_id)
        for feature_name in FEATURES:
            rows.append(build_feature_row(source_id, feature_name, bend_rows.get(feature_name), pressure_index, bend_dir))
    return rows


def summarize(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    computed = [row for row in rows if row["status"] == "computed_from_preserved_two_tap_feature_rows"]
    unavailable = [row for row in rows if row["status"] != "computed_from_preserved_two_tap_feature_rows"]
    k_local_values = [fnum(row.get("K_local")) for row in computed if math.isfinite(fnum(row.get("K_local")))]
    k_app_values = [fnum(row.get("K_apparent")) for row in computed if math.isfinite(fnum(row.get("K_apparent")))]
    return {
        "row_count": len(rows),
        "computed_rows": len(computed),
        "unavailable_rows": len(unavailable),
        "source_ids": len({row["source_id"] for row in rows}),
        "features": sorted({row["feature"] for row in rows}),
        "K_apparent_range": [min(k_app_values), max(k_app_values)] if k_app_values else [],
        "K_local_range": [min(k_local_values), max(k_local_values)] if k_local_values else [],
        "quality_flags": sorted({flag for row in rows for flag in str(row.get("quality_flags", "")).split(";") if flag}),
    }


def write_readme(output_dir: Path, summary: Mapping[str, Any]) -> None:
    text = f"""# Minor Loss Two-Tap Ledger

Generated: `{datetime.now().isoformat(timespec="seconds")}`
Task: `TODO-MINOR-LOSS-TWO-TAP`

## Scope

This package converts preserved Salt 2/3/4 Jin two-interface feature losses into
a stricter minor-loss table. It is a 3D CFD postprocessing reduction, not a 1D
solver calculation.

## Method

For preserved corner rows, the legacy feature extractor already computed:

```text
P0_proxy = <p_rgh> + 0.5 <rho> |<U>|^2
feature_total_pressure_loss = -(Delta p_rgh + buoyancy_term + Delta q_dyn)
K_apparent = feature_total_pressure_loss / q_ref_local
```

This pass joins each feature to the July 8 pressure ledger, computes an
available adjacent straight-loss estimate, and emits:

```text
local_minor_loss = max(feature_total_pressure_loss - adjacent_straight_loss, 0)
K_local = local_minor_loss / q_ref_local
```

Because the preserved feature rows do not contain full centerline tap-to-tap
length, `adjacent_straight_loss` uses `abs(dz_across_feature_m)` as a minimum
tap-length proxy. Therefore `K_local` remains an upper-bound estimate and is
flagged as such.

## Outputs

- `minor_loss_two_tap.csv`
- `minor_loss_two_tap.json`
- `summary.json`
- `README.md`

## Counts

- rows: `{summary['row_count']}`
- computed preserved corner rows: `{summary['computed_rows']}`
- unavailable expected feature rows: `{summary['unavailable_rows']}`

## Scientific Use

- Use `K_apparent` only as a diagnostic value that reproduces the preserved
  total-pressure feature loss without adjacent straight-loss subtraction.
- Use `K_local` as the current best local minor-loss upper-bound estimate.
- Do not use rows with `recirculation_adjacent` as ordinary single-stream
  closure fits.
- The `test_section_complex` rows are intentionally marked unavailable because
  the preserved July 1 bend-minor-loss output did not include that feature.

## Source Evidence

- Pressure ledger: `{rel(PRESSURE_LEDGER)}`
- Preserved bend/minor rows: `{rel(BEND_DIR)}/bend_minor_loss_*.csv`

## Reproduce

```bash
cd {ROOT}
python tools/extract/sample_minor_loss_two_tap.py
python -m pytest tools/extract/test_sample_minor_loss_two_tap.py -q
```
"""
    (output_dir / "README.md").write_text(text, encoding="utf-8")


def build_package(output_dir: Path = DEFAULT_OUTPUT_DIR, pressure_ledger: Path = PRESSURE_LEDGER, bend_dir: Path = BEND_DIR) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = build_rows(pressure_ledger, bend_dir)
    summary = summarize(rows)
    csv_path = output_dir / "minor_loss_two_tap.csv"
    json_path = output_dir / "minor_loss_two_tap.json"
    summary_path = output_dir / "summary.json"
    write_csv(csv_path, rows, FIELDNAMES)
    write_json(json_path, {"rows": rows, "fieldnames": FIELDNAMES})
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task": "TODO-MINOR-LOSS-TWO-TAP",
        "inputs": {
            "pressure_ledger": rel(pressure_ledger),
            "bend_minor_loss_dir": rel(bend_dir),
        },
        "outputs": {
            "csv": rel(csv_path),
            "json": rel(json_path),
        },
        "summary": summary,
        "limitations": [
            "Preserved feature rows do not include full centerline tap-to-tap length.",
            "K_local subtracts only a minimum abs(dz)-proxy adjacent straight loss and remains an upper-bound estimate.",
            "Test-section complex/reducer rows are unavailable until raw feature extraction is rerun for those taps.",
            "Rows adjacent to recirculation spans are validation diagnostics, not ordinary single-stream K closures.",
            "All rows remain coarse_no_gci.",
        ],
    }
    write_json(summary_path, payload)
    write_readme(output_dir, summary)
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args() if argv is None else parse_args()
    payload = build_package(args.output_dir, args.pressure_ledger, args.bend_dir)
    print(json.dumps({"output_dir": rel(args.output_dir), "summary": payload["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
