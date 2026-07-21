#!/usr/bin/env python3
"""Process completed corrected-Q +/-5Q harvest rows into split-aware gates.

This package consumes the completed AGENT-347/3295437 harvest status and
read-only registry aggregates. It does not mutate registry state or admit
perturbations as independent training rows.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing"
HARVEST_STATUS = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_cfd_postprocess_admission_workflow_triage"
    / "corrected_q_harvest_3295437_processing_status.csv"
)
RECOMMENDED_SPLIT = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory"
    / "recommended_salt_split.csv"
)
TRIAGE_README = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_cfd_postprocess_admission_workflow_triage"
    / "README.md"
)
DASHBOARD_README = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_scientific_closure_forward_v1_execution_dashboard"
    / "README.md"
)

ADMISSION_COLUMNS = [
    "case_key",
    "source_case_key",
    "baseline_case",
    "salt_number",
    "variant",
    "q_ratio",
    "terminal_harvest_job",
    "terminal_harvest_state",
    "closure_fit_admissible_terminal_gate",
    "registry_aggregate_available",
    "current_split_family",
    "can_expand_training_now",
    "can_score_validation_now",
    "can_score_holdout_now",
    "current_allowed_use",
    "blocked_use",
    "next_required_gate",
    "normalized_csv",
    "wall_heat_flux_grouped_csv",
    "case_summary_csv",
]

HEAT_COLUMNS = [
    "case_key",
    "source_case_key",
    "final_window_start_s",
    "final_window_end_s",
    "final_window_row_count",
    "total_Q_postProc_mean_W",
    "ambient_proxy_mean_W",
    "ambient_noncooling_proxy_mean_W",
    "cooling_branch_total_removal_mean_W",
    "section_heater_net_q_mean_W",
    "section_test_section_net_q_mean_W",
    "section_cooling_branch_net_q_mean_W",
    "section_downcomer_net_q_mean_W",
    "section_upcomer_net_q_mean_W",
    "section_junctions_net_q_mean_W",
    "radiation_semantics",
    "runtime_use_guardrail",
    "source_wall_heat_flux_grouped_csv",
]

QUEUE_COLUMNS = [
    "queue_id",
    "case_key",
    "gate_lane",
    "current_status",
    "why_it_matters",
    "next_action",
    "may_feed_forward_v1_now",
    "guardrail",
]

MANIFEST_COLUMNS = ["artifact", "role", "mutation_status", "path"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column, "")) for column in columns})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    return value


def fnum(value: str, default: float = float("nan")) -> float:
    if value in ("", None):
        return default
    try:
        return float(value)
    except ValueError:
        return default


def mean(values: list[float]) -> float:
    finite = [value for value in values if math.isfinite(value)]
    return sum(finite) / len(finite) if finite else float("nan")


def variant_q_ratio(case_key: str) -> float:
    if "_lo5q" in case_key:
        return 0.95
    if "_hi5q" in case_key:
        return 1.05
    raise ValueError(f"not a +/-5Q case: {case_key}")


def baseline_case(case_key: str) -> str:
    salt = case_key.split("_", 1)[0]
    return f"{salt}_jin_nominal_continuation"


def split_family(case_key: str) -> str:
    if case_key.startswith("salt2_"):
        return "salt2_train_family_perturbation"
    if case_key.startswith("salt4_"):
        return "salt4_holdout_family_perturbation"
    return "unknown_family"


def admission_rows(harvest_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in harvest_rows:
        case_key = row["case_key"]
        family = split_family(case_key)
        is_salt2 = family.startswith("salt2_")
        rows.append(
            {
                "case_key": case_key,
                "source_case_key": row["source_case_key"],
                "baseline_case": baseline_case(case_key),
                "salt_number": case_key.split("_", 1)[0],
                "variant": "lo5q" if "_lo5q" in case_key else "hi5q",
                "q_ratio": variant_q_ratio(case_key),
                "terminal_harvest_job": row["job_id"],
                "terminal_harvest_state": row["scheduler_state_observed"],
                "closure_fit_admissible_terminal_gate": row["closure_fit_admissible_in_terminal_gate"],
                "registry_aggregate_available": row["registry_aggregate_available"],
                "current_split_family": family,
                "can_expand_training_now": "no",
                "can_score_validation_now": "no",
                "can_score_holdout_now": "no",
                "current_allowed_use": (
                    "train-family sensitivity/admission evidence; not an independent training row"
                    if is_salt2
                    else "holdout-family sensitivity/admission evidence; do not use for model selection"
                ),
                "blocked_use": "independent train/validation/holdout row before dated perturbation split policy",
                "next_required_gate": (
                    "perturbation split-policy update plus BC-role and operating-point admission refresh"
                    if is_salt2
                    else "holdout-family use policy after model selection is frozen"
                ),
                "normalized_csv": row["normalized_csv"],
                "wall_heat_flux_grouped_csv": row["wall_heat_flux_grouped_csv"],
                "case_summary_csv": row["case_summary_csv"],
            }
        )
    return rows


def final_window_heat_row(harvest_row: dict[str, str], window_s: float = 300.0) -> dict[str, Any]:
    case_key = harvest_row["case_key"]
    path = Path(harvest_row["wall_heat_flux_grouped_csv"])
    rows = read_csv(path)
    times = [fnum(row["time_s"]) for row in rows]
    end = max(times)
    start = end - window_s
    window_rows = [row for row in rows if fnum(row["time_s"]) >= start]
    if not window_rows:
        raise ValueError(f"no final-window rows for {case_key}")

    def col(name: str) -> float:
        return mean([fnum(row.get(name, "")) for row in window_rows])

    return {
        "case_key": case_key,
        "source_case_key": harvest_row["source_case_key"],
        "final_window_start_s": start,
        "final_window_end_s": end,
        "final_window_row_count": len(window_rows),
        "total_Q_postProc_mean_W": col("total_Q_postProc"),
        "ambient_proxy_mean_W": col("ambient_proxy_w"),
        "ambient_noncooling_proxy_mean_W": col("ambient_noncooling_proxy_w"),
        "cooling_branch_total_removal_mean_W": col("cooling_branch_total_removal_w"),
        "section_heater_net_q_mean_W": col("section_heater_net_q_w"),
        "section_test_section_net_q_mean_W": col("section_test_section_net_q_w"),
        "section_cooling_branch_net_q_mean_W": col("section_cooling_branch_net_q_w"),
        "section_downcomer_net_q_mean_W": col("section_downcomer_net_q_w"),
        "section_upcomer_net_q_mean_W": col("section_upcomer_net_q_w"),
        "section_junctions_net_q_mean_W": col("section_junctions_net_q_w"),
        "radiation_semantics": "rcExternalTemperature_radiation_embedded_in_wallHeatFlux_no_exported_qr",
        "runtime_use_guardrail": "diagnostic target only; no realized wallHeatFlux or cooler duty as predictive runtime input",
        "source_wall_heat_flux_grouped_csv": harvest_row["wall_heat_flux_grouped_csv"],
    }


def heat_rows(harvest_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [final_window_heat_row(row) for row in harvest_rows]


def queue_rows(admission: list[dict[str, Any]], heat: list[dict[str, Any]]) -> list[dict[str, str]]:
    heat_by_case = {row["case_key"]: row for row in heat}
    rows: list[dict[str, str]] = []
    for row in admission:
        case_key = row["case_key"]
        heat_row = heat_by_case[case_key]
        rows.extend(
            [
                {
                    "queue_id": f"{case_key}_split_policy",
                    "case_key": case_key,
                    "gate_lane": "cfd_admission_split",
                    "current_status": "terminal_harvested_closure_fit_admissible_but_not_independent_training",
                    "why_it_matters": "Corrected +/-5Q expands operating-point evidence only if split discipline prevents leakage.",
                    "next_action": row["next_required_gate"],
                    "may_feed_forward_v1_now": "no",
                    "guardrail": row["blocked_use"],
                },
                {
                    "queue_id": f"{case_key}_boundary_hx_targets",
                    "case_key": case_key,
                    "gate_lane": "boundary_hx",
                    "current_status": "heat_role_reduction_available",
                    "why_it_matters": (
                        f"Final-window cooler removal mean is "
                        f"{csv_value(heat_row['cooling_branch_total_removal_mean_W'])} W; useful as score target only."
                    ),
                    "next_action": "carry heat-role targets into setup-only HX/BC scoring after split policy lands",
                    "may_feed_forward_v1_now": "no",
                    "guardrail": "do not use CFD cooler duty or wallHeatFlux as runtime input",
                },
                {
                    "queue_id": f"{case_key}_f6_onset_candidate",
                    "case_key": case_key,
                    "gate_lane": "hydraulic_or_upcomer_onset",
                    "current_status": "candidate_evidence_pending_metric_extraction",
                    "why_it_matters": "+/-5Q rows may expand Re variation for F6 or onset if matched pressure/upcomer metrics are admitted.",
                    "next_action": "extract/admit pressure and matched upcomer metrics before F6 or onset fitting",
                    "may_feed_forward_v1_now": "no",
                    "guardrail": "do not infer F6 or onset from terminal harvest alone",
                },
            ]
        )
    return rows


def source_manifest(harvest_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    sources = [
        (HARVEST_STATUS, "primary_status"),
        (RECOMMENDED_SPLIT, "split_policy_context"),
        (TRIAGE_README, "workflow_context"),
        (DASHBOARD_README, "forward_gate_context"),
    ]
    for row in harvest_rows:
        sources.append((Path(row["wall_heat_flux_grouped_csv"]), "registry_aggregate_read_only"))
        sources.append((Path(row["case_summary_csv"]), "registry_aggregate_read_only"))
        sources.append((Path(row["normalized_csv"]), "registry_aggregate_read_only"))
    return [
        {
            "artifact": path.name,
            "role": role,
            "mutation_status": "read_only",
            "path": rel(path),
        }
        for path, role in sources
    ]


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(HARVEST_STATUS)}
  - {rel(RECOMMENDED_SPLIT)}
  - {rel(TRIAGE_README)}
tags: [cfd-pp, corrected-q, admission, forward-v1, split-discipline]
related:
  - {rel(out_dir / 'corrected_q_pm5_split_admission_matrix.csv')}
  - {rel(out_dir / 'corrected_q_pm5_heat_role_reduction.csv')}
task: AGENT-353
date: 2026-07-14
role: cfd-pp/Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
---
# Corrected-Q +/-5Q Admission/Split Processing

## Purpose

This package implements the next completed-harvest slice of the forward-v1 plan.
It consumes the completed corrected-Q +/-5Q harvest `3295437` and registry
aggregates, then publishes split-aware admission/use artifacts without changing
registry state or native CFD outputs.

## Decision

The four +/-5Q rows are terminal-harvested and closure-fit admissible under the
current terminal gate, but they do **not** expand independent training,
validation, or holdout rows yet. They are perturbation-family evidence:

- Salt2 +/-5Q: train-family sensitivity/admission evidence pending a dated
  perturbation split policy.
- Salt4 +/-5Q: holdout-family sensitivity/admission evidence; not usable for
  model selection.

## Files

- `corrected_q_pm5_split_admission_matrix.csv`: terminal/admission status and
  split-safe allowed use.
- `corrected_q_pm5_heat_role_reduction.csv`: final-window heat-role reductions
  from read-only registry `wall_heat_flux_grouped.csv`.
- `corrected_q_pm5_forward_gate_queue.csv`: next gate actions for boundary/HX,
  F6, upcomer onset, and forward-v1.
- `source_manifest.csv`: read-only provenance.

## Guardrails

No row is admitted as an independent training point by this package. Realized
CFD wallHeatFlux and cooler duty are diagnostic/score targets only, not runtime
predictive inputs. Radiation remains embedded in `rcExternalTemperature`
`wallHeatFlux`; no separate exported `qr` exists.

Summary: `{summary['harvest_rows']}` harvested rows processed; independent
training expansion rows now: `{summary['independent_training_expansion_rows']}`.
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def build_package(out_dir: Path = OUT_DIR) -> dict[str, Any]:
    harvest = read_csv(HARVEST_STATUS)
    harvested = [row for row in harvest if row.get("registry_aggregate_available") == "yes"]
    admission = admission_rows(harvested)
    heat = heat_rows(harvested)
    queue = queue_rows(admission, heat)

    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "corrected_q_pm5_split_admission_matrix.csv", admission, ADMISSION_COLUMNS)
    write_csv(out_dir / "corrected_q_pm5_heat_role_reduction.csv", heat, HEAT_COLUMNS)
    write_csv(out_dir / "corrected_q_pm5_forward_gate_queue.csv", queue, QUEUE_COLUMNS)
    write_csv(out_dir / "source_manifest.csv", source_manifest(harvested), MANIFEST_COLUMNS)

    summary = {
        "task": "AGENT-353",
        "status": "complete",
        "generated_at": utc_now(),
        "package": rel(out_dir),
        "harvest_rows": len(harvested),
        "closure_fit_admissible_terminal_gate_rows": sum(
            1 for row in admission if row["closure_fit_admissible_terminal_gate"] == "yes"
        ),
        "independent_training_expansion_rows": sum(
            1 for row in admission if row["can_expand_training_now"] == "yes"
        ),
        "forward_gate_queue_rows": len(queue),
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "external_fluid_modified": False,
        "core_decision": "Corrected +/-5Q rows are terminal-harvested perturbation evidence, not independent training rows until split policy changes.",
    }
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    print(json.dumps(build_package(args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
