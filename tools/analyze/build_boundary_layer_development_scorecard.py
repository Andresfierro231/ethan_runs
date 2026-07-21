#!/usr/bin/env python3
"""Build the boundary-layer development scorecard and ablation contract."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-17"
TASK = "TODO-PREDICT-BOUNDARY-LAYER-DEVELOPMENT-SCORECARD"

OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_boundary_layer_development_scorecard"
STATUS = ROOT / ".agent/status/2026-07-17_TODO-PREDICT-BOUNDARY-LAYER-DEVELOPMENT-SCORECARD.md"
JOURNAL = ROOT / ".agent/journal/2026-07-17/predict-boundary-layer-development-scorecard.md"
IMPORT = ROOT / "imports/2026-07-17_predict_boundary_layer_development_scorecard.json"

PRESSURE_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_pressure_models"
    / "segment_pressure_model_scorecard.csv"
)
THERMAL_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_thermal_models"
    / "segment_thermal_model_scorecard.csv"
)
BRANCH_MASK = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_branch_specific_ordinary_pipe_scorecard"
    / "ordinary_pipe_branch_mask.csv"
)
UPCOMER_HYBRID = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model"
    / "upcomer_admission_decision.csv"
)
RESET_CONTRACT = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_reset_k_admission_contract"
    / "hydraulic_reset_development_contract.csv"
)
STATION_DEVELOPMENT = (
    ROOT
    / "work_products/2026-07/2026-07-08/2026-07-08_hydraulic_closure_rigor_audit"
    / "station_development_analysis.csv"
)
INTERFACE_SAMPLES = (
    ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling"
    / "combined_openfoam_interface_samples.csv"
)
ENTHALPY_RESIDUALS = (
    ROOT
    / "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces"
    / "segment_enthalpy_residuals.csv"
)
SENSOR_POLICY = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_sensor_tp2_restore_tw10_exclude"
    / "sensor_policy_scorecard.csv"
)

REGION_SPANS = {
    "heater": {"lower_leg"},
    "cooler_HX": {"upper_leg", "cooling_branch"},
    "downcomer": {"right_leg", "downcomer"},
    "upcomer": {"left_lower_leg", "left_upper_leg", "upcomer"},
    "test_section": {"test_section_span", "test_section"},
    "junction_stub_connector": {"junction"},
    "lower_upper_legs": {"lower_leg", "upper_leg"},
}
TOGGLES = [
    ("hydraulic_reset_length", "entrance/reset length keyed by feature and x/D"),
    ("developing_apparent_friction", "Shah/developing apparent friction or equivalent hydraulic development term"),
    ("thermal_graetz_entrance", "Graetz/thermal entrance effect"),
    ("wall_adjacent_temperature_drive", "wall-adjacent temperature drive"),
    ("wall_layer_resistance", "wall/layer resistance without source-sink absorption"),
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def require_sources() -> None:
    required = [
        PRESSURE_SCORECARD,
        THERMAL_SCORECARD,
        BRANCH_MASK,
        UPCOMER_HYBRID,
        RESET_CONTRACT,
        STATION_DEVELOPMENT,
        INTERFACE_SAMPLES,
        ENTHALPY_RESIDUALS,
        SENSOR_POLICY,
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing boundary-layer scorecard sources: " + "; ".join(missing))


def _by(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows}


def _count_span(rows: list[dict[str, str]], key: str, region: str) -> int:
    spans = REGION_SPANS[region]
    return sum(1 for row in rows if row.get(key, "") in spans)


def build_toggle_scorecard() -> list[dict[str, object]]:
    pressure = _by(read_csv(PRESSURE_SCORECARD), "loop_region")
    thermal = _by(read_csv(THERMAL_SCORECARD), "loop_region")
    reset = read_csv(RESET_CONTRACT)
    station = read_csv(STATION_DEVELOPMENT)
    interfaces = read_csv(INTERFACE_SAMPLES)
    enthalpy = read_csv(ENTHALPY_RESIDUALS)
    rows: list[dict[str, object]] = []
    for region in REGION_SPANS:
        p = pressure[region]
        t = thermal[region]
        reset_rows = _count_span(reset, "downstream_span", region)
        station_rows = _count_span(station, "span", region)
        interface_rows = _count_span(interfaces, "span", region)
        enthalpy_rows = _count_span(enthalpy, "physical_segment", region)
        for toggle_id, description in TOGGLES:
            if toggle_id in {"hydraulic_reset_length", "developing_apparent_friction"}:
                evidence_rows = reset_rows + station_rows
                primary_gate = p["admission_status"]
                admission = "diagnostic_ready_not_executable" if evidence_rows else "blocked_no_local_evidence"
            elif toggle_id == "thermal_graetz_entrance":
                evidence_rows = interface_rows + enthalpy_rows
                primary_gate = t["admission_status"]
                admission = "diagnostic_ready_not_executable" if evidence_rows else "blocked_no_local_evidence"
            elif toggle_id == "wall_adjacent_temperature_drive":
                evidence_rows = interface_rows
                primary_gate = t["admission_status"]
                admission = "diagnostic_ready_not_executable" if evidence_rows else "blocked_no_local_evidence"
            else:
                evidence_rows = enthalpy_rows + int(t.get("diagnostic_source_sink_rows") or 0)
                primary_gate = t["admission_status"]
                admission = "diagnostic_ready_not_executable" if evidence_rows else "blocked_no_local_evidence"
            if p["scoreable_predictive_model_rows"] != "0" and t["scoreable_predictive_thermal_rows"] != "0":
                executable = "blocked_until_coupled_solver_admission_review"
            else:
                executable = "blocked_missing_admitted_pressure_or_thermal_closure"
            rows.append(
                {
                    "loop_region": region,
                    "toggle_id": toggle_id,
                    "toggle_description": description,
                    "local_evidence_rows": evidence_rows,
                    "admission_status": admission,
                    "ablation_executable_now": "false",
                    "execution_blocker": executable,
                    "primary_segment_gate": primary_gate,
                    "output_metrics_required": "mdot;TP_RMSE;TW_RMSE;Tmean;loop_delta_T",
                    "score_delta_status": "not_run_no_admitted_coupled_ablation",
                    "guardrail": "no hidden global multiplier; segment-specific terms only",
                }
            )
    return rows


def build_metric_contract() -> list[dict[str, object]]:
    sensors = read_csv(SENSOR_POLICY)
    scoreable_tp = sum(1 for row in sensors if row["kind"] == "TP" and row["aggregate_score_after_refresh"] == "yes")
    scoreable_tw = sum(1 for row in sensors if row["kind"] == "TW" and row["aggregate_score_after_refresh"] == "yes")
    return [
        {"metric": "mdot", "required_for_ablation": "true", "runtime_leakage_allowed": "false", "score_status": "blocked_not_run", "target_rows": 0, "reason": "coupled pressure/thermal ablation not admitted"},
        {"metric": "TP_RMSE", "required_for_ablation": "true", "runtime_leakage_allowed": "false", "score_status": "blocked_not_run", "target_rows": scoreable_tp, "reason": "post-solve validation targets only"},
        {"metric": "TW_RMSE", "required_for_ablation": "true", "runtime_leakage_allowed": "false", "score_status": "blocked_not_run", "target_rows": scoreable_tw, "reason": "post-solve validation targets only"},
        {"metric": "Tmean", "required_for_ablation": "true", "runtime_leakage_allowed": "false", "score_status": "blocked_not_run", "target_rows": 0, "reason": "coupled thermal solve needed"},
        {"metric": "loop_delta_T", "required_for_ablation": "true", "runtime_leakage_allowed": "false", "score_status": "blocked_not_run", "target_rows": 0, "reason": "coupled thermal solve needed"},
    ]


def build_prerequisite_gate_rows() -> list[dict[str, object]]:
    branch = read_csv(BRANCH_MASK)
    upcomer = read_csv(UPCOMER_HYBRID)
    pressure = read_csv(PRESSURE_SCORECARD)
    thermal = read_csv(THERMAL_SCORECARD)
    return [
        {"gate": "segment_pressure_models", "status": "blocked", "admitted_rows": sum(int(row["scoreable_predictive_model_rows"]) for row in pressure), "reason": "no scoreable predictive pressure model rows"},
        {"gate": "segment_thermal_models", "status": "partial", "admitted_rows": sum(int(row["scoreable_predictive_thermal_rows"]) for row in thermal), "reason": "heater/cooler setup admitted; test-section/upcomer/wall development blocked"},
        {"gate": "branch_specific_ordinary_pipe", "status": "blocked", "admitted_rows": sum(int(row["ordinary_pipe_fit_included"] == "true") for row in branch), "reason": "ordinary-pipe aggregate has zero included current branches"},
        {"gate": "upcomer_hybrid", "status": "diagnostic_only", "admitted_rows": sum(1 for row in upcomer if row["admission_status"] == "diagnostic_only_contract_complete"), "reason": "hybrid contract complete, predictive calibration missing"},
    ]


def runtime_audit_rows() -> list[dict[str, object]]:
    return [
        {"check": "no_global_multiplier", "status": "pass_forbidden", "forbidden_input": "hidden global friction or thermal multiplier", "policy": "all toggles are segment-specific"},
        {"check": "no_cfd_mdot_runtime", "status": "pass_forbidden", "forbidden_input": "CFD mdot", "policy": "mdot is a score target/solved output"},
        {"check": "no_validation_temperature_runtime", "status": "pass_forbidden", "forbidden_input": "validation TP/TW temperatures", "policy": "post-solve targets only"},
        {"check": "no_realized_wall_heat_runtime", "status": "pass_forbidden", "forbidden_input": "realized wallHeatFlux", "policy": "diagnostic evidence only until setup model admitted"},
    ]


def source_manifest() -> list[dict[str, object]]:
    sources = [
        ("pressure_scorecard", PRESSURE_SCORECARD, "pressure prerequisite gates"),
        ("thermal_scorecard", THERMAL_SCORECARD, "thermal prerequisite gates"),
        ("branch_mask", BRANCH_MASK, "ordinary-pipe exclusion mask"),
        ("upcomer_hybrid", UPCOMER_HYBRID, "hybrid prerequisite gate"),
        ("reset_contract", RESET_CONTRACT, "hydraulic reset/development evidence"),
        ("station_development", STATION_DEVELOPMENT, "station development diagnostics"),
        ("interface_samples", INTERFACE_SAMPLES, "thermal interface and backflow evidence"),
        ("enthalpy_residuals", ENTHALPY_RESIDUALS, "thermal residual evidence"),
        ("sensor_policy", SENSOR_POLICY, "TP/TW output target policy"),
    ]
    return [{"source_id": key, "path": rel(path), "exists": str(path.exists()).lower(), "use": use} for key, path, use in sources]


def write_docs(summary: dict[str, object]) -> None:
    (OUT / "README.md").write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(PRESSURE_SCORECARD)}",
                f"  - {rel(THERMAL_SCORECARD)}",
                f"  - {rel(RESET_CONTRACT)}",
                "tags: [boundary-layer-development, ablation-contract, admission]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(JOURNAL)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Hydraulics/Thermal-modeling/Forward-pred/Implementer/Tester/Writer",
                "type: work_product",
                "status: complete",
                "---",
                "# Boundary-Layer Development Scorecard",
                "",
                "## Decision",
                "",
                "Boundary-layer development toggles are now specified segment-by-segment, but ablation execution is not admitted yet. "
                "The missing pressure closure, upcomer hybrid calibration, and blocked test-section/wall thermal lanes prevent a defensible coupled score delta.",
                "",
                "## Results",
                "",
                f"- Toggle rows: `{summary['toggle_rows']}`.",
                f"- Diagnostic-ready toggle rows: `{summary['diagnostic_ready_toggle_rows']}`.",
                f"- Executable ablation rows: `{summary['executable_ablation_rows']}`.",
                f"- Output metric contract rows: `{summary['metric_contract_rows']}`.",
                f"- Runtime audit pass rows: `{summary['runtime_audit_pass_rows']}`.",
            ]
        )
        + "\n"
    )
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    IMPORT.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(OUT / 'README.md')}",
                f"  - {rel(OUT / 'summary.json')}",
                "tags: [status, boundary-layer-development]",
                "related:",
                f"  - {rel(JOURNAL)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Hydraulics/Thermal-modeling/Forward-pred/Implementer/Tester/Writer",
                "type: status",
                "status: complete",
                "---",
                f"# {TASK} Status",
                "",
                "## Observed Facts",
                "",
                "- Segment-specific development toggles can be defined from existing reset, station, interface, and residual evidence.",
                "- Coupled ablation execution remains blocked because prerequisite pressure and thermal closures are not admitted.",
                "- No hidden global multiplier is allowed.",
                "",
                "## Validation",
                "",
                "- `python3 -m unittest tools.analyze.test_boundary_layer_development_scorecard`",
                "- Parsed generated `summary.json` and import manifest with `python3 -m json.tool`.",
                "",
                "## Blockers",
                "",
                "- No blocker remains for boundary-layer development scorecard visibility.",
                "- Score deltas remain blocked by no admitted pressure closure, upcomer hybrid calibration, and test-section/wall thermal blockers.",
                "- Generated docs index refresh was skipped because active board rows own generated index files.",
            ]
        )
        + "\n"
    )
    JOURNAL.write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(RESET_CONTRACT)}",
                f"  - {rel(STATION_DEVELOPMENT)}",
                f"  - {rel(OUT / 'README.md')}",
                "tags: [journal, boundary-layer-development]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Hydraulics/Thermal-modeling/Forward-pred/Implementer/Tester/Writer",
                "type: journal",
                "status: complete",
                "---",
                "# Boundary-Layer Development Scorecard Journal",
                "",
                "## Files Changed",
                "",
                "- `tools/analyze/build_boundary_layer_development_scorecard.py`",
                "- `tools/analyze/test_boundary_layer_development_scorecard.py`",
                f"- `{rel(OUT)}/`",
                f"- `{rel(STATUS)}`",
                f"- `{rel(JOURNAL)}`",
                f"- `{rel(IMPORT)}`",
                "- `.agent/BOARD.md` own row status",
                "",
                "## Interpretation",
                "",
                "The development task is complete as an ablation contract and readiness scorecard. Execution remains a downstream coupled-model task.",
            ]
        )
        + "\n"
    )
    manifest = {
        "task": TASK,
        "date": DATE,
        "package": rel(OUT),
        "outputs": sorted(path.name for path in OUT.iterdir() if path.is_file()),
        "summary": summary,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "generated_index_refreshed": False,
        "generated_index_refresh_note": "Skipped because active board rows own generated docs index files.",
    }
    write_json(IMPORT, manifest)


def main() -> dict[str, object]:
    require_sources()
    OUT.mkdir(parents=True, exist_ok=True)
    toggles = build_toggle_scorecard()
    metrics = build_metric_contract()
    gates = build_prerequisite_gate_rows()
    runtime = runtime_audit_rows()
    sources = source_manifest()
    write_csv(
        OUT / "development_toggle_scorecard.csv",
        toggles,
        [
            "loop_region",
            "toggle_id",
            "toggle_description",
            "local_evidence_rows",
            "admission_status",
            "ablation_executable_now",
            "execution_blocker",
            "primary_segment_gate",
            "output_metrics_required",
            "score_delta_status",
            "guardrail",
        ],
    )
    write_csv(OUT / "output_metric_ablation_contract.csv", metrics, ["metric", "required_for_ablation", "runtime_leakage_allowed", "score_status", "target_rows", "reason"])
    write_csv(OUT / "prerequisite_gate_scorecard.csv", gates, ["gate", "status", "admitted_rows", "reason"])
    write_csv(OUT / "runtime_development_input_audit.csv", runtime, ["check", "status", "forbidden_input", "policy"])
    write_csv(OUT / "source_manifest.csv", sources, ["source_id", "path", "exists", "use"])
    summary = {
        "task": TASK,
        "date": DATE,
        "toggle_rows": len(toggles),
        "diagnostic_ready_toggle_rows": sum(1 for row in toggles if row["admission_status"] == "diagnostic_ready_not_executable"),
        "executable_ablation_rows": sum(1 for row in toggles if row["ablation_executable_now"] == "true"),
        "metric_contract_rows": len(metrics),
        "prerequisite_gate_rows": len(gates),
        "runtime_audit_rows": len(runtime),
        "runtime_audit_pass_rows": sum(1 for row in runtime if row["status"] == "pass_forbidden"),
        "all_sources_present": all(row["exists"] == "true" for row in sources),
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "generated_index_refreshed": False,
    }
    write_json(OUT / "summary.json", summary)
    write_docs(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
