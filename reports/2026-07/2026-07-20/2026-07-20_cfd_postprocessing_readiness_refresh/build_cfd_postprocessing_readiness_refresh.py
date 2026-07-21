#!/usr/bin/env python3
"""Build a refreshed CFD postprocessing readiness table from current evidence."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent


def read_csv(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        vals = [row[c].replace("\n", " ").replace("|", "/") for c in columns]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines) + "\n"


def main() -> None:
    broad_inventory = "work_products/2026-07/2026-07-14/2026-07-14_cfd_case_admission_inventory/cfd_case_admission_inventory.csv"
    salt_inventory = "work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/salt_cfd_candidate_inventory.csv"
    registry_aggregate = "registry/_all_postprocessing_runs.csv"
    pm10_rows_path = "work_products/2026-07/2026-07-20/2026-07-20_salt_pm10_terminal_admission_classification/pm10_terminal_admission_rows.csv"
    upcomer_wrapper_path = "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_post_3305547_harvest_wrapper/pressure_upcomer_admission_rollup.csv"
    freeze_manifest_path = "work_products/2026-07/2026-07-20/2026-07-20_salt1_4_nominal_final_freeze/final_freeze_manifest.csv"

    broad_rows = read_csv(broad_inventory)
    salt_rows = read_csv(salt_inventory)
    registry_rows = read_csv(registry_aggregate)
    pm10_rows = read_csv(pm10_rows_path)
    upcomer_rows = read_csv(upcomer_wrapper_path)
    freeze_rows = read_csv(freeze_manifest_path)

    scheduler_snapshot = """# Read-only scheduler check captured before report build
squeue -j 3293924,3295438,3299610,3299620,3305547 -o '%i|%T|%j|%M|%D|%R'
JOBID|STATE|NAME|TIME|NODES|NODELIST(REASON)
3299620|RUNNING|salt4_heat_pack|3-19:22:35|1|c318-018
3299610|RUNNING|salt4_q3x_probe|3-19:37:24|1|c318-017

sacct -j 3293924,3295438,3299610,3299620,3305547 --format=JobID,JobName%30,State,ExitCode,Elapsed,Start,End -P
3293924|saltq_sel_cont|TIMEOUT|0:0|5-00:00:06|2026-07-13T17:03:56|2026-07-18T17:04:02
3295438|saltq_s24_sel_harv|COMPLETED|0:0|00:35:41|2026-07-18T17:04:13|2026-07-18T17:39:54
3299610|salt4_q3x_probe|RUNNING|0:0|3-19:37:25|2026-07-16T17:39:21|Unknown
3299620|salt4_heat_pack|RUNNING|0:0|3-19:22:36|2026-07-16T17:54:10|Unknown
3305547|upc_nominal|FAILED|1:0|00:02:17|2026-07-20T12:25:41|2026-07-20T12:27:58
"""

    registry_generated = max(r["generated_at"] for r in registry_rows if r.get("generated_at"))
    pm10_pass = sum(1 for r in pm10_rows if r["terminal_drift_status"] == "pass")
    upcomer_fit = sum(1 for r in upcomer_rows if r["fit_candidate"].lower() == "true")
    freeze_included = sum(1 for r in freeze_rows if r["freeze_inclusion"] == "included_final_predictive_training_envelope")

    rows = [
        {
            "row_id": "salt1_4_nominal_freeze",
            "cases": "salt1_nominal; salt2_jin_nominal; salt3_jin_nominal; salt4_nominal",
            "current_status": f"{freeze_included} nominal rows included in July 20 final-freeze envelope",
            "postprocessing_readiness": "ready_for_nominal_freeze_inputs; registry/summary evidence exists; source-envelope policy still blocks final unrestricted fitting",
            "current_allowed_use": "freeze/manifests, setup-boundary candidate review, diagnostics",
            "missing_or_blocked": "final source-envelope policy leaves fit/model-selection at zero; pressure/upcomer ordinary closures still blocked separately",
            "continuation_or_harvest_need": "none for nominal freeze; future fitting needs policy/source-envelope resolution rather than more solver time",
            "primary_source": freeze_manifest_path,
            "refresh_note": "supersedes July 14 Salt1 diagnostic-only status for the nominal freeze envelope only",
        },
        {
            "row_id": "salt2_3_4_nominal_case_admission",
            "cases": "salt2_jin_nominal; salt3_jin_nominal; salt4_nominal",
            "current_status": "admitted in July 14 broad inventory for forward-v0 train/validation/holdout roles",
            "postprocessing_readiness": "registry aggregates, BC role audit, heat/pressure ledgers, observation tables available",
            "current_allowed_use": "case-level comparison, diagnostics, split-aware score targets",
            "missing_or_blocked": "not enough for ordinary upcomer Nu/f_D/K or final source-envelope-safe fitting",
            "continuation_or_harvest_need": "no continuation needed for current case-level summaries",
            "primary_source": broad_inventory,
            "refresh_note": "still valid, but use July 20 freeze/source-policy packages for final predictive fitting status",
        },
        {
            "row_id": "pm10_salt2_salt4",
            "cases": "salt2_lo10q; salt2_hi10q; salt4_lo10q; salt4_hi10q",
            "current_status": f"{pm10_pass}/4 terminal drift rows pass after 3293924 TIMEOUT and 3295438 harvest COMPLETED",
            "postprocessing_readiness": "terminal heat/mass-flow and registered heat ledger ready; PM10 pressure/upcomer not fit-admitted",
            "current_allowed_use": "future/frozen-model holdout scoring after final freeze; not fitting/model selection/runtime input",
            "missing_or_blocked": "matched-plane pressure/upcomer extraction and wall-band fields remain incomplete",
            "continuation_or_harvest_need": "no more solver continuation for terminal PM10 classification; pressure/upcomer needs parser/rerun work",
            "primary_source": pm10_rows_path,
            "refresh_note": "updates stale July 14 rows that still marked selected PM10 as running/pending",
        },
        {
            "row_id": "pressure_upcomer_matched_plane",
            "cases": "nominal Salt2-4 plus selected PM10/upcomer candidates",
            "current_status": "job 3305547 FAILED; wrapper released zero fit-admitted rows",
            "postprocessing_readiness": f"partial parser evidence only; fit candidates released: {upcomer_fit}",
            "current_allowed_use": "diagnostic only where parsed; not predictive upcomer admission",
            "missing_or_blocked": "compute wrapper/rerun and parser rollup; only salt2_lo10q partial parsed in failure-repair package",
            "continuation_or_harvest_need": "rerun or repair matched-plane compute wrapper; then refresh admission rollup",
            "primary_source": upcomer_wrapper_path,
            "refresh_note": "July 20 failure state supersedes older pending-compute notes",
        },
        {
            "row_id": "pm5_corrected_q",
            "cases": "salt2_lo5q; salt2_hi5q; salt4_lo5q; salt4_hi5q",
            "current_status": "postprocessed enough for holdout/diagnostic reviews in repaired PM5 packages",
            "postprocessing_readiness": "matched-plane/wall-band repairs exist for key rows; recirculation diagnostics available",
            "current_allowed_use": "holdout/testing diagnostics and sensitivity/correlation support only",
            "missing_or_blocked": "recirculation/sign/admission gates prevent ordinary F6/internal-Nu fit admission",
            "continuation_or_harvest_need": "continue only if sensitivity coverage is specifically needed; otherwise policy blocks fitting",
            "primary_source": "work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/salt2_pm5_admission_table.csv",
            "refresh_note": "more current than July 14 broad corrected-Q too-short classifications for PM5 diagnostic use",
        },
        {
            "row_id": "high_heat_no_recirc_probes",
            "cases": "salt4_q3x_probe; salt4_heat_pack",
            "current_status": "3299610 and 3299620 still RUNNING in current scheduler snapshot",
            "postprocessing_readiness": "not ready; admitted rows now: 0 in high-heat status refresh",
            "current_allowed_use": "none beyond live monitor/readiness context",
            "missing_or_blocked": "terminal solver exit, harvest, postprocessing, steady/admission gate",
            "continuation_or_harvest_need": "wait for terminal state; harvest only from a separately claimed cfd-pp/admission row",
            "primary_source": "work_products/2026-07/2026-07-20/2026-07-20_high_heat_status_refresh/README.md",
            "refresh_note": "current scheduler snapshot included in this report",
        },
        {
            "row_id": "salt2_mesh_family",
            "cases": "salt2 coarse/medium/fine mesh-family evidence",
            "current_status": "diagnostic-only",
            "postprocessing_readiness": "pressure and thermal repair-smoke summaries available; closure-QOI GCI not publication-ready",
            "current_allowed_use": "mesh/GCI diagnostics and planning",
            "missing_or_blocked": "closure-QOI GCI, sign, heat-balance, and same-QOI uncertainty gates",
            "continuation_or_harvest_need": "no broad continuation decision here; resolve GCI/admission gates before publication/fit use",
            "primary_source": salt_inventory,
            "refresh_note": "unchanged from July 14 salt inventory",
        },
        {
            "row_id": "val_salt2_external",
            "cases": "val_salt2 / native Salt2 external reference",
            "current_status": "external-test/diagnostic rows exist; prediction joins blocked until frozen model predictions exist",
            "postprocessing_readiness": "ledger and admission packages exist; not a training row",
            "current_allowed_use": "external score target after model freeze/prediction artifact",
            "missing_or_blocked": "frozen prediction artifact and score join; some pressure/corner evidence remains diagnostic",
            "continuation_or_harvest_need": "no solver continuation identified for score target use",
            "primary_source": "work_products/2026-07/2026-07-17/2026-07-17_predict_val_salt2_external_ledger/val_salt2_external_admission_decision.csv",
            "refresh_note": "not represented well by the broad July 14 salt-only inventory",
        },
        {
            "row_id": "historical_water_kirst_native",
            "cases": "water1-4; Kirst Salt1-4; native/reference rows",
            "current_status": f"registry aggregate refreshed through {registry_generated}; many rows are convergence-audit or historical context only",
            "postprocessing_readiness": "basic registry aggregates/plots exist for many rows",
            "current_allowed_use": "context, validation split history, or illustrative diagnostics only unless re-admitted",
            "missing_or_blocked": "dated re-admission and convergence/admission review before current-model use",
            "continuation_or_harvest_need": "case-specific only; do not default to continuation without a re-admission objective",
            "primary_source": registry_aggregate,
            "refresh_note": "registry aggregate is current only to July 18 and is not an admission table",
        },
        {
            "row_id": "invalid_original_q_insulation_sweep",
            "cases": "old 14-case Q/insulation perturbation sweep",
            "current_status": "false-steady/quarantined or deleted",
            "postprocessing_readiness": "not useful",
            "current_allowed_use": "none for regression, validation, or closure evidence",
            "missing_or_blocked": "not repair-targeted; use corrected Salt-Q campaign instead",
            "continuation_or_harvest_need": "none",
            "primary_source": broad_inventory,
            "refresh_note": "kept only to prevent accidental reuse",
        },
    ]

    write_csv(OUT / "cfd_postprocessing_readiness_refresh.csv", rows)

    short_columns = [
        "row_id",
        "current_status",
        "postprocessing_readiness",
        "current_allowed_use",
        "missing_or_blocked",
        "continuation_or_harvest_need",
    ]
    (OUT / "cfd_postprocessing_readiness_refresh.md").write_text(
        markdown_table(rows, short_columns)
    )

    (OUT / "scheduler_snapshot.txt").write_text(scheduler_snapshot)

    summary = {
        "rows": len(rows),
        "broad_inventory_rows": len(broad_rows),
        "salt_inventory_rows": len(salt_rows),
        "registry_rows": len(registry_rows),
        "registry_generated_at_max": registry_generated,
        "pm10_terminal_drift_pass_rows": pm10_pass,
        "upcomer_fit_candidates_released": upcomer_fit,
        "nominal_freeze_rows_included": freeze_included,
        "key_conclusion": "Broad July 14 overviews remain useful but are stale for PM10, final freeze/source-policy, high-heat, and pressure/upcomer wrapper state.",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    readme = f"""---
provenance:
  - {broad_inventory}
  - {salt_inventory}
  - {registry_aggregate}
  - {pm10_rows_path}
  - {upcomer_wrapper_path}
  - {freeze_manifest_path}
tags: [cfd-postprocessing, readiness, admission, cfd-pp, report]
related:
  - operational_notes/maps/cfd-runs-and-admission.md
  - operational_notes/maps/forward-predictive-model.md
  - .agent/status/2026-07-20_AGENT-563.md
task: AGENT-563
date: 2026-07-20
role: Coordinator/Writer/cfd-pp
type: report
status: complete
---
# CFD Postprocessing Readiness Refresh

This package refreshes the CFD postprocessing overview without mutating native
solver outputs, registry/admission state, or scheduler state.

## Result

- Refreshed readiness rows: `{len(rows)}`.
- PM10 terminal drift pass rows: `{pm10_pass}/4`.
- Pressure/upcomer fit candidates released after job `3305547`: `{upcomer_fit}`.
- Nominal freeze rows included in the July 20 final freeze: `{freeze_included}`.
- Registry aggregate latest timestamp: `{registry_generated}`.

## Main Interpretation

The July 14 broad overviews remain useful for baseline case/admission context,
but they are stale for four important lanes: PM10 terminal admission, July 20
nominal freeze/source-policy work, high-heat live probes, and the failed
pressure/upcomer matched-plane wrapper. Use this report as the current
high-level dispatch table and open the cited source package before acting on any
row.

## Files

- `cfd_postprocessing_readiness_refresh.csv`
- `cfd_postprocessing_readiness_refresh.md`
- `scheduler_snapshot.txt`
- `summary.json`
- `build_cfd_postprocessing_readiness_refresh.py`

## Guardrails

No native CFD/OpenFOAM outputs were mutated. No registry/admission state was
mutated. No scheduler submission, cancellation, requeue, solver launch,
postprocessing launch, Fluid edit, fitting, tuning, model selection, scientific
admission change, or blocker-register change was performed.
"""
    (OUT / "README.md").write_text(readme)


if __name__ == "__main__":
    main()
