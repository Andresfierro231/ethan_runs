#!/usr/bin/env python3
"""Build AGENT-409 closure-QOI, hydraulic, and scratch postprocess artifacts."""

from __future__ import annotations

import csv
import json
import math
import socket
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
TASK = "AGENT-409"
DATE = "2026-07-15"
OUT_REL = Path("work_products/2026-07/2026-07-15/2026-07-15_lead_closure_qoi_hydraulic_postprocess")
TMP_REL = Path("tmp/2026-07-15_lead_closure_qoi_hydraulic_postprocess")
PACKAGE = ROOT / OUT_REL
TMP = ROOT / TMP_REL
SCRIPTS = PACKAGE / "scripts"
LOGS = PACKAGE / "logs"

AGENT405 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_sensor_policy_gate_opening_and_hydraulic_node_run"
AGENT406 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair"
CLOSURE_GATE = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/refreshed_qoi_mesh_gate_status.csv"
THERMAL_ADMISSION = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/thermal_admission_table.csv"
MESH_ROOT = ROOT / "work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines"
OF_ENV = ROOT / "tools/ofenv/of13_env.sh"

RAW_CASES = [
    ("salt_2", "salt2_mainline", "viscosity_screening_salt_test_2_jin_coarse_mesh", "7915", "tmp/2026-06-30_claude_action_items/recon_salt2_of13", "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation"),
    ("salt_3", "salt3_mainline", "viscosity_screening_salt_test_3_jin_coarse_mesh", "7618", "tmp/2026-06-30_claude_action_items/recon_salt3_of13", "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt3_jin/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh_continuation"),
    ("salt_4", "salt4_mainline", "viscosity_screening_salt_test_4_jin_coarse_mesh", "10000", "tmp/2026-06-30_claude_action_items/recon_salt4_of13", "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt4_jin/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"),
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str] | None = None) -> int:
    materialized = list(rows)
    if fieldnames is None:
        fieldnames = list(materialized[0].keys()) if materialized else []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fmt(value: Any, precision: int = 10) -> str:
    if value is None:
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(number):
        return ""
    return f"{number:.{precision}g}"


def yes(value: str) -> bool:
    return str(value).strip().lower() in {"yes", "true", "1", "y"}


def closure_bucket(row: dict[str, str]) -> tuple[str, str, str]:
    blockers = row.get("blockers", "").lower()
    gci = row.get("gci_status", "").lower()
    conv = row.get("convergence_verdict", "").lower()
    if yes(row.get("publication_ready", "")):
        return ("admitted_publication_ready", "none", "No blocker.")
    if not yes(row.get("complete_triplet", "")):
        return ("blocked_missing_triplet", "extract_missing_mesh_level_qoi", "Missing coarse/medium/fine numeric QoI prevents GCI.")
    if "oscill" in conv or "non_monotone" in gci or "non-monotone" in row.get("classification", "").lower():
        return ("blocked_non_monotone_or_oscillatory", "audit_qoi_definition_or_mesh_family", "Triplet fails monotone/asymptotic gate.")
    if "diverg" in conv or "diverg" in gci:
        return ("blocked_divergent_triplet", "repair_qoi_definition_before_relaunch", "Triplet appears divergent.")
    if "sign" in blockers or "radiation" in blockers:
        return ("blocked_sign_or_semantics_review", "resolve_sign_boundary_radiation_semantics", "Thermal sign/radiation semantics are unresolved.")
    if "nu" in blockers:
        return ("blocked_internal_nu_not_admitted", "keep_internal_nu_closed", "Internal Nu is not fit-admitted.")
    return ("diagnostic_only_unadmitted", "manual_gate_review", "No publication gate admission.")


def build_closure_matrix() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(CLOSURE_GATE):
        status, action, reason = closure_bucket(row)
        rows.append({
            "case_id": row.get("case_id", ""),
            "source_id": row.get("source_id", ""),
            "lane": row.get("lane", ""),
            "qoi_id": row.get("qoi_id", ""),
            "segment": row.get("segment", ""),
            "quantity": row.get("quantity", ""),
            "complete_triplet": row.get("complete_triplet", ""),
            "convergence_verdict": row.get("convergence_verdict", ""),
            "gci_status": row.get("gci_status", ""),
            "publication_ready": row.get("publication_ready", ""),
            "fit_admissible": row.get("fit_admissible", ""),
            "gate_status": status,
            "primary_blocker": reason,
            "next_action": action,
            "blockers": row.get("blockers", ""),
            "coarse_source_path": row.get("coarse_source_path", ""),
            "medium_source_path": row.get("medium_source_path", ""),
            "fine_source_path": row.get("fine_source_path", ""),
            "gci_source_path": row.get("gci_source_path", ""),
        })
    return rows


def station_normal(source_id: str, label: str) -> tuple[float, float, float]:
    payload = read_json(MESH_ROOT / source_id / "mesh_stations.json")
    for row in payload.get("stations", []):
        if row.get("label") == label:
            return (float(row["nx"]), float(row["ny"]), float(row["nz"]))
    raise KeyError(f"missing station {source_id}:{label}")


def parse_plane(path: Path, normal: tuple[float, float, float]) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing", "path": rel(path)}
    n = reverse = 0
    sum_prgh = sum_un = 0.0
    with path.open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 8:
                continue
            ux, uy, uz = float(parts[3]), float(parts[4]), float(parts[5])
            prgh = float(parts[7]) if len(parts) >= 9 else float(parts[6])
            un = ux * normal[0] + uy * normal[1] + uz * normal[2]
            n += 1
            sum_prgh += prgh
            sum_un += un
            reverse += int(un < 0.0)
    if n == 0:
        return {"status": "empty", "path": rel(path)}
    return {
        "status": "parsed_area_proxy",
        "path": rel(path),
        "face_count": n,
        "mean_p_rgh_Pa": sum_prgh / n,
        "mean_normal_velocity_m_s": sum_un / n,
        "reverse_area_fraction_equal_face_proxy": reverse / n,
    }


def build_raw_two_tap() -> list[dict[str, Any]]:
    rows = []
    for case_id, case_key, source_id, time_s, recon_rel, source_case in RAW_CASES:
        lower_label = "left_lower_leg__s00"
        upper_label = "left_upper_leg__s04"
        staged_base = TMP / "raw_two_tap" / case_key / "postProcessing/agent409RawTwoTapSurfaces" / time_s
        existing_base = ROOT / recon_rel / "postProcessing/secmeanSurfaces" / time_s
        use_staged = (staged_base / f"plane_{lower_label}.xy").exists() and (staged_base / f"plane_{upper_label}.xy").exists()
        base = staged_base if use_staged else existing_base
        lower = parse_plane(base / f"plane_{lower_label}.xy", station_normal(source_id, lower_label))
        upper = parse_plane(base / f"plane_{upper_label}.xy", station_normal(source_id, upper_label))
        parsed = lower["status"] == "parsed_area_proxy" and upper["status"] == "parsed_area_proxy"
        origin = "agent409_staged_copy_openfoam" if use_staged else "existing_reconstructed_secmean"
        rows.append({
            "case_id": case_id,
            "source_id": source_id,
            "case_key": case_key,
            "mesh_level": "coarse",
            "representative_time_s": time_s,
            "tap_lower_label": lower_label,
            "tap_upper_label": upper_label,
            "tap_convention": "report_both_signs; no universal upstream/downstream sign assumed under recirculation",
            "lower_mean_p_rgh_Pa": fmt(lower.get("mean_p_rgh_Pa")),
            "upper_mean_p_rgh_Pa": fmt(upper.get("mean_p_rgh_Pa")),
            "delta_p_rgh_upper_minus_lower_Pa": fmt(float(upper["mean_p_rgh_Pa"]) - float(lower["mean_p_rgh_Pa"])) if parsed else "",
            "delta_p_rgh_lower_minus_upper_Pa": fmt(float(lower["mean_p_rgh_Pa"]) - float(upper["mean_p_rgh_Pa"])) if parsed else "",
            "lower_reverse_area_fraction_proxy": fmt(lower.get("reverse_area_fraction_equal_face_proxy")),
            "upper_reverse_area_fraction_proxy": fmt(upper.get("reverse_area_fraction_equal_face_proxy")),
            "lower_face_count": lower.get("face_count", ""),
            "upper_face_count": upper.get("face_count", ""),
            "evidence_origin": origin,
            "admission_status": f"diagnostic_{origin}_parsed_not_fit_admitted" if parsed else "blocked_missing_plane",
            "fit_eligible": "no",
            "blockers": "coarse_only_no_mesh_gci;reduced_pressure_plane_proxy;recirculation_and_component_policy_unresolved" if parsed else "missing_existing_secmean_plane;run_staged_raw_two_tap",
            "lower_plane_file": lower.get("path", ""),
            "upper_plane_file": upper.get("path", ""),
            "staged_copy_runner": rel(SCRIPTS / "run_staged_raw_two_tap.sh"),
            "source_case": source_case,
        })
    return rows


def write_runner() -> None:
    SCRIPTS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    case_lines = "\n".join("|".join([case_key, source_case, time_s]) for _, case_key, _, time_s, _, source_case in RAW_CASES)
    script = f"""#!/usr/bin/env bash
set -euo pipefail
ROOT={ROOT}
OUT="$ROOT/{OUT_REL}"
TMP="$ROOT/{TMP_REL}"
LOG_DIR="$OUT/logs"
OF_ENV="$ROOT/{rel(OF_ENV)}"
mkdir -p "$LOG_DIR" "$TMP/raw_two_tap"
cd "$ROOT"
log() {{ printf '[%s] %s\\n' "$(date --iso-8601=seconds)" "$*" >&2; }}
die() {{ log "ERROR: $*"; exit 1; }}
write_control_dict() {{
  local case_dir="$1"
  cat > "$case_dir/system/controlDict" <<'CONTROL'
FoamFile {{ version 2.0; format ascii; class dictionary; object controlDict; }}
application foamRun; startTime 0; stopAt endTime; endTime 1000000; deltaT 1;
writeControl timeStep; writeInterval 1; writeFormat ascii; writePrecision 10;
writeCompression off; timeFormat general; timePrecision 10; runTimeModifiable false;
functions {{
  agent409RawTwoTapSurfaces {{
    type            surfaces;
    libs            ("libsampling.so");
    writeControl    writeTime;
    surfaceFormat   raw;
    interpolate     false;
    interpolationScheme cell;
    fields          (U p p_rgh rho);
    surfaces (
      plane_left_lower_leg__s00 {{
        type cuttingPlane; planeType pointAndNormal;
        pointAndNormalDict {{ point (1.85606127216e-13 0.0486021944432 0); normal (-1.19827685174e-12 1 0); }}
      }}
      plane_left_upper_leg__s04 {{
        type cuttingPlane; planeType pointAndNormal;
        pointAndNormalDict {{ point (-1.04166497973e-13 0.895903471523 0); normal (6.93310699107e-14 1 0); }}
      }}
    );
  }}
}}
CONTROL
}}
run_one() {{
  local case_key="$1" source_case="$2" time_s="$3"
  local source_abs="$ROOT/$source_case"
  local case_dir="$TMP/raw_two_tap/$case_key"
  [[ -d "$source_abs/processors64/$time_s" ]] || die "missing processor time $source_abs/processors64/$time_s"
  mkdir -p "$case_dir"
  for name in constant system 0; do
    [[ -e "$source_abs/$name" ]] || die "missing $source_abs/$name"
    if [[ ! -e "$case_dir/$name" ]]; then cp -a "$source_abs/$name" "$case_dir/$name"; fi
  done
  ln -sfn "$source_abs/processors64" "$case_dir/processors64"
  if [[ -e "$case_dir/system/functions" || -L "$case_dir/system/functions" ]]; then mv "$case_dir/system/functions" "$case_dir/system/functions.agent409_disabled.$(date +%s)"; fi
  write_control_dict "$case_dir"
  if [[ ! -d "$case_dir/$time_s" ]]; then
    timeout 90m bash -lc "source '$OF_ENV' >/dev/null 2>&1 && reconstructPar -case '$case_dir' -time '$time_s' -fields '(U p p_rgh rho)'" > "$LOG_DIR/reconstruct_${{case_key}}.log" 2>&1
  fi
  timeout 60m bash -lc "source '$OF_ENV' >/dev/null 2>&1 && foamPostProcess -case '$case_dir' -time '$time_s'" > "$LOG_DIR/raw_two_tap_${{case_key}}.log" 2>&1
}}
requested="${{1:-all}}"
while IFS='|' read -r case_key source_case time_s; do
  [[ -n "$case_key" ]] || continue
  if [[ "$requested" == "all" || "$requested" == "$case_key" ]]; then run_one "$case_key" "$source_case" "$time_s"; fi
done <<'CASES'
{case_lines}
CASES
python3.11 tools/analyze/build_lead_closure_qoi_hydraulic_postprocess.py
log "AGENT-409 staged raw two-tap runner complete"
"""
    runner = SCRIPTS / "run_staged_raw_two_tap.sh"
    runner.write_text(script, encoding="utf-8")
    runner.chmod(0o755)


def build_hydraulic_status(pm5_rows: list[dict[str, str]], raw_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    decisions = {row.get("gate_item", ""): row for row in read_csv(AGENT405 / "hydraulic_admission_decisions.csv")}
    pm5_counts = Counter(row.get("metric_status", "") for row in pm5_rows)
    pm5_rollup = [
        {
            "case_key": case_key,
            "row_count": sum(1 for row in pm5_rows if row.get("case_key") == case_key),
            "wallHeatFlux_available_rows": sum(1 for row in pm5_rows if row.get("case_key") == case_key and row.get("wallHeatFlux_available") == "true"),
            "metric_statuses": ";".join(sorted({row.get("metric_status", "") for row in pm5_rows if row.get("case_key") == case_key})),
            "admission_statuses": ";".join(sorted({row.get("admission_status", "") for row in pm5_rows if row.get("case_key") == case_key})),
        }
        for case_key in sorted({row.get("case_key", "") for row in pm5_rows})
    ]
    gates = [
        {
            "gate": "raw_two_tap_test_section_complex",
            "current_state": "diagnostic_landed_not_fit_admitted" if sum(r["admission_status"].startswith("diagnostic") for r in raw_rows) == 3 else "blocked_not_admitted",
            "evidence_now": "AGENT-409 scratch OpenFOAM raw two-tap surfaces completed for Salt2/Salt3/Salt4; AGENT-405 status was preflight-only.",
            "math_needed": "Delta_p_two_tap reported as both p_rgh sign conventions; K requires admitted pressure definition and straight-loss subtraction.",
            "why_not_admitted": "Coarse-only reduced-pressure proxy with recirculation and no mesh/GCI component admission.",
            "next_required_run": rel(SCRIPTS / "run_staged_raw_two_tap.sh"),
        },
        {
            "gate": "pm5_matched_pressure_upcomer",
            "current_state": "diagnostic_complete_not_final",
            "evidence_now": f"AGENT-406 PM5 metric statuses: {dict(pm5_counts)}.",
            "math_needed": "Reverse fractions, Re, Pr, Ri, Gr, Ra, wall-band T, and wallHeatFlux support pressure/onset review only.",
            "why_not_admitted": "Rows are scratch diagnostics until a downstream cfd-pp/hydraulic gate admits them.",
            "next_required_run": "F6/onset scorecard over admitted PM5 rows.",
        },
        {
            "gate": "final_hydraulic_residual_attribution",
            "current_state": "blocked_not_final",
            "evidence_now": decisions.get("final_hydraulic_residual_attribution", {}).get("evidence", "Prior attribution is provisional."),
            "math_needed": "Residual = observed_delta_p - model_delta_p, decomposed into straight, localized K, reset/development K, recirculation/onset, and residual terms.",
            "why_not_admitted": "No fit-admitted raw pressure/F6 evidence landed.",
            "next_required_run": "Recompute only after raw pressure and F6 gates admit rows.",
        },
    ]
    residual = [
        {
            "residual_component": "test_section_complex_pressure_drop",
            "current_attribution": "diagnostic_unassigned",
            "admitted_input": "none_fit_admitted",
            "evidence": "Three reduced-pressure diagnostic rows parsed.",
            "math_or_theory": "Connector two-tap pressure loss must be admitted before subtracting adjacent distributed loss.",
            "result_after_agent409": "improved_from_preflight_to_diagnostic",
            "limitation": "No component K fit; no mesh/GCI.",
        },
        {
            "residual_component": "pm5_upcomer_recirculation_pressure_onset",
            "current_attribution": "diagnostic_pressure_onset_evidence_landed",
            "admitted_input": "none_final",
            "evidence": f"{len(pm5_rows)} AGENT-406 PM5 rows.",
            "math_or_theory": "Reverse fractions and Ri/Re/Pr indicate mixed/recirculating conditions.",
            "result_after_agent409": "cited_read_only",
            "limitation": "Does not reopen true internal-Nu fit.",
        },
        {
            "residual_component": "final_hydraulic_residual",
            "current_attribution": "not_final",
            "admitted_input": "diagnostic reset-K only",
            "evidence": "Raw two-tap diagnostic only; PM5 diagnostic only; F6 not final.",
            "math_or_theory": "Final attribution requires observed pressure residual magnitudes.",
            "result_after_agent409": "still_blocked_for_right_reasons",
            "limitation": "Cannot assign final numeric residual magnitudes yet.",
        },
    ]
    return gates, residual, pm5_rollup


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""# AGENT-409 Lead Closure-QOI / Hydraulic Postprocess

Created: `{summary['created_utc']}`

## Result

This package makes the unblock plan executable without mutating native CFD
outputs. Closure-QOI rows are classified, Salt2/Salt3/Salt4 test-section
two-tap diagnostics are harvested from the AGENT-409 scratch OpenFOAM
`agent409RawTwoTapSurfaces` outputs, and a scratch-only OpenFOAM runner is
available at `scripts/run_staged_raw_two_tap.sh`.

Final forward-v1 remains blocked. Internal Nu remains zero fit-admissible.

## Assumptions And Methods

- Native solver outputs were read-only; new commands write only under `{TMP_REL}`.
- Two-tap convention: lower `left_lower_leg__s00`, upper `left_upper_leg__s04`;
  both reduced-pressure signs are reported.
- The scratch raw two-tap surfaces are equal-face proxy diagnostics, not
  mesh/GCI admitted component-K evidence.
- `p_rgh` is reported as reduced pressure and is not silently promoted to a
  universal static-pressure coefficient.
- CFD `rcExternalTemperature` wallHeatFlux includes radiation when present; no
  separate exported radiation term is invented.
- Internal Nu cannot absorb heater, cooler, passive loss, wall storage, or
  radiation residuals.

## Current Blockers

- Closure-QOI mesh/GCI: {summary['closure_gate_status_counts']}
- Raw two-tap: diagnostic rows landed, but fit use is blocked by mesh/GCI,
  pressure-definition, centerline length, and recirculation policy.
- PM5/F6: AGENT-406 rows are useful diagnostics with wallHeatFlux present in
  the scratch VTKs; no final F6 scorecard has admitted rows.
"""
    (PACKAGE / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    PACKAGE.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    write_runner()

    pm5_rows = read_csv(AGENT406 / "resampled_pm5_matched_plane_metrics.csv")
    pm5_summary = read_json(AGENT406 / "summary.json")
    thermal_rows = read_csv(THERMAL_ADMISSION)
    closure = build_closure_matrix()
    raw = build_raw_two_tap()
    hydraulic_gates, residual, pm5_rollup = build_hydraulic_status(pm5_rows, raw)

    launch_counts = Counter(row["gate_status"] for row in closure)
    launch = [
        {
            "gate_status": status,
            "row_count": count,
            "launchable_by_agent409_now": "conditional" if status == "blocked_missing_triplet" else "no",
            "scratch_only_command": rel(SCRIPTS / "run_staged_raw_two_tap.sh") if status == "blocked_missing_triplet" else "",
            "native_outputs_mutated": "false",
            "rationale": "Missing numeric QoIs may be repairable from staged scratch extraction." if status == "blocked_missing_triplet" else "Policy, sign, or convergence failure is not solved by relaunch alone.",
        }
        for status, count in sorted(launch_counts.items())
    ]
    launch.append({
        "gate_status": "hydraulic_test_section_complex_raw_two_tap",
        "row_count": 3,
        "launchable_by_agent409_now": "yes",
        "scratch_only_command": rel(SCRIPTS / "run_staged_raw_two_tap.sh"),
        "native_outputs_mutated": "false",
        "rationale": "AGENT-405 was preflight-only; AGENT-409 provides scratch runner and diagnostic harvest.",
    })

    raw_manifest = []
    for case_id, case_key, _, time_s, _, source_case in RAW_CASES:
        staged_base = TMP / "raw_two_tap" / case_key / "postProcessing/agent409RawTwoTapSurfaces" / time_s
        complete = (staged_base / "plane_left_lower_leg__s00.xy").exists() and (staged_base / "plane_left_upper_leg__s04.xy").exists()
        raw_manifest.append({
            "case_id": case_id,
            "case_key": case_key,
            "source_case": source_case,
            "source_case_exists": str((ROOT / source_case).exists()).lower(),
            "processor_time_exists": str((ROOT / source_case / "processors64" / time_s).exists()).lower(),
            "representative_time_s": time_s,
            "staged_case_dir": rel(TMP / "raw_two_tap" / case_key),
            "command": f"{rel(SCRIPTS / 'run_staged_raw_two_tap.sh')} {case_key}",
            "log_path": rel(LOGS / f"raw_two_tap_{case_key}.log"),
            "status": "completed_staged_copy_openfoam" if complete else "ready_to_run_staged_copy",
            "native_solver_outputs_mutated": "false",
        })

    internal = [
        {
            "gate": "true_internal_nu_fit",
            "status": "closed_zero_fit_admissible_rows",
            "fit_admissible_rows_today": sum(1 for row in thermal_rows if yes(row.get("fit_eligible", ""))),
            "diagnostic_rows_available": len(thermal_rows) + len(pm5_rows),
            "evidence": "Thermal admission table remains zero fit-eligible; PM5 rows are recirculation/onset diagnostics.",
            "reopen_condition": "Matched wall/plane rows with wallHeatFlux, low reverse/secondary flow, accepted heat-balance residual, and mesh/GCI admitted triplet.",
        },
        {
            "gate": "Nu_section_effective_upcomer_diagnostic",
            "status": "partial_diagnostic_possible_not_fit_nu",
            "fit_admissible_rows_today": 0,
            "diagnostic_rows_available": len(pm5_rows),
            "evidence": f"{sum(1 for row in pm5_rows if row.get('wallHeatFlux_available') == 'true')}/{len(pm5_rows)} PM5 rows include wallHeatFlux.",
            "reopen_condition": "May label section-effective diagnostics; do not use as single-stream fit Nu.",
        },
    ]
    closure_reopen = [
        {
            "gate_status": status,
            "row_count": count,
            "reopen_status": "open" if status == "blocked_missing_triplet" else "blocked_or_diagnostic",
            "agent409_direct_action": "staged scratch postprocess can target missing numeric QoIs" if status == "blocked_missing_triplet" else "not directly solved by local postprocessing",
            "admission_effect_today": "no_publication_ready_rows_from_agent409",
        }
        for status, count in sorted(launch_counts.items())
    ]
    final_delta = [
        {
            "model_or_gate": "forward_v1_final",
            "before_agent409": "blocked_no_go_final_forward_v1_not_admitted",
            "after_agent409": "blocked_no_go_final_forward_v1_not_admitted",
            "delta": "diagnostic_evidence_added_no_fit_admission",
            "why": "Closure-QOI mesh/GCI has no publication-ready row and internal-Nu remains zero fit-admissible.",
        },
        {
            "model_or_gate": "hydraulic_test_section_complex",
            "before_agent409": "preflight_only_blocked",
            "after_agent409": "diagnostic_reduced_pressure_two_tap_rows_landed",
            "delta": f"{sum(row['admission_status'].startswith('diagnostic') for row in raw)} diagnostic rows parsed",
            "why": "Useful for pressure-scale audit, not enough for universal K fitting.",
        },
    ]
    sources = [
        ("closure_gate", CLOSURE_GATE, "refreshed closure-QOI mesh/GCI status"),
        ("thermal_admission", THERMAL_ADMISSION, "thermal/internal-Nu admission source"),
        ("agent405_hydraulic", AGENT405 / "hydraulic_admission_decisions.csv", "AGENT-405 hydraulic status"),
        ("agent406_pm5", AGENT406 / "resampled_pm5_matched_plane_metrics.csv", "AGENT-406 PM5 metrics"),
        ("agent406_summary", AGENT406 / "summary.json", "AGENT-406 PM5 summary"),
    ]
    source_manifest = [{"source_id": sid, "path": rel(path), "exists": str(path.exists()).lower(), "role": role} for sid, path, role in sources]

    write_csv(PACKAGE / "closure_qoi_failed_gate_matrix.csv", closure)
    write_csv(PACKAGE / "closure_qoi_postprocess_launch_plan.csv", launch)
    write_csv(PACKAGE / "raw_two_tap_test_section_complex.csv", raw)
    write_csv(PACKAGE / "raw_two_tap_postprocess_manifest.csv", raw_manifest)
    write_csv(PACKAGE / "hydraulic_admission_refresh.csv", hydraulic_gates)
    write_csv(PACKAGE / "hydraulic_gate_status_after_pm5.csv", hydraulic_gates)
    write_csv(PACKAGE / "hydraulic_residual_attribution_after_pm5.csv", residual)
    write_csv(PACKAGE / "pm5_matched_pressure_upcomer_rollup.csv", pm5_rollup)
    write_csv(PACKAGE / "internal_nu_reopen_status.csv", internal)
    write_csv(PACKAGE / "closure_qoi_mesh_gci_reopen_status.csv", closure_reopen)
    write_csv(PACKAGE / "final_forward_v1_unblock_delta.csv", final_delta)
    write_csv(PACKAGE / "source_manifest.csv", source_manifest)

    summary = {
        "task": TASK,
        "date": DATE,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "work_product_dir": rel(PACKAGE),
        "scratch_dir": rel(TMP),
        "native_solver_outputs_mutated": False,
        "external_fluid_modified": False,
        "scheduler_jobs_launched": False,
        "registry_or_admission_mutated": False,
        "openfoam_postprocessing_launched_by_builder": False,
        "openfoam_postprocessing_launched_in_agent409_scratch": any((LOGS / f"raw_two_tap_{case_key}.log").exists() for _, case_key, _, _, _, _ in RAW_CASES),
        "staged_openfoam_runner": rel(SCRIPTS / "run_staged_raw_two_tap.sh"),
        "closure_qoi_rows": len(closure),
        "closure_gate_status_counts": dict(launch_counts),
        "raw_two_tap_rows": len(raw),
        "raw_two_tap_diagnostic_rows": sum(row["admission_status"].startswith("diagnostic") for row in raw),
        "raw_two_tap_status": "diagnostic_landed_not_fit_admitted",
        "reset_k_status": "diagnostic_admitted_component_separation_only",
        "pm5_rows": len(pm5_rows),
        "pm5_metric_status_counts": dict(Counter(row.get("metric_status", "") for row in pm5_rows)),
        "pm5_admission_status_counts": dict(Counter(row.get("admission_status", "") for row in pm5_rows)),
        "pm5_vtk_validation_fail_rows": pm5_summary.get("vtk_validation_fail_rows"),
        "internal_nu_fit_admissible_rows_today": 0,
        "f6_status": "reopenable_for_review_not_final",
        "final_hydraulic_residual_status": "blocked_not_final",
        "final_forward_v1_status": "blocked_no_go_final_forward_v1_not_admitted",
    }
    write_json(PACKAGE / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> int:
    print(json.dumps(build(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
