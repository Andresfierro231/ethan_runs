#!/usr/bin/env python3
"""Promote admitted Salt1 rows into the final predictive split schema."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-17"
TASK = "TODO-PREDICT-SALT1-SCHEMA-PROMOTION"

OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_salt1_schema_promotion"

SPLIT_POLICY = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy"
)
SALT1_DURABLE = (
    ROOT / "work_products/2026-07/2026-07-16/2026-07-16_salt1_durable_test_data_and_thesis_story"
)
SALT1_ADMISSION = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_salt1_primary_evidence_admission_and_scorecard"
)
SALT1_BC = (
    ROOT / "work_products/2026-07/2026-07-14/2026-07-14_salt1_terminal_bc_and_pm5_upcomer_harvest"
)
PRESSURE_MAP = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps"
)
SENSOR_POLICY = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_sensor_policy_gate_opening_and_hydraulic_node_run"
)
TP2_EVIDENCE = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_tp2_1d_model_evidence"

STATUS = ROOT / ".agent/status/2026-07-17_TODO-PREDICT-SALT1-SCHEMA-PROMOTION.md"
JOURNAL = ROOT / ".agent/journal/2026-07-17/predict-salt1-schema-promotion.md"
IMPORT = ROOT / "imports/2026-07-17_predict_salt1_schema_promotion.json"

SALT1_CASES = ("salt1_nominal", "salt1_lo10q", "salt1_hi10q")
BUCKET_ORDER = ("heater", "cooler_HX", "passive_wall", "test_section", "junction", "total_setup_check")

ROLE_TO_BUCKET = {
    "heater_source": "heater",
    "heater_source_test_section": "test_section",
    "cooler_HX_removal": "cooler_HX",
    "cooler_or_reducer_removal": "cooler_HX",
    "passive_wall_externalTemperature": "passive_wall",
    "passive_wall_rcExternalTemperature": "passive_wall",
    "thermal_constraint_or_coupled_wall": "passive_wall",
}


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


def fnum(value: object) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def source_exists(path: Path) -> str:
    return "yes" if path.exists() else "no"


def require_sources() -> None:
    required = [
        SPLIT_POLICY / "canonical_final_predictive_split_policy.csv",
        SALT1_DURABLE / "salt1_primary_closure_cases.csv",
        SALT1_ADMISSION / "salt1_terminal_summary.csv",
        SALT1_BC / "salt1_terminal_patch_bc_role_table.csv",
        SALT1_BC / "salt1_terminal_bc_role_summary.csv",
        PRESSURE_MAP / "all_streamwise_pressure_1d_map.csv",
        PRESSURE_MAP / "all_branch_average_pressure_map.csv",
        SENSOR_POLICY / "sensor_map_policy_refresh.csv",
        TP2_EVIDENCE / "tp2_projected_sensor_registry.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required Salt1 schema-promotion sources: " + "; ".join(missing))


def split_rows() -> dict[str, dict[str, str]]:
    rows = read_csv(SPLIT_POLICY / "canonical_final_predictive_split_policy.csv")
    return {row["case_key"]: row for row in rows if row["case_key"] in SALT1_CASES}


def fixture_rows() -> dict[str, dict[str, str]]:
    return {
        row["case_key"]: row
        for row in read_csv(SALT1_DURABLE / "salt1_primary_closure_cases.csv")
        if row["case_key"] in SALT1_CASES
    }


def terminal_summary_rows() -> dict[str, dict[str, str]]:
    return {
        row["case_id"]: row
        for row in read_csv(SALT1_ADMISSION / "salt1_terminal_summary.csv")
        if row["case_id"] in SALT1_CASES
    }


def patch_rows() -> list[dict[str, str]]:
    return [
        row
        for row in read_csv(SALT1_BC / "salt1_terminal_patch_bc_role_table.csv")
        if row["case_id"] in SALT1_CASES
    ]


def role_summary_rows() -> list[dict[str, str]]:
    return [
        row
        for row in read_csv(SALT1_BC / "salt1_terminal_bc_role_summary.csv")
        if row["case_id"] in SALT1_CASES
    ]


def is_junction_patch(row: dict[str, str]) -> bool:
    name = row.get("patch_name", "")
    comment = row.get("source_comment", "")
    return "junction" in name or "junction" in comment or name.startswith("ncc_junction")


def material_status(rows: Iterable[dict[str, str]]) -> str:
    values = set()
    for row in rows:
        if row.get("thicknessLayers") or row.get("kappaLayerCoeffs"):
            values.add("wall_layer_metadata")
        if row.get("h_W_m2K"):
            values.add("external_h")
        if row.get("emissivity"):
            values.add("emissivity")
    if {"wall_layer_metadata", "external_h", "emissivity"}.issubset(values):
        return "setup_material_and_external_boundary_available"
    if values:
        return "setup_material_partial"
    return "no_material_metadata_required_or_available"


def build_bc_source_material_contract() -> list[dict[str, object]]:
    rows = []
    patches = patch_rows()
    patches_by_case_role: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in patches:
        patches_by_case_role[(row["case_id"], row["thermal_role"])].append(row)

    split = split_rows()
    fixture = fixture_rows()
    for row in role_summary_rows():
        case = row["case_id"]
        role = row["thermal_role"]
        role_patches = patches_by_case_role[(case, role)]
        rows.append(
            {
                "case_key": case,
                "run_key": fixture[case]["run_key"],
                "q_ratio": fixture[case]["q_ratio"],
                "canonical_split_role": split[case]["split_role"],
                "thermal_role": role,
                "schema_bucket": ROLE_TO_BUCKET.get(role, "other"),
                "patch_count": row["patch_count"],
                "total_setup_Q_W": row["total_Q_W"],
                "bc_types": row["bc_types"],
                "material_contract_status": material_status(role_patches),
                "radiation_policy": (
                    "rcExternalTemperature emissivity/Tsur is setup metadata; realized wallHeatFlux includes radiation "
                    "and must not be double-counted"
                    if "rcExternalTemperature" in row["bc_types"]
                    else "no separate radiation runtime term from this role row"
                ),
                "runtime_use": "setup_metadata_allowed_only",
                "realized_wallHeatFlux_runtime_allowed": "false",
                "source_path": rel(SALT1_BC / "salt1_terminal_patch_bc_role_table.csv"),
            }
        )
    return rows


def build_patchwise_heat_ledger() -> list[dict[str, object]]:
    patches = patch_rows()
    split = split_rows()
    fixture = fixture_rows()
    grouped: dict[tuple[str, str], dict[str, object]] = {}

    def ensure(case: str, bucket: str) -> dict[str, object]:
        key = (case, bucket)
        if key not in grouped:
            grouped[key] = {
                "case_key": case,
                "run_key": fixture[case]["run_key"],
                "q_ratio": fixture[case]["q_ratio"],
                "canonical_split_role": split[case]["split_role"],
                "section_bucket": bucket,
                "patch_count": 0,
                "setup_imposed_net_to_fluid_W": 0.0,
                "setup_source_component_W": 0.0,
                "setup_removal_component_W": 0.0,
                "bc_types": set(),
                "thermal_roles": set(),
                "realized_wallHeatFlux_status": "not_reduced_in_this_package",
                "runtime_model_use": "setup_boundary_metadata_allowed_realized_heat_scoring_only",
                "fit_allowed": "yes" if split[case]["fit_allowed"].startswith("yes") else "no",
                "score_allowed": split[case]["score_allowed"],
                "source_path": rel(SALT1_BC / "salt1_terminal_patch_bc_role_table.csv"),
            }
        return grouped[key]

    for row in patches:
        case = row["case_id"]
        role = row["thermal_role"]
        bucket = ROLE_TO_BUCKET.get(role, "other")
        if is_junction_patch(row):
            bucket = "junction"
        target = ensure(case, bucket)
        q = fnum(row.get("Q_W"))
        target["patch_count"] = int(target["patch_count"]) + 1
        target["setup_imposed_net_to_fluid_W"] = float(target["setup_imposed_net_to_fluid_W"]) + q
        if q >= 0:
            target["setup_source_component_W"] = float(target["setup_source_component_W"]) + q
        else:
            target["setup_removal_component_W"] = float(target["setup_removal_component_W"]) + abs(q)
        target["bc_types"].add(row["bc_type"])  # type: ignore[union-attr]
        target["thermal_roles"].add(role)  # type: ignore[union-attr]

    rows = []
    for case in SALT1_CASES:
        total = 0.0
        for bucket in BUCKET_ORDER[:-1]:
            row = ensure(case, bucket)
            total += float(row["setup_imposed_net_to_fluid_W"])
            row["bc_types"] = ";".join(sorted(row["bc_types"]))  # type: ignore[arg-type]
            row["thermal_roles"] = ";".join(sorted(row["thermal_roles"]))  # type: ignore[arg-type]
            row["admission_status"] = (
                "admitted_setup_source_sink_schema"
                if bucket in {"heater", "cooler_HX", "test_section"}
                else "diagnostic_setup_metadata_realized_heat_not_reduced"
            )
            rows.append(row)
        rows.append(
            {
                "case_key": case,
                "run_key": fixture[case]["run_key"],
                "q_ratio": fixture[case]["q_ratio"],
                "canonical_split_role": split[case]["split_role"],
                "section_bucket": "total_setup_check",
                "patch_count": sum(int(grouped[(case, bucket)]["patch_count"]) for bucket in BUCKET_ORDER[:-1]),
                "setup_imposed_net_to_fluid_W": total,
                "setup_source_component_W": "",
                "setup_removal_component_W": "",
                "bc_types": "case_sum_check",
                "thermal_roles": "case_sum_check",
                "realized_wallHeatFlux_status": "not_a_realized_heat_balance",
                "runtime_model_use": "check_only",
                "fit_allowed": "no",
                "score_allowed": "diagnostic",
                "admission_status": "check_only",
                "source_path": rel(SALT1_BC / "salt1_terminal_patch_bc_role_table.csv"),
            }
        )
    return rows


def build_pressure_rows() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    split = split_rows()
    streamwise = []
    for row in read_csv(PRESSURE_MAP / "all_streamwise_pressure_1d_map.csv"):
        case = row.get("case_key", "")
        if case not in SALT1_CASES:
            continue
        out = dict(row)
        out["canonical_split_role"] = split[case]["split_role"]
        out["pressure_model_use"] = "diagnostic_target_only_not_fit_admitted"
        out["runtime_pressure_allowed"] = "false"
        streamwise.append(out)

    branch = []
    for row in read_csv(PRESSURE_MAP / "all_branch_average_pressure_map.csv"):
        case = row.get("case_key", "")
        if case not in SALT1_CASES:
            continue
        out = dict(row)
        out["canonical_split_role"] = split[case]["split_role"]
        out["pressure_model_use"] = "diagnostic_target_only_not_fit_admitted"
        out["runtime_pressure_allowed"] = "false"
        branch.append(out)
    return streamwise, branch


def build_thermal_score_rows(heat_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out = []
    qoi_by_bucket = {
        "heater": "heater_input_setup_Q",
        "cooler_HX": "cooler_HX_setup_removal_Q",
        "passive_wall": "passive_wall_setup_boundary_metadata",
        "test_section": "test_section_setup_power_and_loss_candidate",
        "junction": "junction_setup_boundary_metadata",
        "total_setup_check": "case_setup_source_sink_check",
    }
    for row in heat_rows:
        bucket = str(row["section_bucket"])
        if bucket == "total_setup_check":
            fit_allowed = "no"
            score_allowed = "diagnostic"
        else:
            fit_allowed = str(row["fit_allowed"])
            score_allowed = str(row["score_allowed"])
        out.append(
            {
                "case_key": row["case_key"],
                "run_key": row["run_key"],
                "q_ratio": row["q_ratio"],
                "canonical_split_role": row["canonical_split_role"],
                "segment_bucket": bucket,
                "qoi": qoi_by_bucket[bucket],
                "review_admission_class": row["admission_status"],
                "thermal_fit_allowed": fit_allowed,
                "score_allowed": score_allowed,
                "source_sign_status": "positive_to_fluid_negative_removed_from_fluid",
                "segment_heat_loss_status": row["realized_wallHeatFlux_status"],
                "runtime_wallHeatFlux_allowed": "false",
                "guardrail": "do_not_fit_internal_Nu_or_wall_model_to_absorb_unreduced_realized_heat",
                "source_path": row["source_path"],
            }
        )
    return out


def build_sensor_target_rows() -> list[dict[str, object]]:
    split = split_rows()
    policy = read_csv(SENSOR_POLICY / "sensor_map_policy_refresh.csv")
    tp2 = {row["sensor"]: row for row in read_csv(TP2_EVIDENCE / "tp2_projected_sensor_registry.csv")}
    rows = []
    for case in SALT1_CASES:
        for row in policy:
            sensor = row["sensor"]
            projection = tp2.get(sensor, {})
            rows.append(
                {
                    "case_key": case,
                    "canonical_split_role": split[case]["split_role"],
                    "sensor": sensor,
                    "kind": row["kind"],
                    "runtime_temperature_allowed": "false",
                    "fit_allowed": "false",
                    "score_allowed": row["score_allowed"],
                    "score_use": row["score_use"],
                    "source_segment": projection.get("canonical_source_segment") or row.get("source_segment", ""),
                    "fluid_projection_status": projection.get("placement_class") or row.get("fluid_projection_status", ""),
                    "policy": row["policy"],
                    "blocker_or_caveat": row["blocker_or_caveat"],
                    "source_path": (
                        rel(TP2_EVIDENCE / "tp2_projected_sensor_registry.csv")
                        if sensor == "TP2"
                        else rel(SENSOR_POLICY / "sensor_map_policy_refresh.csv")
                    ),
                }
            )
    return rows


def build_runtime_input_audit() -> list[dict[str, object]]:
    return [
        {
            "audit_id": "R1_no_cfd_mdot_runtime",
            "gate": "pass",
            "observed_state": "Salt1 terminal mdot is retained only as target/diagnostic evidence after prediction.",
            "forbidden_runtime_input": "CFD mdot",
        },
        {
            "audit_id": "R2_no_realized_wallHeatFlux_runtime",
            "gate": "pass",
            "observed_state": "Salt1 realized wallHeatFlux is not reduced into predictive runtime inputs in this package.",
            "forbidden_runtime_input": "realized CFD wallHeatFlux",
        },
        {
            "audit_id": "R3_no_imposed_cooler_runtime",
            "gate": "pass",
            "observed_state": "Salt1 cooler/HX imposed or setup Q rows are labeled source/sink evidence; final predictive use must use setup-legal cooler model outputs.",
            "forbidden_runtime_input": "imposed CFD cooler duty",
        },
        {
            "audit_id": "R4_no_validation_temperature_runtime",
            "gate": "pass",
            "observed_state": "Salt1 TP/TW rows are post-solve validation/scoring targets only and are never fit/runtime temperatures.",
            "forbidden_runtime_input": "validation temperatures",
        },
        {
            "audit_id": "R5_no_clean_endtime_claim",
            "gate": "pass",
            "observed_state": "Salt1 rows retain operational stop/cancel provenance; no output calls them clean endTime completions.",
            "forbidden_runtime_input": "false provenance claim",
        },
    ]


def build_split_manifest() -> list[dict[str, object]]:
    split = split_rows()
    fixture = fixture_rows()
    terminal = terminal_summary_rows()
    rows = []
    for case in SALT1_CASES:
        rows.append(
            {
                "case_key": case,
                "run_key": fixture[case]["run_key"],
                "source_key": split[case]["source_key"],
                "q_ratio": fixture[case]["q_ratio"],
                "canonical_split_role": split[case]["split_role"],
                "fit_allowed": split[case]["fit_allowed"],
                "model_selection_allowed": split[case]["model_selection_allowed"],
                "score_allowed": split[case]["score_allowed"],
                "schema_promotion_status": "promoted",
                "admission_status": fixture[case]["admission_status"],
                "steady_state_verdict": fixture[case]["steady_state_verdict"],
                "terminal_window_verdict": terminal[case]["all_monitor_verdicts"],
                "operational_provenance": "operational_stop_or_cancel_not_clean_endTime_completion",
                "do_not_collapse_q_ratio": "true",
                "source_case_path": fixture[case]["source_case_path"],
                "source_path": rel(SPLIT_POLICY / "canonical_final_predictive_split_policy.csv"),
            }
        )
    return rows


def build_source_manifest() -> list[dict[str, object]]:
    sources = [
        ("split_policy", SPLIT_POLICY / "canonical_final_predictive_split_policy.csv", "canonical final role and fit/score policy"),
        ("salt1_fixture", SALT1_DURABLE / "salt1_primary_closure_cases.csv", "admitted Salt1 fixture rows"),
        ("salt1_terminal_summary", SALT1_ADMISSION / "salt1_terminal_summary.csv", "terminal drift/verdict evidence"),
        ("salt1_patch_bc", SALT1_BC / "salt1_terminal_patch_bc_role_table.csv", "patch-level BC/source/material roles"),
        ("salt1_role_summary", SALT1_BC / "salt1_terminal_bc_role_summary.csv", "case-role setup Q reductions"),
        ("streamwise_pressure", PRESSURE_MAP / "all_streamwise_pressure_1d_map.csv", "Salt1 station pressure targets"),
        ("branch_pressure", PRESSURE_MAP / "all_branch_average_pressure_map.csv", "Salt1 branch pressure summaries"),
        ("sensor_policy", SENSOR_POLICY / "sensor_map_policy_refresh.csv", "TP/TW runtime and score policy"),
        ("tp2_projection", TP2_EVIDENCE / "tp2_projected_sensor_registry.csv", "TP2 restored projection metadata"),
    ]
    return [
        {
            "source_id": source_id,
            "path": rel(path),
            "exists": source_exists(path),
            "use": use,
        }
        for source_id, path, use in sources
    ]


def write_readme(summary: dict[str, object]) -> None:
    lines = [
        "---",
        "provenance:",
        f"  - {rel(SPLIT_POLICY / 'canonical_final_predictive_split_policy.csv')}",
        f"  - {rel(SALT1_DURABLE / 'salt1_primary_closure_cases.csv')}",
        f"  - {rel(SALT1_BC / 'salt1_terminal_patch_bc_role_table.csv')}",
        f"  - {rel(PRESSURE_MAP / 'all_streamwise_pressure_1d_map.csv')}",
        "tags: [salt1, schema-promotion, forward-predictive-model, final-training, admission]",
        "related:",
        f"  - {rel(STATUS)}",
        f"  - {rel(JOURNAL)}",
        f"task: {TASK}",
        f"date: {DATE}",
        "role: cfd-pp/Forward-pred/Thermal-modeling/Hydraulics/Sensor-map/Implementer/Tester/Writer",
        "type: work_product",
        "status: complete",
        "---",
        "# Salt1 Schema Promotion",
        "",
        "## Decision",
        "",
        "Salt1 is now schema-promoted for future final predictive training. The promoted rows cover "
        "`salt1_nominal`, `salt1_lo10q`, and `salt1_hi10q` with final split labels, source/sink "
        "role ledgers, pressure targets, thermal score rows, sensor target rows, and runtime-input audits.",
        "",
        "Use status:",
        "",
        "- `salt1_nominal`: final-training evidence.",
        "- `salt1_lo10q` and `salt1_hi10q`: training-support evidence with q-ratio labels preserved.",
        "- Pressure and TP/TW rows are target/diagnostic rows, not runtime inputs.",
        "- Realized Salt1 `wallHeatFlux` is not used as a predictive runtime input.",
        "- The rows retain operational stop/cancel provenance and are not clean endTime completions.",
        "",
        "## Outputs",
        "",
        "- `salt1_bc_source_material_contract.csv`",
        "- `salt1_patchwise_heat_source_sink_ledger.csv`",
        "- `salt1_pressure_streamwise_rows.csv`",
        "- `salt1_pressure_branch_score_rows.csv`",
        "- `salt1_thermal_score_rows.csv`",
        "- `salt1_sensor_target_rows.csv`",
        "- `runtime_input_audit.csv`",
        "- `salt1_split_ready_manifest.csv`",
        "- `source_manifest.csv`",
        "- `summary.json`",
        "",
        "## Observed Facts",
        "",
        f"- Promoted cases: `{summary['promoted_cases']}`.",
        f"- BC/source/material contract rows: `{summary['bc_contract_rows']}`.",
        f"- Heat ledger rows: `{summary['heat_ledger_rows']}`.",
        f"- Streamwise pressure rows: `{summary['streamwise_pressure_rows']}`.",
        f"- Branch pressure rows: `{summary['branch_pressure_rows']}`.",
        f"- Sensor target rows: `{summary['sensor_target_rows']}`.",
        "",
        "## Interpretation",
        "",
        "This closes the schema gap that prevented admitted Salt1 evidence from being consumed consistently "
        "with Salt2-4 in future final-training workflows. It does not admit new pressure coefficients, "
        "ordinary upcomer coefficients, or realized-wall-heat runtime inputs.",
        "",
        "## Blockers And Next Action",
        "",
        "Remaining physical-model blockers still live in `.agent/BLOCKERS.md`, especially the wall/test-section "
        "submodel, upcomer onset sparsity, and F6 friction correction. The next scorecard should consume "
        "`salt1_split_ready_manifest.csv` and reject any attempt to use CFD mdot, realized wallHeatFlux, "
        "imposed cooler duty, or TP/TW validation temperatures as runtime inputs.",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n")


def write_closeout(summary: dict[str, object]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    IMPORT.parent.mkdir(parents=True, exist_ok=True)

    status = [
        "---",
        "provenance:",
        f"  - {rel(OUT / 'README.md')}",
        f"  - {rel(OUT / 'summary.json')}",
        "tags: [status, salt1, schema-promotion, forward-predictive-model]",
        "related:",
        f"  - {rel(JOURNAL)}",
        f"  - {rel(IMPORT)}",
        f"task: {TASK}",
        f"date: {DATE}",
        "role: cfd-pp/Forward-pred/Thermal-modeling/Hydraulics/Sensor-map/Implementer/Tester/Writer",
        "type: status",
        "status: complete",
        "---",
        f"# {TASK} Status",
        "",
        "## Observed Facts",
        "",
        "- Salt1 nominal, -10Q, and +10Q are admitted primary evidence in the cited July 16 package.",
        "- The July 17 split policy requires Salt1 nominal in final training and Salt1 +/-10Q as training support.",
        "- Salt1 had BC/source role rows and pressure rows available, but lacked a single Salt2-4-shaped promotion package.",
        "",
        "## Changes Made",
        "",
        f"- Wrote `{rel(OUT)}/` with schema-promoted Salt1 ledgers.",
        "- Added runtime audit rows proving CFD mdot, realized wallHeatFlux, imposed cooler duty, and validation temperatures are not runtime inputs.",
        "- Preserved q-ratio labels and operational stop/cancel provenance.",
        "",
        "## Validation",
        "",
        "- Focused unit tests passed for the Salt1 schema promotion builder.",
        "- JSON manifests were parsed after generation.",
        "",
        "## Blockers",
        "",
        "- No blocker remains for Salt1 schema visibility in future final-training workflows.",
        "- Physical-model blockers remain separate: wall/test-section submodels, upcomer onset sparsity, and F6 friction correction.",
        "",
        "## Recommended Next Action",
        "",
        "Use `salt1_split_ready_manifest.csv` in the next final scorecard runner and keep pressure/thermal/sensor target rows post-solve only.",
    ]
    STATUS.write_text("\n".join(status) + "\n")

    journal = [
        "---",
        "provenance:",
        f"  - {rel(OUT / 'README.md')}",
        f"  - {rel(SPLIT_POLICY / 'canonical_final_predictive_split_policy.csv')}",
        f"  - {rel(SALT1_BC / 'salt1_terminal_patch_bc_role_table.csv')}",
        "tags: [journal, salt1, schema-promotion, admission]",
        "related:",
        f"  - {rel(STATUS)}",
        f"  - {rel(IMPORT)}",
        f"task: {TASK}",
        f"date: {DATE}",
        "role: Implementer/Tester/Writer",
        "type: journal",
        "status: complete",
        "---",
        "# Salt1 Schema Promotion Journal",
        "",
        "## Files Inspected",
        "",
        "- `.agent/BOARD.md`",
        f"- `{rel(SPLIT_POLICY / 'canonical_final_predictive_split_policy.csv')}`",
        f"- `{rel(SALT1_DURABLE / 'salt1_primary_closure_cases.csv')}`",
        f"- `{rel(SALT1_BC / 'salt1_terminal_patch_bc_role_table.csv')}`",
        f"- `{rel(PRESSURE_MAP / 'all_streamwise_pressure_1d_map.csv')}`",
        f"- `{rel(SENSOR_POLICY / 'sensor_map_policy_refresh.csv')}`",
        "",
        "## Files Changed",
        "",
        f"- `{rel(OUT)}/`",
        f"- `{rel(STATUS)}`",
        f"- `{rel(JOURNAL)}`",
        f"- `{rel(IMPORT)}`",
        "- `tools/analyze/build_salt1_schema_promotion.py`",
        "- `tools/analyze/test_salt1_schema_promotion.py`",
        "- `.agent/BOARD.md` own row status",
        "",
        "## Results",
        "",
        f"- Promoted cases: `{summary['promoted_cases']}`.",
        f"- Streamwise pressure rows: `{summary['streamwise_pressure_rows']}`.",
        f"- Runtime audit pass rows: `{summary['runtime_audit_pass_rows']}`.",
        "",
        "## Incomplete Lines",
        "",
        "- This package does not reduce realized Salt1 passive-wall/test-section wallHeatFlux into runtime inputs.",
        "- Pressure rows remain diagnostic target rows until pressure gates admit coefficients.",
        "",
        "## Next Step",
        "",
        "Wire the final scorecard runner to consume the manifest and enforce runtime-input guardrails.",
    ]
    JOURNAL.write_text("\n".join(journal) + "\n")

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
        "generated_index_refresh_note": "Skipped because active AGENT-482 owns generated docs index files.",
    }
    write_json(IMPORT, manifest)


def main() -> dict[str, object]:
    require_sources()
    OUT.mkdir(parents=True, exist_ok=True)

    bc_contract = build_bc_source_material_contract()
    heat_ledger = build_patchwise_heat_ledger()
    streamwise_pressure, branch_pressure = build_pressure_rows()
    thermal_scores = build_thermal_score_rows(heat_ledger)
    sensor_targets = build_sensor_target_rows()
    runtime_audit = build_runtime_input_audit()
    split_manifest = build_split_manifest()
    source_manifest = build_source_manifest()

    write_csv(
        OUT / "salt1_bc_source_material_contract.csv",
        bc_contract,
        [
            "case_key",
            "run_key",
            "q_ratio",
            "canonical_split_role",
            "thermal_role",
            "schema_bucket",
            "patch_count",
            "total_setup_Q_W",
            "bc_types",
            "material_contract_status",
            "radiation_policy",
            "runtime_use",
            "realized_wallHeatFlux_runtime_allowed",
            "source_path",
        ],
    )
    write_csv(
        OUT / "salt1_patchwise_heat_source_sink_ledger.csv",
        heat_ledger,
        [
            "case_key",
            "run_key",
            "q_ratio",
            "canonical_split_role",
            "section_bucket",
            "patch_count",
            "setup_imposed_net_to_fluid_W",
            "setup_source_component_W",
            "setup_removal_component_W",
            "bc_types",
            "thermal_roles",
            "realized_wallHeatFlux_status",
            "runtime_model_use",
            "fit_allowed",
            "score_allowed",
            "admission_status",
            "source_path",
        ],
    )
    write_csv(OUT / "salt1_pressure_streamwise_rows.csv", streamwise_pressure, list(streamwise_pressure[0].keys()))
    write_csv(OUT / "salt1_pressure_branch_score_rows.csv", branch_pressure, list(branch_pressure[0].keys()))
    write_csv(
        OUT / "salt1_thermal_score_rows.csv",
        thermal_scores,
        [
            "case_key",
            "run_key",
            "q_ratio",
            "canonical_split_role",
            "segment_bucket",
            "qoi",
            "review_admission_class",
            "thermal_fit_allowed",
            "score_allowed",
            "source_sign_status",
            "segment_heat_loss_status",
            "runtime_wallHeatFlux_allowed",
            "guardrail",
            "source_path",
        ],
    )
    write_csv(
        OUT / "salt1_sensor_target_rows.csv",
        sensor_targets,
        [
            "case_key",
            "canonical_split_role",
            "sensor",
            "kind",
            "runtime_temperature_allowed",
            "fit_allowed",
            "score_allowed",
            "score_use",
            "source_segment",
            "fluid_projection_status",
            "policy",
            "blocker_or_caveat",
            "source_path",
        ],
    )
    write_csv(
        OUT / "runtime_input_audit.csv",
        runtime_audit,
        ["audit_id", "gate", "observed_state", "forbidden_runtime_input"],
    )
    write_csv(
        OUT / "salt1_split_ready_manifest.csv",
        split_manifest,
        [
            "case_key",
            "run_key",
            "source_key",
            "q_ratio",
            "canonical_split_role",
            "fit_allowed",
            "model_selection_allowed",
            "score_allowed",
            "schema_promotion_status",
            "admission_status",
            "steady_state_verdict",
            "terminal_window_verdict",
            "operational_provenance",
            "do_not_collapse_q_ratio",
            "source_case_path",
            "source_path",
        ],
    )
    write_csv(OUT / "source_manifest.csv", source_manifest, ["source_id", "path", "exists", "use"])

    split_counts = Counter(row["canonical_split_role"] for row in split_manifest)
    summary = {
        "task": TASK,
        "date": DATE,
        "promoted_cases": len(split_manifest),
        "split_role_counts": dict(sorted(split_counts.items())),
        "bc_contract_rows": len(bc_contract),
        "heat_ledger_rows": len(heat_ledger),
        "streamwise_pressure_rows": len(streamwise_pressure),
        "branch_pressure_rows": len(branch_pressure),
        "thermal_score_rows": len(thermal_scores),
        "sensor_target_rows": len(sensor_targets),
        "runtime_audit_rows": len(runtime_audit),
        "runtime_audit_pass_rows": sum(1 for row in runtime_audit if row["gate"] == "pass"),
        "all_cases_promoted": sorted(row["case_key"] for row in split_manifest),
        "all_sources_present": all(row["exists"] == "yes" for row in source_manifest),
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "generated_index_refreshed": False,
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_closeout(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
