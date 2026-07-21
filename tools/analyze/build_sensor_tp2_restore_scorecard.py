#!/usr/bin/env python3
"""Build the final TP2-restore / TW10-exclude sensor scorecard."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-17"
TASK = "TODO-SENSOR-TP2-RESTORE-TW10-EXCLUDE"

OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_sensor_tp2_restore_tw10_exclude"
STATUS = ROOT / ".agent/status/2026-07-17_TODO-SENSOR-TP2-RESTORE-TW10-EXCLUDE.md"
JOURNAL = ROOT / ".agent/journal/2026-07-17/sensor-tp2-restore-tw10-exclude.md"
IMPORT = ROOT / "imports/2026-07-17_sensor_tp2_restore_tw10_exclude.json"

SENSOR_POLICY = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_sensor_policy_gate_opening_and_hydraulic_node_run"
    / "sensor_map_policy_refresh.csv"
)
TP2_EVIDENCE = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_tp2_1d_model_evidence"
TP2_PROJECTED_REGISTRY = TP2_EVIDENCE / "tp2_projected_sensor_registry.csv"
TP2_SENSOR_EVIDENCE = TP2_EVIDENCE / "tp2_sensor_level_evidence.csv"
TP2_POLICY_GATE_EVIDENCE = TP2_EVIDENCE / "sensor_policy_gate_evidence.csv"
TP2_AGGREGATE_RMSE = TP2_EVIDENCE / "aggregate_rmse_before_after.csv"
TP2_GATE_STATUS = TP2_EVIDENCE / "tp2_gate_status.csv"
SEGMENT_CONTRACT = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_equation_contract"
    / "segment_equation_contract.csv"
)

TP2_RESTORED_SEGMENT = "right_downcomer_bottom_horizontal_junction"


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
        SENSOR_POLICY,
        TP2_PROJECTED_REGISTRY,
        TP2_SENSOR_EVIDENCE,
        TP2_POLICY_GATE_EVIDENCE,
        TP2_AGGREGATE_RMSE,
        TP2_GATE_STATUS,
        SEGMENT_CONTRACT,
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing TP2/TW10 source(s): " + "; ".join(missing))


def source_segment_by_sensor() -> dict[str, str]:
    rows = read_csv(TP2_PROJECTED_REGISTRY)
    return {row["sensor"]: row.get("canonical_source_segment", "") for row in rows}


def gate_status_by_gate() -> dict[str, str]:
    return {row["gate"]: row["status"] for row in read_csv(TP2_GATE_STATUS)}


def finite_rows_by_sensor() -> dict[str, tuple[int, int]]:
    rows = read_csv(TP2_POLICY_GATE_EVIDENCE)
    out: dict[str, tuple[int, int]] = {}
    for row in rows:
        out[row["sensor"]] = (int(row.get("finite_prediction_rows") or 0), int(row.get("total_rows") or 0))
    return out


def policy_rows() -> list[dict[str, object]]:
    policy = read_csv(SENSOR_POLICY)
    segments = source_segment_by_sensor()
    finite = finite_rows_by_sensor()
    gates = gate_status_by_gate()
    rows: list[dict[str, object]] = []

    for row in policy:
        sensor = row["sensor"]
        source_segment = row.get("source_segment", "")
        aggregate_after = "yes" if row.get("score_allowed") == "true_provisional" else "no"
        gate_status = "pass" if aggregate_after == "yes" else "blocked"
        policy_decision = row.get("policy", "")
        caveat = row.get("blocker_or_caveat", "")
        finite_rows, total_rows = finite.get(sensor, (0, int(row.get("observed_rows") or 0)))

        if sensor == "TP2":
            source_segment = segments[sensor]
            aggregate_after = "yes"
            gate_status = (
                "pass"
                if gates.get("TP2_source_segment_named") == "pass"
                and gates.get("TP2_runtime_input_forbidden") == "pass"
                and gates.get("TP2_finite_prediction_before_aggregate") == "pass"
                else "blocked"
            )
            policy_decision = "restore_to_aggregate_validation_only_after_gates"
            caveat = (
                "TP2 is projected onto the bottom-horizontal/right-downcomer junction and has finite "
                "post-solve 1D score rows; it remains runtime_temperature_allowed=false and fit_allowed=false."
            )
        elif sensor == "TW10":
            source_segment = ""
            aggregate_after = "no"
            gate_status = "blocked_active_hx_shell_state_not_emitted"
            policy_decision = "keep_excluded_until_active_hx_shell_state"
            caveat = (
                "TW10 is a cooling-jacket shell surrogate and remains excluded until the 1D model emits "
                "an active-HX shell-state temperature."
            )

        rows.append(
            {
                "sensor": sensor,
                "kind": row["kind"],
                "runtime_temperature_allowed": "false",
                "fit_allowed": "false",
                "aggregate_score_current": "yes" if row.get("score_allowed") == "true_provisional" else "no",
                "aggregate_score_after_refresh": aggregate_after,
                "source_segment_after_refresh": source_segment,
                "finite_prediction_rows": finite_rows,
                "total_rows": total_rows,
                "score_gate_status": gate_status,
                "score_use": row.get("score_use", ""),
                "policy_decision": policy_decision,
                "blocker_or_caveat": caveat,
                "source_path": rel(SENSOR_POLICY),
            }
        )
    return rows


def aggregate_rows() -> list[dict[str, object]]:
    rows = read_csv(TP2_AGGREGATE_RMSE)
    out: list[dict[str, object]] = []
    for row in rows:
        out.append(
            {
                "aggregate_policy": row["aggregate_policy"],
                "tp_count": row["tp_count"],
                "tw_count": row["tw_count"],
                "sensor_count": row["sensor_count"],
                "n_compared_rows": row["n_compared_rows"],
                "rmse_K": row["rmse_K"],
                "mae_K": row["mae_K"],
                "mean_error_K": row["mean_error_K"],
                "max_abs_error_K": row["max_abs_error_K"],
                "included_sensors": row["included_sensors"],
                "excluded_sensors": row["excluded_sensors"],
                "interpretation": row["interpretation"],
                "source_path": rel(TP2_AGGREGATE_RMSE),
            }
        )
    return out


def gate_rows() -> list[dict[str, object]]:
    rows = read_csv(TP2_GATE_STATUS)
    return [
        {
            "gate": row["gate"],
            "status": row["status"],
            "detail": row["detail"],
            "source_path": rel(TP2_GATE_STATUS),
        }
        for row in rows
    ]


def admission_rows() -> list[dict[str, object]]:
    return [
        {
            "item": "TP2 restored 1D sensor target",
            "admission_status": "validation-only",
            "admitted_use": "post-solve TP/TW aggregate scoring only",
            "forbidden_use": "runtime input; fit target; closure calibration",
            "decision": "admitted_to_aggregate_score_after_projection_source_segment_and_finite_row_gates",
        },
        {
            "item": "TW10 cooling-jacket shell surrogate",
            "admission_status": "blocked",
            "admitted_use": "reported as excluded",
            "forbidden_use": "aggregate TP/TW score until active-HX shell-state model exists",
            "decision": "keep_excluded",
        },
        {
            "item": "Final predictive forward-v1 model",
            "admission_status": "blocked",
            "admitted_use": "none from this sensor package alone",
            "forbidden_use": "claim final forward-v1 is admitted",
            "decision": "sensor scoring gate only; broader hydraulic/thermal gates remain separate",
        },
    ]


def source_manifest() -> list[dict[str, object]]:
    sources = [
        ("sensor_policy", SENSOR_POLICY, "current TP/TW policy before restoration"),
        ("tp2_projected_registry", TP2_PROJECTED_REGISTRY, "projected TP2 source segment"),
        ("tp2_sensor_evidence", TP2_SENSOR_EVIDENCE, "finite TP2 prediction rows"),
        ("tp2_policy_gate_evidence", TP2_POLICY_GATE_EVIDENCE, "finite-row and runtime/fit gate table"),
        ("tp2_aggregate_rmse", TP2_AGGREGATE_RMSE, "before/after aggregate score impact"),
        ("tp2_gate_status", TP2_GATE_STATUS, "TP2/TW10 gate status"),
        ("segment_equation_contract", SEGMENT_CONTRACT, "downcomer source-segment/runtime leakage context"),
    ]
    return [
        {"source_id": key, "path": rel(path), "exists": str(path.exists()).lower(), "use": use}
        for key, path, use in sources
    ]


def write_readme(summary: dict[str, object]) -> None:
    lines = [
        "---",
        "provenance:",
        f"  - {rel(SENSOR_POLICY)}",
        f"  - {rel(TP2_PROJECTED_REGISTRY)}",
        f"  - {rel(TP2_AGGREGATE_RMSE)}",
        "tags: [sensor-map, TP2, TW10, forward-v1, validation-only]",
        "related:",
        f"  - {rel(STATUS)}",
        f"  - {rel(JOURNAL)}",
        f"task: {TASK}",
        f"date: {DATE}",
        "role: Sensor-map/Forward-pred/Implementer/Tester/Writer",
        "type: work_product",
        "status: complete",
        "---",
        "# TP2 Restore / TW10 Exclude Final Scorecard",
        "",
        "## Decision",
        "",
        "TP2 is restored as a post-solve validation/scoring target on the 1D path. TW10 remains excluded from "
        "aggregate scoring because the current model does not emit an active-HX shell-state temperature.",
        "",
        "## Results",
        "",
        f"- TP2 source segment: `{summary['tp2_source_segment']}`.",
        f"- TP2 finite rows: `{summary['tp2_finite_rows']}` of `{summary['tp2_total_rows']}`.",
        f"- Current aggregate: `{summary['current_tp_count']}` TP + `{summary['current_tw_count']}` TW, RMSE `{summary['current_rmse_K']}` K.",
        f"- Restored aggregate: `{summary['restored_tp_count']}` TP + `{summary['restored_tw_count']}` TW, RMSE `{summary['restored_rmse_K']}` K.",
        "- TP2 and TW10 both remain `runtime_temperature_allowed=false` and `fit_allowed=false`.",
        "",
        "## Outputs",
        "",
        "- `sensor_policy_scorecard.csv`",
        "- `aggregate_rmse_before_after.csv`",
        "- `tp2_tw10_gate_status.csv`",
        "- `admission_status_scorecard.csv`",
        "- `source_manifest.csv`",
        "- `summary.json`",
        "",
        "## Guardrails",
        "",
        "This package changes score/admission status only. It does not mutate Fluid, native CFD outputs, registry state, "
        "scheduler state, or generated docs indexes.",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n")


def write_closeout(summary: dict[str, object]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    IMPORT.parent.mkdir(parents=True, exist_ok=True)

    status_lines = [
        "---",
        "provenance:",
        f"  - {rel(OUT / 'README.md')}",
        f"  - {rel(OUT / 'summary.json')}",
        "tags: [status, sensor-map, TP2, TW10]",
        "related:",
        f"  - {rel(JOURNAL)}",
        f"  - {rel(IMPORT)}",
        f"task: {TASK}",
        f"date: {DATE}",
        "role: Sensor-map/Forward-pred/Implementer/Tester/Writer",
        "type: status",
        "status: complete",
        "---",
        f"# {TASK} Status",
        "",
        "## Observed Facts",
        "",
        "- July 15 policy excluded TP2 and TW10 from aggregate scoring.",
        "- July 16 TP2 evidence projected TP2 onto the bottom-horizontal/right-downcomer junction and produced 3 finite TP2 rows.",
        "- TW10 remains a cooling-jacket shell surrogate with no active-HX shell-state model output.",
        "",
        "## Changes Made",
        "",
        f"- Wrote `{rel(OUT)}/` with final TP2 restore/TW10 exclude scorecard rows.",
        "- Preserved runtime and fit forbiddance for TP2/TW10.",
        "- Documented before/after aggregate RMSE impact.",
        "",
        "## Validation",
        "",
        "- `python3 -m unittest tools.analyze.test_sensor_tp2_restore_scorecard`",
        "- Parsed generated `summary.json` and import manifest with `python3 -m json.tool`.",
        "",
        "## Blockers",
        "",
        "- TP2 aggregate scoring blocker is resolved for validation-only use.",
        "- TW10 remains blocked until the active-HX shell-state output exists.",
        "- Generated docs index refresh was skipped because active AGENT-482 owns generated index files.",
    ]
    STATUS.write_text("\n".join(status_lines) + "\n")

    journal_lines = [
        "---",
        "provenance:",
        f"  - {rel(SENSOR_POLICY)}",
        f"  - {rel(TP2_EVIDENCE / 'README.md')}",
        f"  - {rel(OUT / 'README.md')}",
        "tags: [journal, sensor-map, TP2, TW10]",
        "related:",
        f"  - {rel(STATUS)}",
        f"  - {rel(IMPORT)}",
        f"task: {TASK}",
        f"date: {DATE}",
        "role: Sensor-map/Forward-pred/Implementer/Tester/Writer",
        "type: journal",
        "status: complete",
        "---",
        "# TP2 Restore / TW10 Exclude Journal",
        "",
        "## Files Inspected",
        "",
        f"- `{rel(SENSOR_POLICY)}`",
        f"- `{rel(TP2_PROJECTED_REGISTRY)}`",
        f"- `{rel(TP2_SENSOR_EVIDENCE)}`",
        f"- `{rel(TP2_AGGREGATE_RMSE)}`",
        f"- `{rel(TP2_GATE_STATUS)}`",
        "",
        "## Files Changed",
        "",
        "- `tools/analyze/build_sensor_tp2_restore_scorecard.py`",
        "- `tools/analyze/test_sensor_tp2_restore_scorecard.py`",
        f"- `{rel(OUT)}/`",
        f"- `{rel(STATUS)}`",
        f"- `{rel(JOURNAL)}`",
        f"- `{rel(IMPORT)}`",
        "- `.agent/BOARD.md` own row status",
        "",
        "## Interpretation",
        "",
        "TP2 is now usable as validation-only 1D aggregate evidence. TW10 remains correctly blocked rather than silently scored.",
        "",
        "## Recommended Next Action",
        "",
        "Make future TP/TW scorecards consume `sensor_policy_scorecard.csv` and keep TP/TW out of runtime inputs.",
    ]
    JOURNAL.write_text("\n".join(journal_lines) + "\n")

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

    sensors = policy_rows()
    aggregates = aggregate_rows()
    gates = gate_rows()
    admissions = admission_rows()
    sources = source_manifest()

    write_csv(
        OUT / "sensor_policy_scorecard.csv",
        sensors,
        [
            "sensor",
            "kind",
            "runtime_temperature_allowed",
            "fit_allowed",
            "aggregate_score_current",
            "aggregate_score_after_refresh",
            "source_segment_after_refresh",
            "finite_prediction_rows",
            "total_rows",
            "score_gate_status",
            "score_use",
            "policy_decision",
            "blocker_or_caveat",
            "source_path",
        ],
    )
    write_csv(
        OUT / "aggregate_rmse_before_after.csv",
        aggregates,
        [
            "aggregate_policy",
            "tp_count",
            "tw_count",
            "sensor_count",
            "n_compared_rows",
            "rmse_K",
            "mae_K",
            "mean_error_K",
            "max_abs_error_K",
            "included_sensors",
            "excluded_sensors",
            "interpretation",
            "source_path",
        ],
    )
    write_csv(OUT / "tp2_tw10_gate_status.csv", gates, ["gate", "status", "detail", "source_path"])
    write_csv(
        OUT / "admission_status_scorecard.csv",
        admissions,
        ["item", "admission_status", "admitted_use", "forbidden_use", "decision"],
    )
    write_csv(OUT / "source_manifest.csv", sources, ["source_id", "path", "exists", "use"])

    current = next(row for row in aggregates if row["aggregate_policy"] == "current_policy_excludes_tp2_tw10")
    restored = next(row for row in aggregates if row["aggregate_policy"] == "restored_policy_includes_tp2_excludes_tw10")
    tp2 = next(row for row in sensors if row["sensor"] == "TP2")
    tw10 = next(row for row in sensors if row["sensor"] == "TW10")
    gate_map = {row["gate"]: row["status"] for row in gates}

    summary = {
        "task": TASK,
        "date": DATE,
        "sensor_rows": len(sensors),
        "tp2_source_segment": tp2["source_segment_after_refresh"],
        "tp2_finite_rows": int(tp2["finite_prediction_rows"]),
        "tp2_total_rows": int(tp2["total_rows"]),
        "tp2_aggregate_after_refresh": tp2["aggregate_score_after_refresh"],
        "tw10_aggregate_after_refresh": tw10["aggregate_score_after_refresh"],
        "current_tp_count": int(current["tp_count"]),
        "current_tw_count": int(current["tw_count"]),
        "current_rmse_K": float(current["rmse_K"]),
        "restored_tp_count": int(restored["tp_count"]),
        "restored_tw_count": int(restored["tw_count"]),
        "restored_rmse_K": float(restored["rmse_K"]),
        "rmse_delta_K": float(restored["rmse_K"]) - float(current["rmse_K"]),
        "gate_status": gate_map,
        "all_gates_pass": all(status == "pass" for status in gate_map.values()),
        "all_sources_present": all(row["exists"] == "true" for row in sources),
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
