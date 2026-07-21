#!/usr/bin/env python3
"""Resolve Salt1 cooler/HX support for M2 score readiness."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-PREDICT-M2-SALT1-COOLER-HX-RESOLUTION-PACKAGE"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_m2_salt1_cooler_hx_resolution_package"
M2_RESOLVER = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_m2_scoring_gate_resolver"
M2_ARTIFACT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt1_4_m2_frozen_prediction_artifact"
SALT1_CLOSEOUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt1_4_m2_salt1_support_closeout"
FINAL_FREEZE = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt1_4_nominal_final_freeze"
COOLER_SCORECARD = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_predictive_boundary_submodel_admission/cooler_hx_scorecard.csv"
STATUS = ROOT / ".agent/status/2026-07-20_TODO-PREDICT-M2-SALT1-COOLER-HX-RESOLUTION-PACKAGE.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/predict-m2-salt1-cooler-hx-resolution-package.md"
IMPORT = ROOT / "imports/2026-07-20_m2_salt1_cooler_hx_resolution_package.json"
FROZEN_MODEL_ID = "M2_FROZEN_PREDICTION_ARTIFACT_SALT1_4_NOMINAL_2026_07_20"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for field in row:
                if field not in fieldnames:
                    fieldnames.append(field)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_sources() -> None:
    required = [
        M2_RESOLVER / "m2_score_ready_policy_decision.csv",
        M2_ARTIFACT / "candidate_model_freeze.json",
        SALT1_CLOSEOUT / "salt1_boundary_projection_candidate.csv",
        FINAL_FREEZE / "final_freeze_manifest.csv",
        COOLER_SCORECARD,
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing M2 Salt1 cooler/HX resolution sources: " + "; ".join(missing))


def salt1_supported_in_csv(path: Path) -> tuple[bool, str]:
    if not path.exists() or path.suffix.lower() != ".csv":
        return False, ""
    try:
        rows = read_csv(path)
    except (csv.Error, UnicodeDecodeError):
        return False, ""
    for row in rows:
        values = {str(value).lower() for value in row.values()}
        joined = " ".join(values)
        has_salt1 = "salt1" in joined or "salt_1" in joined
        has_cooler = "cooler" in joined or "hx" in joined or "qhx" in joined
        blocked = "missing" in joined or "blocked" in joined or "not_supported" in joined or "false" in values
        numeric_projection = False
        for key in ("predicted_qhx_W", "cooler_predicted_qhx_W", "candidate_value"):
            raw = row.get(key, "").strip()
            if raw:
                try:
                    float(raw)
                except ValueError:
                    pass
                else:
                    numeric_projection = True
        if has_salt1 and has_cooler and numeric_projection and not blocked:
            return True, joined[:240]
    return False, ""


def candidate_paths() -> list[Path]:
    seed_paths = [
        COOLER_SCORECARD,
        SALT1_CLOSEOUT / "salt1_boundary_projection_candidate.csv",
        FINAL_FREEZE / "final_freeze_manifest.csv",
    ]
    patterns = ("*salt1*cooler*.csv", "*cooler*salt1*.csv", "*salt1*hx*.csv", "*hx*salt1*.csv")
    discovered: list[Path] = []
    for pattern in patterns:
        discovered.extend((ROOT / "work_products/2026-07").glob(f"**/{pattern}"))
    paths = []
    for path in [*seed_paths, *sorted(discovered)]:
        if path not in paths:
            paths.append(path)
    return paths


def build_salt1_cooler_hx_source_audit() -> list[dict[str, Any]]:
    rows = []
    for path in candidate_paths():
        supported, evidence = salt1_supported_in_csv(path)
        rows.append(
            {
                "source_path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "candidate_role": "salt1_cooler_hx_support_search",
                "salt1_cooler_hx_supported": str(supported).lower(),
                "evidence": evidence if supported else "no_supported_salt1_cooler_hx_projection_found",
            }
        )
    return rows


def build_salt1_cooler_hx_projection_candidate(audit: list[dict[str, Any]]) -> list[dict[str, Any]]:
    supported = [row for row in audit if row["salt1_cooler_hx_supported"] == "true"]
    return [
        {
            "case_key": "salt1_nominal",
            "case_id": "salt_1",
            "term_id": "cooler_hx",
            "projection_status": "supported" if supported else "blocked_missing_supported_scorecard_row",
            "candidate_value": "",
            "source_path": supported[0]["source_path"] if supported else rel(COOLER_SCORECARD),
            "guardrail": "do_not_fabricate_salt1_cooler_hx_projection",
        }
    ]


def build_m2_score_ready_decision(projection: list[dict[str, Any]]) -> list[dict[str, Any]]:
    supported = projection[0]["projection_status"] == "supported"
    return [
        {
            "frozen_model_id": FROZEN_MODEL_ID,
            "decision": "score_ready_4row_supported" if supported else "blocked_missing_salt1_cooler_hx",
            "holdout_score_release": str(supported).lower(),
            "holdout_rows_scored_now": 0,
            "fit_rows_added": 0,
            "model_selection_rows_added": 0,
            "reason": "Salt1 cooler/HX support found" if supported else "No real Salt1 cooler/HX support found",
        }
    ]


def build_optional_3row_exception_memo() -> list[dict[str, Any]]:
    return [
        {
            "exception_id": "M2_CORE_3ROW_SUPPORTED_SCORE_READY",
            "status": "available_policy_option_not_granted",
            "would_release_holdout_scoring": "yes_after_explicit_approval",
            "current_decision": "not_granted",
            "guardrail": "Salt1 remains unsupported context; no fitting/model selection changes; no automatic blind scoring",
        }
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        (M2_RESOLVER / "m2_score_ready_policy_decision.csv", "prior score gate decision"),
        (M2_ARTIFACT / "candidate_model_freeze.json", "M2 artifact"),
        (SALT1_CLOSEOUT / "salt1_boundary_projection_candidate.csv", "Salt1 closeout"),
        (COOLER_SCORECARD, "cooler/HX scorecard"),
    ]
    return [{"source_path": rel(path), "exists": "yes" if path.exists() else "no", "source_role": role, "mutation": "read_only"} for path, role in sources]


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(f"# M2 Salt1 Cooler/HX Resolution Package\n\nDecision: {summary['decision']}. Holdout rows scored: {summary['holdout_rows_scored_now']}.\n", encoding="utf-8")


def write_status_files(summary: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(f"# {TASK}\n\n- status: complete\n- decision: {summary['decision']}\n- output: {rel(OUT)}\n", encoding="utf-8")
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(f"# {DATE} M2 Salt1 cooler/HX resolution\n\nAudited Salt1 cooler/HX support without scoring holdout rows.\n", encoding="utf-8")
    write_json(IMPORT, {"task": TASK, "date": DATE, "output_dir": rel(OUT), "native_solver_outputs_mutated": False, "summary_path": rel(OUT / "summary.json")})


def main() -> dict[str, Any]:
    require_sources()
    audit = build_salt1_cooler_hx_source_audit()
    projection = build_salt1_cooler_hx_projection_candidate(audit)
    decision = build_m2_score_ready_decision(projection)
    memo = build_optional_3row_exception_memo()
    sources = build_source_manifest()
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "decision": decision[0]["decision"],
        "salt1_cooler_hx_supported": projection[0]["projection_status"] == "supported",
        "optional_3row_exception_granted": False,
        "holdout_rows_scored_now": 0,
        "fit_rows_added": 0,
        "model_selection_rows_added": 0,
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
    }
    write_csv(OUT / "salt1_cooler_hx_source_audit.csv", audit)
    write_csv(OUT / "salt1_cooler_hx_projection_candidate.csv", projection)
    write_csv(OUT / "m2_score_ready_decision.csv", decision)
    write_csv(OUT / "optional_3row_exception_memo.csv", memo)
    write_csv(OUT / "source_manifest.csv", sources)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
