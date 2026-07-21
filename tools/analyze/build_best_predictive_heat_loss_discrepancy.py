#!/usr/bin/env python3
"""Compare best current predictive-style heat losses against CFD by leg."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import socket
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "AGENT-356"
BEST_VARIANT = "F1_heater_only"

DEFAULT_OUTPUT = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_best_predictive_heat_loss_discrepancy"
)

FORWARD_RESULTS = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_full/forward_v0_results.csv"
)
FORWARD_SEGMENTS = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_full/forward_v0_segment_states.csv"
)
SOLVE_CASE_COMPARISON = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_vs_fast_scan_comparison.csv"
)
SECTION_HEAT_BALANCE = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/section_heat_balance.csv"
)
AGENT350_SEGMENTS = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_3d_1d_heat_loss_alignment/heat_loss_alignment_by_segment.csv"
)
BOUNDARY_MATRIX = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_boundary_model_task_matrix/boundary_model_task_matrix.csv"
)

SOURCE_PATHS = [
    FORWARD_RESULTS,
    FORWARD_SEGMENTS,
    SOLVE_CASE_COMPARISON,
    SECTION_HEAT_BALANCE,
    AGENT350_SEGMENTS,
    BOUNDARY_MATRIX,
]

PARENT_TO_LEG = {
    "left_lower_vertical": "upcomer",
    "test_section": "upcomer",
    "left_upper_vertical": "upcomer",
    "top_horizontal_inlet": "junction",
    "top_horizontal_exit": "junction",
    "bottom_horizontal_inlet": "junction",
    "bottom_horizontal_exit": "junction",
    "cooled_incline_pre_hx": "cooling_branch",
    "cooled_incline_hx_active": "cooling_branch",
    "cooled_incline_post_hx": "cooling_branch",
    "right_vertical": "downcomer",
    "heated_incline": "lower_leg",
}

LEG_ORDER = {
    "lower_leg": 0,
    "upcomer": 1,
    "cooling_branch": 2,
    "downcomer": 3,
    "junction": 4,
}

LEG_LABEL = {
    "lower_leg": "heated lower leg",
    "upcomer": "upcomer and test-section leg",
    "cooling_branch": "upper cooling branch",
    "downcomer": "right downcomer",
    "junction": "junctions and horizontal connectors",
}

LEG_MODEL_CHANGE = {
    "lower_leg": (
        "Separate heater realization from lower-leg passive loss. Current net heat can look close because "
        "heater over-input and ambient over-loss cancel; model heater efficiency/source contract and wall loss separately."
    ),
    "upcomer": (
        "Keep heater-only/test-section source policy as default, then reduce or remap upcomer external loss using "
        "wall-adjacent/external-boundary dictionaries rather than bulk-temperature ambient loss."
    ),
    "cooling_branch": (
        "Separate active HX/cooler duty from passive upper-leg wall loss. Replace imposed cooler duty with a "
        "setup-only UA/effectiveness model, and keep passive cooling-branch wall loss in the external-boundary lane."
    ),
    "downcomer": (
        "Implement first-class external boundary h/Ta/Tsur/emissivity/layer handling with wall/shell drive; current "
        "bulk-driven ambient loss over-removes heat in the downcomer."
    ),
    "junction": (
        "Add junction/stub/horizontal-connector heat-loss coverage. Current 1D ambient model under-removes junction heat "
        "relative to CFD realized wallHeatFlux by the largest W margin."
    ),
}

DISCREPANCY_COLUMNS = [
    "case_id",
    "source_id",
    "best_model_variant",
    "leg",
    "leg_label",
    "model_source_W",
    "model_hx_loss_W",
    "model_ambient_loss_W",
    "model_total_loss_W",
    "model_net_to_fluid_W",
    "cfd_imposed_source_W",
    "cfd_imposed_loss_W",
    "cfd_imposed_net_to_fluid_W",
    "cfd_realized_source_W",
    "cfd_realized_loss_W",
    "cfd_realized_net_to_fluid_W",
    "model_minus_cfd_realized_loss_W",
    "model_minus_cfd_imposed_loss_W",
    "model_minus_cfd_realized_net_W",
    "loss_discrepancy_fraction_of_heater",
    "heat_loss_bias",
    "net_bias",
    "priority",
    "recommended_model_change",
    "runtime_status",
    "source_paths",
]

CASE_COLUMNS = [
    "case_id",
    "source_id",
    "best_model_variant",
    "heater_power_W",
    "model_total_loss_W",
    "cfd_realized_total_loss_W",
    "cfd_imposed_total_loss_W",
    "model_minus_cfd_realized_total_loss_W",
    "model_net_to_fluid_W",
    "cfd_realized_net_to_fluid_W",
    "aggregate_net_residual_W",
    "largest_over_loss_leg",
    "largest_under_loss_leg",
    "largest_abs_loss_discrepancy_leg",
    "case_interpretation",
]

CHANGE_COLUMNS = [
    "change_id",
    "model_area",
    "applies_to_leg",
    "priority",
    "observed_discrepancy",
    "required_change",
    "guardrail",
    "source_paths",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column, "")) for column in columns})


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return round(value, 9)
    return value


def fnum(value: Any, default: float = 0.0) -> float:
    if value in ("", None):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def source_join(*paths: Path) -> str:
    return ";".join(rel(path) for path in paths)


def bias(value: float, tolerance: float = 1e-6) -> str:
    if value > tolerance:
        return "model_over_loses_heat"
    if value < -tolerance:
        return "model_under_loses_heat"
    return "model_matches_cfd_within_tolerance"


def priority_for(leg: str, discrepancy: float, heater_power: float) -> str:
    frac = abs(discrepancy) / heater_power if heater_power else 0.0
    if leg == "junction" or frac >= 0.1:
        return "high"
    if frac >= 0.03:
        return "medium"
    return "low"


def best_model_results() -> dict[str, dict[str, str]]:
    return {
        row["case_id"]: row
        for row in read_csv(FORWARD_RESULTS)
        if row["variant_id"] == BEST_VARIANT and row["engine"] == "solve_case"
    }


def aggregate_model_by_leg() -> dict[tuple[str, str], dict[str, Any]]:
    rows: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "model_source_W": 0.0,
            "model_hx_loss_W": 0.0,
            "model_ambient_loss_W": 0.0,
            "source_id": "",
        }
    )
    for row in read_csv(FORWARD_SEGMENTS):
        if row["variant_id"] != BEST_VARIANT or row["engine"] != "solve_case":
            continue
        leg = PARENT_TO_LEG[row["parent_segment"]]
        item = rows[(row["case_id"], leg)]
        item["source_id"] = row["source_id"]
        item["model_source_W"] += fnum(row["Q_source_W"])
        item["model_hx_loss_W"] += fnum(row["Q_hx_sink_W"])
        item["model_ambient_loss_W"] += fnum(row["Q_ambient_W"])
    for item in rows.values():
        item["model_total_loss_W"] = item["model_hx_loss_W"] + item["model_ambient_loss_W"]
        item["model_net_to_fluid_W"] = item["model_source_W"] - item["model_total_loss_W"]
    return rows


def aggregate_cfd_by_leg() -> dict[tuple[str, str], dict[str, Any]]:
    rows: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "cfd_imposed_source_W": 0.0,
            "cfd_imposed_loss_W": 0.0,
            "cfd_realized_source_W": 0.0,
            "cfd_realized_loss_W": 0.0,
            "source_id": "",
        }
    )
    for row in read_csv(SECTION_HEAT_BALANCE):
        key = (row["case_id"], row["one_d_segment"])
        item = rows[key]
        item["source_id"] = row["source_id"]
        item["cfd_imposed_source_W"] += fnum(row["imposed_source_W"])
        item["cfd_imposed_loss_W"] += fnum(row["imposed_loss_W"])
        item["cfd_realized_source_W"] += fnum(row["realized_source_W"])
        item["cfd_realized_loss_W"] += fnum(row["realized_loss_W"])
    for item in rows.values():
        item["cfd_imposed_net_to_fluid_W"] = item["cfd_imposed_source_W"] - item["cfd_imposed_loss_W"]
        item["cfd_realized_net_to_fluid_W"] = item["cfd_realized_source_W"] - item["cfd_realized_loss_W"]
    return rows


def discrepancy_rows() -> list[dict[str, Any]]:
    model = aggregate_model_by_leg()
    cfd = aggregate_cfd_by_leg()
    results = best_model_results()
    rows: list[dict[str, Any]] = []
    for case_id in sorted(results):
        heater_power = fnum(results[case_id]["source_total_input_W"])
        for leg in sorted(LEG_ORDER, key=LEG_ORDER.get):
            m = model[(case_id, leg)]
            c = cfd[(case_id, leg)]
            loss_delta = m["model_total_loss_W"] - c["cfd_realized_loss_W"]
            imposed_loss_delta = m["model_total_loss_W"] - c["cfd_imposed_loss_W"]
            net_delta = m["model_net_to_fluid_W"] - c["cfd_realized_net_to_fluid_W"]
            rows.append(
                {
                    "case_id": case_id,
                    "source_id": m["source_id"] or c["source_id"],
                    "best_model_variant": BEST_VARIANT,
                    "leg": leg,
                    "leg_label": LEG_LABEL[leg],
                    "model_source_W": m["model_source_W"],
                    "model_hx_loss_W": m["model_hx_loss_W"],
                    "model_ambient_loss_W": m["model_ambient_loss_W"],
                    "model_total_loss_W": m["model_total_loss_W"],
                    "model_net_to_fluid_W": m["model_net_to_fluid_W"],
                    "cfd_imposed_source_W": c["cfd_imposed_source_W"],
                    "cfd_imposed_loss_W": c["cfd_imposed_loss_W"],
                    "cfd_imposed_net_to_fluid_W": c["cfd_imposed_net_to_fluid_W"],
                    "cfd_realized_source_W": c["cfd_realized_source_W"],
                    "cfd_realized_loss_W": c["cfd_realized_loss_W"],
                    "cfd_realized_net_to_fluid_W": c["cfd_realized_net_to_fluid_W"],
                    "model_minus_cfd_realized_loss_W": loss_delta,
                    "model_minus_cfd_imposed_loss_W": imposed_loss_delta,
                    "model_minus_cfd_realized_net_W": net_delta,
                    "loss_discrepancy_fraction_of_heater": loss_delta / heater_power if heater_power else "",
                    "heat_loss_bias": bias(loss_delta),
                    "net_bias": bias(-net_delta),
                    "priority": priority_for(leg, loss_delta, heater_power),
                    "recommended_model_change": LEG_MODEL_CHANGE[leg],
                    "runtime_status": "best_current_predictive_style_imposed_cooler_not_final_predictive_hx",
                    "source_paths": source_join(FORWARD_SEGMENTS, FORWARD_RESULTS, SECTION_HEAT_BALANCE),
                }
            )
    return rows


def case_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    results = best_model_results()
    for row in rows:
        by_case[row["case_id"]].append(row)
    summaries: list[dict[str, Any]] = []
    for case_id, items in sorted(by_case.items()):
        over = max(items, key=lambda row: fnum(row["model_minus_cfd_realized_loss_W"]))
        under = min(items, key=lambda row: fnum(row["model_minus_cfd_realized_loss_W"]))
        absmax = max(items, key=lambda row: abs(fnum(row["model_minus_cfd_realized_loss_W"])))
        model_loss = sum(fnum(row["model_total_loss_W"]) for row in items)
        cfd_realized_loss = sum(fnum(row["cfd_realized_loss_W"]) for row in items)
        cfd_imposed_loss = sum(fnum(row["cfd_imposed_loss_W"]) for row in items)
        model_net = sum(fnum(row["model_net_to_fluid_W"]) for row in items)
        cfd_net = sum(fnum(row["cfd_realized_net_to_fluid_W"]) for row in items)
        summaries.append(
            {
                "case_id": case_id,
                "source_id": items[0]["source_id"],
                "best_model_variant": BEST_VARIANT,
                "heater_power_W": fnum(results[case_id]["source_total_input_W"]),
                "model_total_loss_W": model_loss,
                "cfd_realized_total_loss_W": cfd_realized_loss,
                "cfd_imposed_total_loss_W": cfd_imposed_loss,
                "model_minus_cfd_realized_total_loss_W": model_loss - cfd_realized_loss,
                "model_net_to_fluid_W": model_net,
                "cfd_realized_net_to_fluid_W": cfd_net,
                "aggregate_net_residual_W": model_net - cfd_net,
                "largest_over_loss_leg": f"{over['leg']}:{over['model_minus_cfd_realized_loss_W']}",
                "largest_under_loss_leg": f"{under['leg']}:{under['model_minus_cfd_realized_loss_W']}",
                "largest_abs_loss_discrepancy_leg": f"{absmax['leg']}:{absmax['model_minus_cfd_realized_loss_W']}",
                "case_interpretation": (
                    "Aggregate heat balance is much closer than the leg distribution; use leg rows to fix model form."
                ),
            }
        )
    return summaries


def change_recommendations(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_leg: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_leg[row["leg"]].append(row)
    output: list[dict[str, Any]] = []
    for leg in sorted(by_leg, key=LEG_ORDER.get):
        items = by_leg[leg]
        mean_delta = sum(fnum(row["model_minus_cfd_realized_loss_W"]) for row in items) / len(items)
        max_abs = max(items, key=lambda row: abs(fnum(row["model_minus_cfd_realized_loss_W"])))
        model_area = {
            "lower_leg": "heater realization plus lower-leg wall loss",
            "upcomer": "test-section/upcomer source and wall loss",
            "cooling_branch": "cooler/HX plus upper-leg passive wall loss",
            "downcomer": "external boundary wall-drive model",
            "junction": "junction/stub heat-loss coverage",
        }[leg]
        output.append(
            {
                "change_id": f"CHG-{LEG_ORDER[leg] + 1}",
                "model_area": model_area,
                "applies_to_leg": leg,
                "priority": priority_for(leg, mean_delta, fnum(best_model_results()["salt_2"]["source_total_input_W"])),
                "observed_discrepancy": (
                    f"mean model-minus-CFD-realized loss = {mean_delta:.3f} W; "
                    f"largest absolute case = {max_abs['case_id']} ({max_abs['model_minus_cfd_realized_loss_W']} W)"
                ),
                "required_change": LEG_MODEL_CHANGE[leg],
                "guardrail": (
                    "Do not use realized CFD wallHeatFlux, CFD mdot, or validation temperatures as predictive runtime inputs; "
                    "fit only declared setup-only or train-only parameters and score Salt3/Salt4 without refit."
                ),
                "source_paths": source_join(FORWARD_SEGMENTS, SECTION_HEAT_BALANCE, BOUNDARY_MATRIX),
            }
        )
    return output


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_manifest() -> list[dict[str, Any]]:
    role = {
        FORWARD_RESULTS: "best model solve_case results and heater/cooler totals",
        FORWARD_SEGMENTS: "best model per-segment source/HX/ambient losses",
        SOLVE_CASE_COMPARISON: "solve_case authority over fast_scan",
        SECTION_HEAT_BALANCE: "CFD imposed/realized heat by comparison leg",
        AGENT350_SEGMENTS: "prior diagnostic heat-loss alignment context",
        BOUNDARY_MATRIX: "model-change task mapping and guardrails",
    }
    rows = []
    for path in SOURCE_PATHS:
        rows.append(
            {
                "source_path": rel(path),
                "exists": path.exists(),
                "row_count": len(read_csv(path)) if path.suffix == ".csv" else "",
                "sha256": sha256(path) if path.exists() else "",
                "role": role[path],
            }
        )
    return rows


def write_docs(out: Path, summary: dict[str, Any], cases: list[dict[str, Any]], changes: list[dict[str, Any]]) -> None:
    case_lines = "\n".join(
        f"- `{row['case_id']}`: model total loss `{float(row['model_total_loss_W']):.3f} W`, "
        f"CFD realized total loss `{float(row['cfd_realized_total_loss_W']):.3f} W`, "
        f"largest discrepancy `{row['largest_abs_loss_discrepancy_leg']}`."
        for row in cases
    )
    change_lines = "\n".join(
        f"- `{row['applies_to_leg']}` ({row['priority']}): {row['observed_discrepancy']}."
        for row in changes
    )
    readme = f"""---
provenance:
  - {rel(FORWARD_RESULTS)}
  - {rel(FORWARD_SEGMENTS)}
  - {rel(SECTION_HEAT_BALANCE)}
tags: [thermal-parity, forward-model, heat-loss, thesis-source]
related:
  - work_products/2026-07/2026-07-14/2026-07-14_3d_1d_heat_loss_alignment/README.md
  - operational_notes/maps/forward-predictive-model.md
task: {TASK_ID}
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Best Predictive Heat-Loss Discrepancy

## Open First

1. `presentation_brief.md` — one-page meeting/presentation version.
2. `best_predictive_leg_heat_loss_discrepancy.csv` — main numerical table.
3. `model_change_recommendations.csv` — what to change in the 1D model.
4. `repeatability_and_refinement_guide.md` — how to rerun and reuse after model
   updates.
5. `thesis_reuse_index.md` — thesis/presentation wording and claim boundaries.

## Model Compared

The comparison uses `solve_case` `{BEST_VARIANT}` as the best current
predictive-style thermal model: heater-only source with imposed cooler duty.
This is the current best executable model for this comparison, but it is not a
final predictive HX closure because it still consumes imposed cooler duty.

## Main Result

Aggregate heat balance is much closer than the leg-by-leg heat-loss
distribution. The model over-loses heat in the cooling branch, downcomer, lower
leg, and upcomer, while it strongly under-loses heat in the junction/stub
connector lane.

The key table is `best_predictive_leg_heat_loss_discrepancy.csv`. The short
presentation finding is: **the current model's total heat balance looks close
because pipe-leg over-loss cancels junction/stub under-loss.**

## Case Summary

{case_lines}

## Model-Change Summary

{change_lines}

## Repeatability

Regenerate the package from repo root with:

```bash
python3.11 tools/analyze/build_best_predictive_heat_loss_discrepancy.py
python3.11 -m unittest tools.analyze.test_best_predictive_heat_loss_discrepancy
```

The script consumes only existing work-product CSVs and writes only this package
directory. It does not run OpenFOAM, touch scheduler state, mutate native CFD
outputs, or edit external Fluid source.

## Files

- `best_predictive_leg_heat_loss_discrepancy.csv`
- `best_predictive_case_heat_loss_summary.csv`
- `model_change_recommendations.csv`
- `presentation_brief.md`
- `repeatability_and_refinement_guide.md`
- `thesis_reuse_index.md`
- `methodology.md`
- `thesis_notes.md`
- `source_manifest.csv`
- `summary.json`
- `README.md`
"""
    (out / "README.md").write_text(readme, encoding="utf-8")

    method = f"""# Methodology

## Leg Aggregation

Fluid `solve_case` segment states for `{BEST_VARIANT}` are aggregated into the
same five comparison groups used by the CFD heat ledger:

- `lower_leg`: heated incline.
- `upcomer`: left lower vertical, test section, and left upper vertical.
- `cooling_branch`: cooled incline pre-HX, active HX, and post-HX.
- `downcomer`: right vertical.
- `junction`: top/bottom horizontal connectors and junction-adjacent pieces.

For each leg:

```text
model_total_loss = Q_hx_sink + Q_ambient
model_net_to_fluid = Q_source - Q_hx_sink - Q_ambient
loss_discrepancy = model_total_loss - CFD_realized_loss
```

Positive loss discrepancy means the 1D model loses too much heat from that leg.
Negative means the 1D model does not lose enough heat from that leg.

## Inputs

- Model leg losses: `{rel(FORWARD_SEGMENTS)}` filtered to `engine=solve_case`
  and `variant_id={BEST_VARIANT}`.
- Model case totals and source contract: `{rel(FORWARD_RESULTS)}`.
- CFD realized/imposed heat by comparison leg: `{rel(SECTION_HEAT_BALANCE)}`.
- Prior full diagnostic heat-path alignment: `{rel(AGENT350_SEGMENTS)}`.
- Model-change guardrails: `{rel(BOUNDARY_MATRIX)}`.

## Output Semantics

- `model_total_loss_W = model_hx_loss_W + model_ambient_loss_W`.
- `model_minus_cfd_realized_loss_W > 0`: 1D loses too much heat from that leg.
- `model_minus_cfd_realized_loss_W < 0`: 1D loses too little heat from that leg.
- `model_minus_cfd_realized_net_W` keeps source placement visible so heater
  over-input and wall-loss errors cannot cancel silently.

## Guardrails

This is a predictive-style discrepancy audit, not a new closure fit. The model
uses imposed cooler duty, so the package is not final predictive-HX evidence.
Realized CFD `wallHeatFlux` is used only as a comparison target. CFD mdot,
realized `wallHeatFlux`, and validation temperatures are not admitted as
runtime predictive inputs.

## Updating After 1D Refinement

When a new 1D model variant lands, rerun or clone this package with the new
variant ID in `BEST_VARIANT`, confirm the leg aggregation still maps every Fluid
parent segment, and compare the new `model_change_recommendations.csv` against
this package. A useful refinement should reduce the junction under-loss without
creating a larger pipe-leg over-loss or using forbidden runtime targets.
"""
    (out / "methodology.md").write_text(method, encoding="utf-8")

    thesis = "# Thesis Notes\n\n"
    thesis += "Use this package to explain why a low aggregate temperature error can still hide wrong heat-loss placement.\n\n"
    thesis += "Best wording: the current best predictive-style model roughly balances total heat because errors cancel by leg; it over-removes heat from several pipe legs and under-removes heat in junction/stub regions.\n\n"
    thesis += "Model changes needed:\n\n"
    for row in changes:
        thesis += f"- {row['model_area']}: {row['required_change']}\n"
    (out / "thesis_notes.md").write_text(thesis, encoding="utf-8")

    presentation = f"""# Presentation Brief

## Slide Title

Where the current 1D model loses heat versus where CFD loses heat

## One-Sentence Takeaway

The best current predictive-style model (`{BEST_VARIANT}`) has a near-closed
aggregate heat balance, but the heat is lost in the wrong places: pipe legs
over-lose heat while junction/stub regions under-lose heat.

## Numbers to Show

{case_lines}

## Main Visual to Make

Use `best_predictive_leg_heat_loss_discrepancy.csv` to make a grouped bar chart:

- x-axis: lower leg, upcomer/test-section, cooling branch, downcomer, junction.
- bars: model total loss, CFD realized loss.
- annotate: model-minus-CFD realized loss.

## Speaker Notes

- This is the current best executable predictive-style model, but not final
  predictive HX because imposed cooler duty is still consumed.
- The model over-loses heat in lower leg, upcomer, cooling branch, and downcomer.
- The model under-loses heat most strongly in junction/stub/horizontal
  connector regions.
- The next 1D refinement should add junction heat-loss coverage and replace
  bulk-driven ambient losses with wall/shell external-boundary dictionaries.
- Do not present this as validation of the 1D heat-loss model. Present it as a
  diagnostic that tells us exactly what to fix.
"""
    (out / "presentation_brief.md").write_text(presentation, encoding="utf-8")

    repeatability = f"""# Repeatability and 1D Refinement Guide

## Exact Rerun

From repo root:

```bash
python3.11 tools/analyze/build_best_predictive_heat_loss_discrepancy.py
python3.11 -m unittest tools.analyze.test_best_predictive_heat_loss_discrepancy
```

Expected row counts:

- `best_predictive_leg_heat_loss_discrepancy.csv`: 15 rows.
- `best_predictive_case_heat_loss_summary.csv`: 3 rows.
- `model_change_recommendations.csv`: 5 rows.

## Dependencies

The package uses only existing CSV/markdown work products:

- `{rel(FORWARD_RESULTS)}`
- `{rel(FORWARD_SEGMENTS)}`
- `{rel(SOLVE_CASE_COMPARISON)}`
- `{rel(SECTION_HEAT_BALANCE)}`
- `{rel(AGENT350_SEGMENTS)}`
- `{rel(BOUNDARY_MATRIX)}`

No native CFD solver outputs, Slurm jobs, or external Fluid source edits are
required to reproduce this package.

## How to Reuse After Refining the 1D Model

1. Land the new 1D model outputs as a new forward package with per-segment
   `Q_source_W`, `Q_hx_sink_W`, and `Q_ambient_W` or equivalent columns.
2. Update or parameterize `BEST_VARIANT` and the forward-results/segment-state
   paths in the builder.
3. Confirm every Fluid `parent_segment` maps to one of the five comparison legs.
4. Rerun the builder and tests.
5. Compare the new leg discrepancies to this baseline:
   - junction under-loss should shrink;
   - pipe-leg over-loss should not grow;
   - aggregate heat balance should not be the only success metric;
   - Salt3 and Salt4 should be scored without refit if Salt2 trains a scalar.

## What Not To Do

- Do not use realized CFD `wallHeatFlux` as a runtime predictive input.
- Do not use CFD mdot as a runtime predictive input.
- Do not call imposed cooler duty final predictive HX.
- Do not hide junction or heater errors inside one global ambient multiplier.
"""
    (out / "repeatability_and_refinement_guide.md").write_text(repeatability, encoding="utf-8")

    thesis_index = f"""# Thesis Reuse Index

## Where This Fits

Use this package in the master's thesis as the bridge between:

- diagnostic CFD-to-1D heat-path accounting, and
- the next predictive 1D boundary/HX/refinement work.

It belongs in a chapter or section on thermal model-form diagnosis, not in a
final validation section.

## Thesis Claim Status

| Claim | Status | Use |
| --- | --- | --- |
| Current best predictive-style model can be compared by physical heat-loss leg. | Supported | Methods/results. |
| Aggregate heat balance hides wrong-location heat loss. | Supported by this package | Presentation and thesis result. |
| Junction/stub regions are the largest under-loss lane. | Supported diagnostic | Model-refinement target. |
| Pipe legs over-lose heat under the current ambient model. | Supported diagnostic | External-boundary target. |
| The model is final predictive HX. | Not supported | Do not claim. |

## Canonical Citation Inside Repo

Use:

`work_products/2026-07/2026-07-14/2026-07-14_best_predictive_heat_loss_discrepancy/`

Primary table:

`best_predictive_leg_heat_loss_discrepancy.csv`

## Short Thesis Paragraph

Although the best current predictive-style model nearly closes the aggregate
heat balance, a leg-resolved comparison shows that agreement is partly
cancellation. The 1D model removes too much heat from pipe legs and too little
from junction/stub regions. This motivates a branchwise external-boundary and
junction heat-loss treatment rather than a single global heat-loss correction.
"""
    (out / "thesis_reuse_index.md").write_text(thesis_index, encoding="utf-8")


def build_package(out: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    rows = discrepancy_rows()
    cases = case_summary(rows)
    changes = change_recommendations(rows)
    manifest = source_manifest()
    write_csv(out / "best_predictive_leg_heat_loss_discrepancy.csv", rows, DISCREPANCY_COLUMNS)
    write_csv(out / "best_predictive_case_heat_loss_summary.csv", cases, CASE_COLUMNS)
    write_csv(out / "model_change_recommendations.csv", changes, CHANGE_COLUMNS)
    write_csv(out / "source_manifest.csv", manifest, ["source_path", "exists", "row_count", "sha256", "role"])
    summary = {
        "task": TASK_ID,
        "generated_utc": utc_now(),
        "host": socket.gethostname(),
        "best_model_variant": BEST_VARIANT,
        "model_status": "best_current_predictive_style_imposed_cooler_not_final_predictive_hx",
        "case_count": len(cases),
        "leg_discrepancy_rows": len(rows),
        "model_change_rows": len(changes),
        "native_solver_outputs_mutated": False,
        "heavy_openfoam_run": False,
        "external_fluid_modified": False,
        "predictive_hx_admitted": False,
        "runtime_guardrail": "CFD_mdot_realized_wallHeatFlux_and_validation_temperatures_not_runtime_inputs",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_docs(out, summary, cases, changes)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(build_package(args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
