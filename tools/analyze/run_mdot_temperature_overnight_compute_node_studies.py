#!/usr/bin/env python3
"""Run local mdot/temperature overnight studies on a compute node."""
from __future__ import annotations

import csv
import json
import math
import os
import platform
import subprocess
import sys
import time
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_mdot_temperature_probe_error_audit as audit  # noqa: E402


TASK = "AGENT-391"
DATE = "2026-07-14"
OUT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_overnight_compute_node_run"
LOGS = OUT / "logs"
RUN_LOG = LOGS / "runner_events.jsonl"


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def event(stage: str, status: str, **payload: Any) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    row = {"time": now(), "stage": stage, "status": status, **payload}
    with RUN_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
    print(json.dumps(row, sort_keys=True), flush=True)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: audit.csv_value(row.get(field, "")) for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_cmd(args: list[str], *, log_name: str) -> dict[str, Any]:
    log_path = LOGS / log_name
    event("command", "start", command=" ".join(args), log=rel(log_path))
    start = time.time()
    with log_path.open("w", encoding="utf-8") as handle:
        proc = subprocess.run(args, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT, text=True)
    result = {
        "command": " ".join(args),
        "returncode": proc.returncode,
        "elapsed_s": round(time.time() - start, 3),
        "log": rel(log_path),
    }
    event("command", "complete" if proc.returncode == 0 else "failed", **result)
    return result


def case_context() -> tuple[list[dict[str, Any]], dict[str, list[dict[str, str]]], dict[tuple[str, str], dict[str, str]], dict[str, Any]]:
    targets = audit.load_targets()
    refs = audit.load_sensor_refs()
    heat_by = audit.heat_rows_by_case()
    cases = audit.case_rows(targets, refs, heat_by)
    fluid_cases = {case.name: case for case in audit.config_loader.load_cases()}
    return cases, heat_by, refs, fluid_cases


def heat_score_summary(rows: list[dict[str, Any]], part: str) -> list[dict[str, Any]]:
    return [row for row in audit.summarize_heat(rows) if row["part"] == part]


def setup_only_cooler_study(case_table: list[dict[str, Any]]) -> dict[str, Any]:
    out = OUT / "setup_only_cooler_closure_bakeoff"
    event("setup_only_cooler", "start", output=rel(out))
    heat_scores = [row for row in audit.heat_score_rows(case_table, execute_fluid=True) if row["part"] == "part4"]
    summary = heat_score_summary(heat_scores, "part4")
    candidates = []
    for row in summary:
        form = row["model_form"]
        is_predictive_candidate = "upper_bound" not in form and "imposed_ratio" not in form and row["scope"] == "all_non_salt1"
        candidates.append(
            {
                **row,
                "runtime_leakage_class": "diagnostic_uses_cfd_cooler_or_imposed_heat" if ("upper_bound" in form or "imposed_ratio" in form) else "candidate_no_realized_cfd_cooler_runtime",
                "predictive_candidate": "yes" if is_predictive_candidate else "no",
            }
        )
    write_csv(out / "cooler_model_scores.csv", heat_scores, audit.HEAT_SCORE_COLUMNS)
    write_csv(
        out / "cooler_rmse_summary_with_leakage_policy.csv",
        candidates,
        audit.HEAT_SUMMARY_COLUMNS + ["runtime_leakage_class", "predictive_candidate"],
    )
    (out / "README.md").write_text(
        """# Setup-Only Cooler Closure Bakeoff

This overnight local Fluid study re-scores cooling heat removed using the
AGENT-360 Part4 machinery. Rows using imposed or realized CFD cooler heat are
kept as diagnostics and leakage warnings. Predictive candidates exclude
`imposed_cfd_cooler_upper_bound` and `salt2_fit_cooler_imposed_ratio`.

Primary files:

- `cooler_model_scores.csv`
- `cooler_rmse_summary_with_leakage_policy.csv`
""",
        encoding="utf-8",
    )
    event("setup_only_cooler", "complete", rows=len(heat_scores), summary_rows=len(summary))
    return {"rows": len(heat_scores), "summary_rows": len(summary), "output": rel(out)}


def mode_dict(mode_id: str, part: str, description: str, closure: str) -> dict[str, str]:
    return {
        "mode_id": mode_id,
        "part": part,
        "description": description,
        "predictivity_class": "overnight_cfd_informed_diagnostic",
        "runtime_input_policy": "CFD heater/cooler/test-section heat evidence may be consumed only by explicitly labeled diagnostic forms.",
        "closure_terms": closure,
        "assumption_ids": "A001;A002;A003;A005;A006;A009",
    }


def run_ts_variant(case_row: dict[str, Any], rows: list[dict[str, str]], fluid_case: Any, variant: str) -> tuple[Any, dict[str, str]]:
    terms = audit.heat_terms(rows)
    if variant == "zero_test_section":
        scenario = audit.base_scenario(case_row, name=variant, imposed_qhx_W=terms["cooler_loss_W"], radiation_on=False)
        sources = {"heated_incline": terms["heater_W"]}
        losses = None
        mode = mode_dict(variant, "overnight_test_section", "Heater/cooler only; no test-section term.", "heater source plus imposed cooler; no CFD test-section term")
    elif variant == "negative_source_compatibility":
        scenario = audit.base_scenario(case_row, name=variant, imposed_qhx_W=terms["cooler_loss_W"], radiation_on=False)
        sources = {"heated_incline": terms["heater_W"], "test_section": -terms["test_loss_W"]}
        losses = None
        mode = mode_dict(variant, "overnight_test_section", "Compatibility negative test-section source.", "heater source plus negative test-section source plus imposed cooler")
    elif variant == "prescribed_test_loss":
        scenario = audit.base_scenario(case_row, name=variant, imposed_qhx_W=terms["cooler_loss_W"], radiation_on=False)
        sources = {"heated_incline": terms["heater_W"]}
        losses = {"left_upper_vertical": terms["test_loss_W"]}
        mode = mode_dict(variant, "overnight_test_section", "Prescribed test-section loss on upcomer parent segment.", "heater source plus imposed cooler plus prescribed left_upper_vertical test loss")
    elif variant == "half_prescribed_test_loss":
        scenario = audit.base_scenario(case_row, name=variant, imposed_qhx_W=terms["cooler_loss_W"], radiation_on=False)
        sources = {"heated_incline": terms["heater_W"]}
        losses = {"left_upper_vertical": 0.5 * terms["test_loss_W"]}
        mode = mode_dict(variant, "overnight_test_section", "Half-strength prescribed test-section loss.", "heater source plus imposed cooler plus 0.5x prescribed left_upper_vertical test loss")
    else:
        raise ValueError(variant)
    return audit.fast_pressure_root(fluid_case, scenario, sources, losses), mode


def test_section_boundary_study(
    case_table: list[dict[str, Any]],
    heat_by: dict[str, list[dict[str, str]]],
    refs: dict[tuple[str, str], dict[str, str]],
    fluid_cases: dict[str, Any],
) -> dict[str, Any]:
    out = OUT / "test_section_boundary_form_bakeoff"
    event("test_section_boundary", "start", output=rel(out))
    variants = ["zero_test_section", "negative_source_compatibility", "prescribed_test_loss", "half_prescribed_test_loss"]
    result_rows: list[dict[str, Any]] = []
    sensor_rows: list[dict[str, Any]] = []
    for case_row in case_table:
        if case_row["case_id"] == "salt_1" or case_row["has_patch_heat_ledger"] != "yes":
            continue
        rows = heat_by[case_row["case_id"]]
        fluid_case = fluid_cases[case_row["fluid_case_name"]]
        for variant in variants:
            event("test_section_boundary", "variant_start", case_id=case_row["case_id"], variant=variant)
            result, mode = run_ts_variant(case_row, rows, fluid_case, variant)
            terms = audit.heat_terms(rows)
            source_total = terms["heater_W"] - (terms["test_loss_W"] if variant == "negative_source_compatibility" else 0.0)
            loss_total = terms["test_loss_W"] if variant == "prescribed_test_loss" else (0.5 * terms["test_loss_W"] if variant == "half_prescribed_test_loss" else 0.0)
            row = audit.result_row(result, case_row, mode, str(source_total), str(loss_total), rel(audit.SECTION_HEAT))
            result_rows.append(row)
            sensor_rows.extend(audit.sensor_rows_for_result(result, case_row, mode, refs))
            event("test_section_boundary", "variant_complete", case_id=case_row["case_id"], variant=variant, mdot=row["mdot_pred_kg_s"])
    temp_summary = audit.summarize_sensors(sensor_rows)
    corr = audit.correlation_rows(result_rows, temp_summary)
    write_csv(out / "test_section_model_result_ledger.csv", result_rows, audit.RESULT_COLUMNS)
    write_csv(out / "test_section_sensor_level_errors.csv", sensor_rows, audit.SENSOR_COLUMNS)
    write_csv(out / "test_section_temperature_probe_summary.csv", temp_summary, audit.TEMP_SUMMARY_COLUMNS)
    write_csv(out / "test_section_mdot_probe_correlation.csv", corr, audit.CORRELATION_COLUMNS)
    (out / "README.md").write_text(
        """# Test-Section Boundary-Form Bakeoff

This compute-node local Fluid study compares test-section representations:

- `zero_test_section`
- `negative_source_compatibility`
- `prescribed_test_loss`
- `half_prescribed_test_loss`

All rows are diagnostic. The compatibility negative source is not a physical
boundary proof; it is retained because AGENT-360 used it for Part2.
""",
        encoding="utf-8",
    )
    event("test_section_boundary", "complete", result_rows=len(result_rows), sensor_rows=len(sensor_rows))
    return {"result_rows": len(result_rows), "sensor_rows": len(sensor_rows), "output": rel(out)}


def reference_state_diagnostic() -> dict[str, Any]:
    out = OUT / "reference_state_temperature_audit"
    event("reference_state", "start", output=rel(out))
    model_rows = audit.read_csv(audit.OUT / "model_result_ledger.csv")
    sensor_rows = audit.read_csv(audit.OUT / "sensor_level_errors.csv")
    rows = []
    for row in model_rows:
        if row.get("result_status") != "executed":
            continue
        rows.append(
            {
                "case_id": row.get("case_id", ""),
                "mode_id": row.get("mode_id", ""),
                "part": row.get("part", ""),
                "model_Tmean_K": row.get("model_Tmean_K", ""),
                "cfd_Tmean_K": row.get("cfd_Tmean_K", ""),
                "Tmean_error_K": row.get("Tmean_error_K", ""),
                "loop_delta_error_K": row.get("loop_delta_error_K", ""),
                "temperature_periodicity_error_K": row.get("temperature_periodicity_error_K", ""),
                "interpretation": "Large Tmean offsets indicate a reference-state/start-temperature or energy distribution issue before probe-level fitting.",
            }
        )
    bias_rows = []
    grouped: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in sensor_rows:
        err = audit.fnum(row.get("error_K"))
        if err is None:
            continue
        grouped[(row["case_id"], row["mode_id"], row["kind"])].append(err)
    for (case_id, mode_id, kind), values in sorted(grouped.items()):
        bias_rows.append(
            {
                "case_id": case_id,
                "mode_id": mode_id,
                "kind": kind,
                "n": len(values),
                "mean_error_K": audit.mean(values),
                "rmse_K": audit.rmse(values),
                "bias_fraction_of_rmse": (abs(audit.mean(values) or 0.0) / (audit.rmse(values) or float("nan"))) if audit.rmse(values) else "",
            }
        )
    write_csv(out / "reference_state_mode_offsets.csv", rows, ["case_id", "mode_id", "part", "model_Tmean_K", "cfd_Tmean_K", "Tmean_error_K", "loop_delta_error_K", "temperature_periodicity_error_K", "interpretation"])
    write_csv(out / "sensor_bias_fraction_by_mode.csv", bias_rows, ["case_id", "mode_id", "kind", "n", "mean_error_K", "rmse_K", "bias_fraction_of_rmse"])
    (out / "README.md").write_text(
        """# Reference-State Temperature Audit

This diagnostic uses AGENT-360 outputs to separate mean offset behavior from
probe-level RMSE. It does not tune predictive start temperatures and does not
use TP/TW targets as runtime inputs.
""",
        encoding="utf-8",
    )
    event("reference_state", "complete", rows=len(rows), bias_rows=len(bias_rows))
    return {"rows": len(rows), "bias_rows": len(bias_rows), "output": rel(out)}


def pressure_root_qa(case_table: list[dict[str, Any]], heat_by: dict[str, list[dict[str, str]]], fluid_cases: dict[str, Any]) -> dict[str, Any]:
    out = OUT / "pressure_root_solver_quality_audit"
    event("pressure_root_qa", "start", output=rel(out))
    rows = []
    for case_row in case_table:
        if case_row["case_id"] == "salt_1" or case_row["has_patch_heat_ledger"] != "yes":
            continue
        hr = heat_by[case_row["case_id"]]
        fluid_case = fluid_cases[case_row["fluid_case_name"]]
        for mode in audit.mode_rows():
            if mode["part"] == "part1" and "fixed_mdot" in mode["mode_id"]:
                continue
            if mode["part"] not in {"part1", "part2", "part3"}:
                continue
            scenario, sources, losses, _source_total, _loss_total = audit.mode_setup(case_row, mode["mode_id"], hr)
            root = audit.fast_pressure_root(fluid_case, scenario, sources, losses)
            cfd_mdot = audit.fnum(case_row.get("cfd_mdot_kg_s"))
            cfd_residual = None
            if cfd_mdot is not None:
                cfd_residual = audit.pressure_eval(cfd_mdot, fluid_case, scenario, sources, losses).get("pressure_residual_Pa")
            rows.append(
                {
                    "case_id": case_row["case_id"],
                    "mode_id": mode["mode_id"],
                    "root_status": root.root_status,
                    "root_mdot_kg_s": root.mdot_kg_s,
                    "cfd_mdot_kg_s": cfd_mdot,
                    "root_pressure_residual_Pa": root.pressure_residual_Pa,
                    "cfd_mdot_pressure_residual_Pa": cfd_residual,
                    "root_rejection_reason": root.root_rejection_reason,
                }
            )
    write_csv(out / "pressure_root_quality.csv", rows, ["case_id", "mode_id", "root_status", "root_mdot_kg_s", "cfd_mdot_kg_s", "root_pressure_residual_Pa", "cfd_mdot_pressure_residual_Pa", "root_rejection_reason"])
    (out / "README.md").write_text(
        """# Pressure-Root Solver Quality Audit

This local QA diagnostic re-runs AGENT-360 pressure-root modes and records the
fast-scan root residual and pressure residual at CFD mdot. It is intended to
flag modes where the root search, not the physics closure, may dominate error.
""",
        encoding="utf-8",
    )
    event("pressure_root_qa", "complete", rows=len(rows))
    return {"rows": len(rows), "output": rel(out)}


def write_closeout(summary: dict[str, Any]) -> None:
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(
        f"""# mdot/Temperature Overnight Compute-Node Run

Task: `{TASK}`
Node: `{summary['hostname']}`
Status: `{summary['status']}`

This package was launched on the current compute node as a background local
analysis run. It did not launch OpenFOAM, mutate native CFD solver outputs, or
edit external Fluid files.

Substudies:

- `agent360_refresh/`
- `setup_only_cooler_closure_bakeoff/`
- `test_section_boundary_form_bakeoff/`
- `reference_state_temperature_audit/`
- `pressure_root_solver_quality_audit/`

Logs are in `logs/`.
""",
        encoding="utf-8",
    )
    status = ROOT / ".agent/status/2026-07-14_AGENT-391.md"
    journal = ROOT / ".agent/journal/2026-07-14/mdot-temperature-overnight-compute-node-run.md"
    manifest = ROOT / "imports/2026-07-14_mdot_temperature_overnight_compute_node_run.json"
    status.write_text(
        f"""---
provenance:
  - {rel(OUT / 'summary.json')}
tags: [status, overnight-run, mdot, temperature-probes]
related:
  - {rel(journal)}
task: {TASK}
date: {DATE}
role: Forward-pred/BC-modeling/Scheduler/Implementer/Writer
type: status
status: {summary['status']}
---
# AGENT-391 Status

Status: {summary['status'].upper()}

Started: `{summary['started_at']}`
Finished: `{summary.get('finished_at', '')}`
Node: `{summary['hostname']}`
PID: `{summary['pid']}`

No OpenFOAM solver launch, native CFD mutation, registry/admission mutation,
generated-index mutation, or external Fluid file mutation.

Output: `{rel(OUT)}`
""",
        encoding="utf-8",
    )
    journal.parent.mkdir(parents=True, exist_ok=True)
    journal.write_text(
        f"""---
provenance:
  - {rel(OUT / 'summary.json')}
tags: [journal, overnight-run, mdot, temperature-probes]
related:
  - {rel(status)}
task: {TASK}
date: {DATE}
role: Forward-pred/BC-modeling/Scheduler/Implementer/Writer
type: journal
status: {summary['status']}
---
# mdot/Temperature Overnight Compute-Node Run

Ran local compute-node studies from the AGENT-372 queue:

- AGENT-360 refresh.
- Setup-only cooler closure bakeoff.
- Test-section boundary-form bakeoff.
- Reference-state temperature diagnostic.
- Pressure-root QA diagnostic.

See `{rel(OUT / 'summary.json')}` and `{rel(RUN_LOG)}`.
""",
        encoding="utf-8",
    )
    write_json(
        manifest,
        {
            "task": TASK,
            "date": DATE,
            "kind": "work_product_import",
            "work_product": rel(OUT),
            "summary": rel(OUT / "summary.json"),
            "status": rel(status),
            "journal": rel(journal),
            "runner_log": rel(RUN_LOG),
            "native_cfd_outputs_mutated": False,
            "external_cfd_modeling_tools_mutated": False,
            "openfoam_solver_launched": False,
            "generated_index_refresh": "not_run_generated_index_scope_not_claimed",
        },
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {
        "task": TASK,
        "status": "running",
        "started_at": now(),
        "hostname": platform.node(),
        "pid": os.getpid(),
        "native_cfd_outputs_mutated": False,
        "external_cfd_modeling_tools_mutated": False,
        "openfoam_solver_launched": False,
        "substudies": {},
        "commands": [],
    }
    write_json(OUT / "summary.json", summary)
    event("runner", "start", hostname=summary["hostname"], pid=summary["pid"])
    try:
        summary["commands"].append(run_cmd([sys.executable, "-m", "unittest", "tools.analyze.test_mdot_temperature_probe_error_audit"], log_name="00_unittest.log"))
        event("agent360_refresh", "start")
        summary["substudies"]["agent360_refresh"] = audit.build(OUT / "agent360_refresh", execute_fluid=True)
        event("agent360_refresh", "complete", output=rel(OUT / "agent360_refresh"))
        case_table, heat_by, refs, fluid_cases = case_context()
        summary["substudies"]["setup_only_cooler_closure_bakeoff"] = setup_only_cooler_study(case_table)
        summary["substudies"]["test_section_boundary_form_bakeoff"] = test_section_boundary_study(case_table, heat_by, refs, fluid_cases)
        summary["substudies"]["reference_state_temperature_audit"] = reference_state_diagnostic()
        summary["substudies"]["pressure_root_solver_quality_audit"] = pressure_root_qa(case_table, heat_by, fluid_cases)
        summary["status"] = "complete"
        summary["finished_at"] = now()
        event("runner", "complete")
    except Exception as exc:
        summary["status"] = "failed"
        summary["finished_at"] = now()
        summary["error"] = str(exc)
        summary["traceback"] = traceback.format_exc()
        event("runner", "failed", error=str(exc), traceback=summary["traceback"])
    finally:
        write_closeout(summary)
    return 0 if summary["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
