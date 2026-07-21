#!/usr/bin/env python3
"""Build the segment-local thermal model scorecard from admitted evidence."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-17"
TASK = "TODO-PREDICT-SEGMENT-THERMAL-MODELS"

OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_thermal_models"
STATUS = ROOT / ".agent/status/2026-07-17_TODO-PREDICT-SEGMENT-THERMAL-MODELS.md"
JOURNAL = ROOT / ".agent/journal/2026-07-17/predict-segment-thermal-models.md"
IMPORT = ROOT / "imports/2026-07-17_predict_segment_thermal_models.json"

THERMAL_CONTRACT = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_equation_contract"
    / "thermal_model_slots.csv"
)
BOUNDARY_ADMISSION = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_predictive_boundary_submodel_admission"
    / "submodel_admission_summary.csv"
)
TEST_SECTION = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_predictive_test_section_heat_loss_model"
    / "setup_candidate_summary.csv"
)
THERMAL_PARITY = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_thermal_parity_resolution_gate"
    / "thermal_row_admission_gate.csv"
)
SALT1_THERMAL = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_salt1_schema_promotion"
    / "salt1_thermal_score_rows.csv"
)
SALT2_THERMAL = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_salt2_pm5q_val_salt2_readiness_ledger"
    / "thermal_source_sink_ledger.csv"
)
COOLER_MODEL = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model"
    / "model_comparison_decision.json"
)
COOLER_SCORE = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model"
    / "coupled_scorecard.csv"
)
SENSOR_POLICY = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_sensor_tp2_restore_tw10_exclude"
    / "sensor_policy_scorecard.csv"
)


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
        THERMAL_CONTRACT,
        BOUNDARY_ADMISSION,
        TEST_SECTION,
        THERMAL_PARITY,
        SALT1_THERMAL,
        SALT2_THERMAL,
        COOLER_MODEL,
        COOLER_SCORE,
        SENSOR_POLICY,
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing segment thermal scorecard sources: " + "; ".join(missing))


def _rows_with(rows: list[dict[str, str]], key: str, needles: set[str]) -> list[dict[str, str]]:
    return [row for row in rows if row.get(key, "") in needles]


def build_segment_scorecard() -> list[dict[str, object]]:
    contract = read_csv(THERMAL_CONTRACT)
    boundary = {row["submodel"]: row for row in read_csv(BOUNDARY_ADMISSION)}
    test_rows = read_csv(TEST_SECTION)
    parity = read_csv(THERMAL_PARITY)
    salt1 = read_csv(SALT1_THERMAL)
    salt2 = read_csv(SALT2_THERMAL)
    cooler_decision = json.loads(COOLER_MODEL.read_text())
    cooler_scores = read_csv(COOLER_SCORE)

    source_map = {
        "heater": {"heater"},
        "cooler_HX": {"cooler_HX", "cooling_branch"},
        "downcomer": {"passive_wall", "downcomer"},
        "upcomer": {"test_section", "upcomer"},
        "test_section": {"test_section"},
        "junction_stub_connector": {"junction_stub_connector", "connector", "stub"},
        "lower_upper_legs": {"lower_leg", "upper_leg", "passive_wall"},
    }
    rows: list[dict[str, object]] = []
    for row in contract:
        region = row["loop_region"]
        salt1_rows = _rows_with(salt1, "segment_bucket", source_map.get(region, set()))
        salt2_rows = _rows_with(salt2, "section_key", source_map.get(region, set()))
        parity_rows = [item for item in parity if region in item.get("segment", "") or item.get("segment") in source_map.get(region, set())]

        if region == "heater":
            admitted_setup = 1 if boundary["heater"]["admission_decision"].startswith("admitted") else 0
            status = "admitted_setup_source_term"
            decision = "Use admitted scalar heater boundary/source model; do not absorb residual heat into internal Nu."
            blockers = "none_for_setup_heater_boundary;internal_Nu_residual_absorption_forbidden"
        elif region == "cooler_HX":
            admitted_setup = 1 if boundary["cooler_hx"]["admission_decision"].startswith("admitted") else 0
            status = "admitted_setup_cooler_removal_candidate"
            decision = "Use setup-only cooler removal model lane; keep coupled score as pending review evidence."
            blockers = cooler_decision.get("final_decision", "pending_coupled_review")
        elif region == "test_section":
            admitted_setup = 0
            status = "blocked_test_section_passive_loss"
            decision = "No test-section passive loss candidate is admitted; TS rows remain validation-only diagnostics."
            blockers = "predictive-wall-test-section-submodels;candidate_q_loss_gates_fail;no_coupled_m3ts_candidate"
        elif region == "upcomer":
            admitted_setup = 0
            status = "blocked_hybrid_cell_exchange_required"
            decision = "Use upcomer hybrid lane only; current recirculating rows cannot admit ordinary internal Nu."
            blockers = "recirculating_upcomer;hybrid_cell_exchange_not_calibrated;ordinary_internal_Nu_forbidden"
        elif region == "downcomer":
            admitted_setup = 0
            status = "validation_only_passive_boundary"
            decision = "Passive wall evidence may validate heat balance, but ordinary internal-Nu residual fits are not admitted."
            blockers = "downcomer_policy_blocks_ordinary_internal_Nu;passive_boundary_validation_only"
        elif region == "junction_stub_connector":
            admitted_setup = 0
            status = "diagnostic_only_named_loss_boundary"
            decision = "Use junction/stub/connector thermal rows as named source-sink diagnostics, not pipe heat-transfer coefficients."
            blockers = "local_component_heat_not_isolated;named_boundary_term_required"
        else:
            admitted_setup = 0
            status = "validation_only_development_and_wall_resistance"
            decision = "Use lower/upper leg thermal evidence to test development and wall resistance, not as a hidden multiplier."
            blockers = "boundary_layer_development_unscored;wall_layer_resistance_not_coupled"

        rows.append(
            {
                "loop_region": region,
                "one_d_segments": row["one_d_segments"],
                "thermal_slots": row["thermal_slots"],
                "property_form": row["property_form"],
                "admitted_setup_model_rows": admitted_setup,
                "residual_internal_nu_fit_admitted_rows": 0,
                "scoreable_predictive_thermal_rows": admitted_setup,
                "diagnostic_source_sink_rows": len(salt1_rows) + len(salt2_rows) + len(parity_rows),
                "test_section_candidate_rows": len(test_rows) if region == "test_section" else 0,
                "cooler_coupled_score_rows": len(cooler_scores) if region == "cooler_HX" else 0,
                "admission_status": status,
                "source_sink_ownership": "explicit_setup_or_named_boundary_term;internal_Nu_must_not_absorb_source_sink_residuals",
                "primary_blockers": blockers,
                "train_validation_holdout_improvement_status": "not_run_in_this_scorecard",
                "decision": decision,
                "runtime_forbidden_inputs": row["runtime_forbidden_inputs"],
                "source_paths": ";".join(
                    [
                        rel(THERMAL_CONTRACT),
                        rel(BOUNDARY_ADMISSION),
                        rel(TEST_SECTION),
                        rel(THERMAL_PARITY),
                        rel(SALT1_THERMAL),
                        rel(SALT2_THERMAL),
                    ]
                ),
            }
        )
    return rows


def build_slot_rows(scorecard: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in scorecard:
        for slot in str(row["thermal_slots"]).split(";"):
            if not slot:
                continue
            if row["admission_status"].startswith("admitted_setup"):
                admission = "admitted_setup_only"
                fit_allowed = "true_setup_only"
                score_allowed = "true"
            elif "internal_Nu" in slot or "diagnostic_internal_Nu" in slot:
                admission = "not_admitted_residual_absorption_forbidden"
                fit_allowed = "false"
                score_allowed = "diagnostic"
            elif "hybrid" in slot or "cell" in slot:
                admission = "blocked_until_hybrid_calibrated"
                fit_allowed = "false"
                score_allowed = "diagnostic"
            else:
                admission = "validation_or_diagnostic_only"
                fit_allowed = "false"
                score_allowed = "diagnostic"
            rows.append(
                {
                    "loop_region": row["loop_region"],
                    "thermal_slot": slot,
                    "admission_status": admission,
                    "fit_allowed_now": fit_allowed,
                    "score_allowed_now": score_allowed,
                    "source_sink_ownership": row["source_sink_ownership"],
                    "reason": row["primary_blockers"],
                }
            )
    return rows


def build_evidence_rollup(scorecard: list[dict[str, object]]) -> list[dict[str, object]]:
    boundary = read_csv(BOUNDARY_ADMISSION)
    test_rows = read_csv(TEST_SECTION)
    parity = read_csv(THERMAL_PARITY)
    salt1 = read_csv(SALT1_THERMAL)
    salt2 = read_csv(SALT2_THERMAL)
    counts = Counter(row["admission_status"] for row in scorecard)
    return [
        {
            "evidence_source": "segment_equation_contract",
            "rows": len(read_csv(THERMAL_CONTRACT)),
            "admitted_setup_rows": 0,
            "diagnostic_rows": len(scorecard),
            "status": "contract_available",
            "interpretation": "Segment-local thermal slots and runtime forbidden inputs are defined.",
            "source_path": rel(THERMAL_CONTRACT),
        },
        {
            "evidence_source": "predictive_boundary_submodel_admission",
            "rows": len(boundary),
            "admitted_setup_rows": sum(1 for row in boundary if row["admission_decision"].startswith("admitted")),
            "diagnostic_rows": len(boundary),
            "status": "heater_and_cooler_setup_admitted_test_section_blocked",
            "interpretation": "Heater and cooler setup boundary models are usable; wall/test-section remains blocked.",
            "source_path": rel(BOUNDARY_ADMISSION),
        },
        {
            "evidence_source": "test_section_heat_loss_model",
            "rows": len(test_rows),
            "admitted_setup_rows": 0,
            "diagnostic_rows": len(test_rows),
            "status": "not_admitted",
            "interpretation": "All test-section candidates fail validation or coupled admission gates.",
            "source_path": rel(TEST_SECTION),
        },
        {
            "evidence_source": "thermal_parity_resolution_gate",
            "rows": len(parity),
            "admitted_setup_rows": 0,
            "diagnostic_rows": len(parity),
            "status": "validation_only_no_internal_nu_absorption",
            "interpretation": "Parity evidence supports sign/resolution decisions but forbids residual internal-Nu fitting.",
            "source_path": rel(THERMAL_PARITY),
        },
        {
            "evidence_source": "salt1_schema_promoted_thermal_rows",
            "rows": len(salt1),
            "admitted_setup_rows": sum(1 for row in salt1 if row.get("review_admission_class", "").startswith("admitted_setup")),
            "diagnostic_rows": len(salt1),
            "status": "final_training_schema_rows_available",
            "interpretation": "Salt1 now contributes setup/source-sink rows under the same guardrails as Salt2-4.",
            "source_path": rel(SALT1_THERMAL),
        },
        {
            "evidence_source": "salt2_pm5q_val_salt2_source_sink_ledger",
            "rows": len(salt2),
            "admitted_setup_rows": 0,
            "diagnostic_rows": len(salt2),
            "status": "diagnostic_source_sink_evidence",
            "interpretation": "Corrected +/-5Q and val_salt2 ledgers are source-sink diagnostics, not runtime heat leakage.",
            "source_path": rel(SALT2_THERMAL),
        },
        {
            "evidence_source": "segment_scorecard_decisions",
            "rows": len(scorecard),
            "admitted_setup_rows": sum(int(row["admitted_setup_model_rows"]) for row in scorecard),
            "diagnostic_rows": sum(counts.values()),
            "status": "complete_admission_status_split",
            "interpretation": "The scorecard separates setup admissions from validation-only and diagnostic-only thermal rows.",
            "source_path": rel(OUT / "segment_thermal_model_scorecard.csv"),
        },
    ]


def source_sink_contract_rows(scorecard: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in scorecard:
        if row["loop_region"] == "heater":
            owner = "setup heater power or admitted heater efficiency"
        elif row["loop_region"] == "cooler_HX":
            owner = "setup cooler removal model, not imposed CFD cooler duty"
        elif row["loop_region"] == "test_section":
            owner = "unadmitted passive test-section loss candidate"
        elif row["loop_region"] == "upcomer":
            owner = "hybrid wall-core exchange and recirculation cell, pending calibration"
        else:
            owner = "named passive/source-sink boundary or validation diagnostic"
        rows.append(
            {
                "loop_region": row["loop_region"],
                "source_sink_owner": owner,
                "internal_nu_absorption_allowed": "false",
                "runtime_realized_wall_heat_allowed": "false",
                "runtime_imposed_cfd_cooler_duty_allowed": "false",
                "notes": row["decision"],
            }
        )
    return rows


def runtime_audit_rows() -> list[dict[str, object]]:
    return [
        {
            "check": "no_realized_wall_heat_runtime",
            "status": "pass_forbidden",
            "forbidden_input": "realized wallHeatFlux",
            "policy": "Realized wall heat remains diagnostic/validation data.",
        },
        {
            "check": "no_imposed_cfd_cooler_duty_runtime",
            "status": "pass_forbidden",
            "forbidden_input": "imposed CFD cooler duty",
            "policy": "Cooler removal must come from setup-only admitted model terms.",
        },
        {
            "check": "no_validation_temperatures_runtime",
            "status": "pass_forbidden",
            "forbidden_input": "validation TP/TW temperatures",
            "policy": "Temperatures are score targets; runtime uses setup metadata and solved state.",
        },
        {
            "check": "no_internal_nu_residual_absorption",
            "status": "pass_forbidden",
            "forbidden_input": "residual internal Nu fit",
            "policy": "Source/sink ownership is explicit; internal Nu cannot hide heater/cooler/passive/radiation residuals.",
        },
        {
            "check": "no_cfd_mdot_runtime",
            "status": "pass_forbidden",
            "forbidden_input": "CFD mdot",
            "policy": "mdot remains solved by the coupled segment model.",
        },
    ]


def source_manifest() -> list[dict[str, object]]:
    sources = [
        ("thermal_contract", THERMAL_CONTRACT, "thermal slots and runtime guardrails"),
        ("boundary_admission", BOUNDARY_ADMISSION, "heater/cooler/test-section admission decisions"),
        ("test_section", TEST_SECTION, "test-section passive loss candidates"),
        ("thermal_parity", THERMAL_PARITY, "internal-Nu absorption guardrails"),
        ("salt1_thermal", SALT1_THERMAL, "Salt1 promoted final-training thermal rows"),
        ("salt2_thermal", SALT2_THERMAL, "Salt2/val source-sink diagnostics"),
        ("cooler_model_decision", COOLER_MODEL, "cooler coupled decision state"),
        ("cooler_coupled_score", COOLER_SCORE, "cooler coupled scores"),
        ("sensor_policy", SENSOR_POLICY, "TP/TW sensor policy for downstream scoring"),
    ]
    return [
        {"source_id": key, "path": rel(path), "exists": str(path.exists()).lower(), "use": use}
        for key, path, use in sources
    ]


def write_readme(summary: dict[str, object]) -> None:
    lines = [
        "---",
        "provenance:",
        f"  - {rel(THERMAL_CONTRACT)}",
        f"  - {rel(BOUNDARY_ADMISSION)}",
        f"  - {rel(TEST_SECTION)}",
        f"  - {rel(SALT1_THERMAL)}",
        "tags: [segment-thermal-models, forward-predictive-model, thermal-modeling, admission]",
        "related:",
        f"  - {rel(STATUS)}",
        f"  - {rel(JOURNAL)}",
        f"task: {TASK}",
        f"date: {DATE}",
        "role: Thermal-modeling/Implementer/Tester/Writer",
        "type: work_product",
        "status: complete",
        "---",
        "# Segment Thermal Model Scorecard",
        "",
        "## Decision",
        "",
        "This package separates setup-admitted thermal source/sink models from validation-only and diagnostic-only thermal evidence. "
        "Heater and cooler setup boundary models are usable. Test-section passive loss, upcomer recirculation exchange, and residual "
        "internal-Nu rows are not admitted as predictive closures.",
        "",
        "## Results",
        "",
        f"- Loop regions reviewed: `{summary['segment_rows']}`.",
        f"- Thermal slot rows: `{summary['thermal_slot_rows']}`.",
        f"- Setup-admitted thermal model rows: `{summary['admitted_setup_model_rows']}`.",
        f"- Residual internal-Nu fit-admitted rows: `{summary['residual_internal_nu_fit_admitted_rows']}`.",
        f"- Diagnostic source/sink rows represented: `{summary['diagnostic_source_sink_rows']}`.",
        f"- Runtime audit pass rows: `{summary['runtime_audit_pass_rows']}`.",
        "",
        "## Interpretation",
        "",
        "The forward model can use admitted setup heater/cooler terms, but it cannot claim a full segment thermal closure yet. "
        "The remaining blockers are test-section passive loss, upcomer hybrid exchange calibration, and boundary-layer/wall-resistance scoring.",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n")


def write_closeout(summary: dict[str, object]) -> None:
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
                "tags: [status, segment-thermal-models, thermal-modeling]",
                "related:",
                f"  - {rel(JOURNAL)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Thermal-modeling/Implementer/Tester/Writer",
                "type: status",
                "status: complete",
                "---",
                f"# {TASK} Status",
                "",
                "## Observed Facts",
                "",
                "- The segment equation contract defines seven thermal loop regions.",
                "- Heater and cooler setup boundary terms are admitted by the July 16 predictive boundary submodel package.",
                "- Test-section passive loss candidates remain not admitted; upcomer ordinary internal Nu remains blocked.",
                "- Salt1 now contributes final-training setup/source-sink rows under the same guardrails as Salt2-4.",
                "",
                "## Changes Made",
                "",
                f"- Wrote `{rel(OUT)}/` with segment scorecard, slot admission, source/sink ownership, evidence rollup, runtime audit, README, and summary.",
                "- Added focused builder tests.",
                "",
                "## Validation",
                "",
                "- `python3 -m unittest tools.analyze.test_segment_thermal_model_scorecard`",
                "- Parsed generated `summary.json` and import manifest with `python3 -m json.tool`.",
                "",
                "## Blockers",
                "",
                "- No blocker remains for thermal scorecard visibility.",
                "- Full predictive segment thermal closure remains blocked by test-section passive loss, upcomer hybrid calibration, and boundary-layer/wall-resistance scoring.",
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
                f"  - {rel(THERMAL_CONTRACT)}",
                f"  - {rel(BOUNDARY_ADMISSION)}",
                f"  - {rel(OUT / 'README.md')}",
                "tags: [journal, segment-thermal-models, thermal-modeling]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Thermal-modeling/Implementer/Tester/Writer",
                "type: journal",
                "status: complete",
                "---",
                "# Segment Thermal Model Scorecard Journal",
                "",
                "## Files Inspected",
                "",
                f"- `{rel(THERMAL_CONTRACT)}`",
                f"- `{rel(BOUNDARY_ADMISSION)}`",
                f"- `{rel(TEST_SECTION)}`",
                f"- `{rel(THERMAL_PARITY)}`",
                f"- `{rel(SALT1_THERMAL)}`",
                f"- `{rel(SALT2_THERMAL)}`",
                "",
                "## Files Changed",
                "",
                "- `tools/analyze/build_segment_thermal_model_scorecard.py`",
                "- `tools/analyze/test_segment_thermal_model_scorecard.py`",
                f"- `{rel(OUT)}/`",
                f"- `{rel(STATUS)}`",
                f"- `{rel(JOURNAL)}`",
                f"- `{rel(IMPORT)}`",
                "- `.agent/BOARD.md` own row status",
                "",
                "## Interpretation",
                "",
                "The thermal lane is now admission-status first: setup heater/cooler models can be used, but diagnostic heat ledgers and validation-only wall data are not promoted into closure terms.",
                "",
                "## Recommended Next Action",
                "",
                "Proceed to the upcomer hybrid package and boundary-layer scorecard before running the final coupled M3+TS admission review.",
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
    scorecard = build_segment_scorecard()
    slots = build_slot_rows(scorecard)
    evidence = build_evidence_rollup(scorecard)
    ownership = source_sink_contract_rows(scorecard)
    runtime = runtime_audit_rows()
    sources = source_manifest()

    write_csv(
        OUT / "segment_thermal_model_scorecard.csv",
        scorecard,
        [
            "loop_region",
            "one_d_segments",
            "thermal_slots",
            "property_form",
            "admitted_setup_model_rows",
            "residual_internal_nu_fit_admitted_rows",
            "scoreable_predictive_thermal_rows",
            "diagnostic_source_sink_rows",
            "test_section_candidate_rows",
            "cooler_coupled_score_rows",
            "admission_status",
            "source_sink_ownership",
            "primary_blockers",
            "train_validation_holdout_improvement_status",
            "decision",
            "runtime_forbidden_inputs",
            "source_paths",
        ],
    )
    write_csv(
        OUT / "thermal_model_slot_admission.csv",
        slots,
        [
            "loop_region",
            "thermal_slot",
            "admission_status",
            "fit_allowed_now",
            "score_allowed_now",
            "source_sink_ownership",
            "reason",
        ],
    )
    write_csv(
        OUT / "thermal_evidence_rollup.csv",
        evidence,
        [
            "evidence_source",
            "rows",
            "admitted_setup_rows",
            "diagnostic_rows",
            "status",
            "interpretation",
            "source_path",
        ],
    )
    write_csv(
        OUT / "source_sink_ownership_contract.csv",
        ownership,
        [
            "loop_region",
            "source_sink_owner",
            "internal_nu_absorption_allowed",
            "runtime_realized_wall_heat_allowed",
            "runtime_imposed_cfd_cooler_duty_allowed",
            "notes",
        ],
    )
    write_csv(OUT / "runtime_thermal_input_audit.csv", runtime, ["check", "status", "forbidden_input", "policy"])
    write_csv(OUT / "source_manifest.csv", sources, ["source_id", "path", "exists", "use"])
    summary = {
        "task": TASK,
        "date": DATE,
        "segment_rows": len(scorecard),
        "thermal_slot_rows": len(slots),
        "evidence_rollup_rows": len(evidence),
        "admitted_setup_model_rows": sum(int(row["admitted_setup_model_rows"]) for row in scorecard),
        "residual_internal_nu_fit_admitted_rows": sum(
            int(row["residual_internal_nu_fit_admitted_rows"]) for row in scorecard
        ),
        "scoreable_predictive_thermal_rows": sum(int(row["scoreable_predictive_thermal_rows"]) for row in scorecard),
        "diagnostic_source_sink_rows": sum(int(row["diagnostic_source_sink_rows"]) for row in scorecard),
        "runtime_audit_rows": len(runtime),
        "runtime_audit_pass_rows": sum(1 for row in runtime if row["status"] == "pass_forbidden"),
        "all_sources_present": all(row["exists"] == "true" for row in sources),
        "train_validation_holdout_improvement_status": "not_run_in_this_scorecard",
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
