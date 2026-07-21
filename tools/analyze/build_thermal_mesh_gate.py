#!/usr/bin/env python3
"""Refresh the Salt2 thermal/closure mesh gate after coarse thermal smoke.

This consumes existing repair-smoke and Closure-QOI GCI artifacts. It does not
run OpenFOAM, reconstruct fields, mutate native solver outputs, or admit
closure-fit targets. The purpose is to compare coarse/medium/fine availability
per QOI and classify each QOI without fabricating GCI for two-level or
non-monotone data.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.compute_gci import compute_gci  # noqa: E402
TASK_ID = "AGENT-309"
SOURCE_ID = "viscosity_screening_salt_test_2_jin_coarse_mesh"
CASE_ID = "salt_2"
DEFAULT_R21 = 1.5
DEFAULT_R32 = 1.5

DEFAULT_COARSE_CSV = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_salt2_coarse_thermal_repair_smoke"
    / "outputs/coarse/segment_htc_uaprime_viscosity_screening_salt_test_2_jin_coarse_mesh.csv"
)
DEFAULT_MEDIUM_CSV = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_trial"
    / "outputs/medium/segment_htc_uaprime_viscosity_screening_salt_test_2_jin_coarse_mesh.csv"
)
DEFAULT_FINE_CSV = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_salt2_fine_reconstructed_t_repair_plan_sbatch"
    / "repair_trial_output/outputs/fine/segment_htc_uaprime_viscosity_screening_salt_test_2_jin_coarse_mesh.csv"
)
DEFAULT_COARSE_SUMMARY = (
    ROOT / "work_products/2026-07/2026-07-13/2026-07-13_salt2_coarse_thermal_repair_smoke/summary.json"
)
DEFAULT_MEDIUM_SUMMARY = (
    ROOT / "work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_trial/summary.json"
)
DEFAULT_FINE_SUMMARY = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_salt2_fine_reconstructed_t_repair_plan_sbatch"
    / "repair_trial_output/summary.json"
)
DEFAULT_CLOSURE_GCI_DIR = (
    ROOT / "work_products/2026-07/2026-07-13/2026-07-13_salt2_closure_qoi_mesh_gci"
)
DEFAULT_OUTPUT = (
    ROOT / "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh"
)
DEFAULT_ENTHALPY_CSV = (
    ROOT
    / "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces"
    / "segment_enthalpy_residuals.csv"
)
DEFAULT_SIGN_REVIEW_CSV = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_thermal_sign_enthalpy_review"
    / "thermal_sign_enthalpy_review.csv"
)
DEFAULT_BOUNDARY_SEGMENT_CSV = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table"
    / "segment_reduction_inputs.csv"
)

STATUS_FIELDS = [
    "case_id",
    "source_id",
    "qoi_family",
    "lane",
    "qoi_id",
    "span",
    "segment",
    "method",
    "quantity",
    "units",
    "coarse_value",
    "medium_value",
    "fine_value",
    "coarse_available",
    "medium_available",
    "fine_available",
    "complete_triplet",
    "coarse_status",
    "medium_status",
    "fine_status",
    "convergence_verdict",
    "gci_status",
    "observed_order_p",
    "gci_fine_pct",
    "gci_coarse_pct",
    "asymptotic_range_ratio",
    "publication_ready",
    "classification",
    "fit_admissible",
    "thesis_evidence_use",
    "blockers",
    "recommended_next_action",
    "coarse_source_path",
    "medium_source_path",
    "fine_source_path",
    "decision_source_path",
    "gci_source_path",
]

EVIDENCE_FIELDS = [
    "case_id",
    "source_id",
    "category",
    "level",
    "status",
    "details",
    "source_path",
]

ADMISSION_FIELDS = [
    "case_id",
    "source_id",
    "segment",
    "qoi",
    "units",
    "admission_class",
    "fit_eligible",
    "validation_use",
    "blockers",
    "coarse_value",
    "medium_value",
    "fine_value",
    "wallHeatFlux_W",
    "enthalpy_change_W",
    "segment_duty_W",
    "residual_W",
    "residual_fraction",
    "max_interface_recirc_ratio",
    "wall_vs_enthalpy_direction",
    "sign_convention",
    "radiation_semantics",
    "nu_guardrail",
    "source_paths",
]

SIGN_FIELDS = [
    "quantity",
    "positive_direction",
    "fit_use",
    "guardrail",
    "source",
]

METRICS = [
    ("htc_wm2k", "HTC", "W/m2/K"),
    ("uaprime_wmk", "UA_prime", "W/m/K"),
    ("Nu", "Nu", "dimensionless"),
]

CLASSIFICATION_ORDER = [
    "publication-ready GCI",
    "diagnostic-only",
    "blocked-sign-review",
    "blocked-downcomer-policy",
    "blocked-missing-triplet",
    "non-monotone/oscillatory",
]


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_value(row.get(field)) for field in fields})


def format_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    return str(value)


def number(value: object | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def yes(value: object | None) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1"}


def load_segment_rows(path: Path) -> dict[str, dict[str, str]]:
    return {row.get("segment", ""): row for row in read_csv(path)}


def load_summary(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"exists": False}
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["exists"] = True
    return payload


def summary_gate_status(payload: dict[str, object], level: str) -> tuple[str, str]:
    if not payload.get("exists"):
        return "missing", "summary.json missing"
    sections = payload.get("section_temperature_sampling") or []
    segments = payload.get("segment_thermal_extraction") or []
    section_pass = any(
        isinstance(item, dict) and item.get("level") == level and item.get("gate_pass") is True
        for item in sections  # type: ignore[union-attr]
    )
    segment_pass = any(
        isinstance(item, dict) and item.get("level") == level and item.get("gate_pass") is True
        for item in segments  # type: ignore[union-attr]
    )
    decision = str(payload.get("decision", ""))
    if section_pass and segment_pass and ("smoke passed" in decision or "Repair smoke passed" in decision):
        return "passed_repair_smoke", decision
    return "failed_or_partial", decision


def gci_diagnostics(
    coarse_value: float | None,
    medium_value: float | None,
    fine_value: float | None,
    r21: float,
    r32: float,
) -> dict[str, object]:
    if coarse_value is None or medium_value is None or fine_value is None:
        return {
            "complete_triplet": False,
            "convergence_verdict": "",
            "observed_order_p": None,
            "gci_fine_pct": None,
            "gci_coarse_pct": None,
            "asymptotic_range_ratio": None,
            "gci_trustworthy": False,
        }
    result = compute_gci(coarse_value, medium_value, fine_value, r21, r32)
    trustworthy = result.get("gci_trustworthy") is True
    return {
        "complete_triplet": True,
        "convergence_verdict": result.get("verdict", ""),
        "observed_order_p": result.get("observed_order_p"),
        "gci_fine_pct": result.get("gci_fine_pct") if trustworthy else None,
        "gci_coarse_pct": result.get("gci_coarse_pct") if trustworthy else None,
        "asymptotic_range_ratio": result.get("asymptotic_range_ratio") if trustworthy else None,
        "gci_trustworthy": trustworthy,
    }


def thermal_decision(
    segment: str,
    quantity: str,
    coarse_row: dict[str, str] | None,
    medium_row: dict[str, str] | None,
    fine_row: dict[str, str] | None,
    diagnostics: dict[str, object],
) -> tuple[str, str, str, str, str, str]:
    blockers: list[str] = []
    rows = {"coarse": coarse_row, "medium": medium_row, "fine": fine_row}
    for level, row in rows.items():
        if row is None:
            blockers.append(f"missing_{level}_row")
            continue
        status = row.get("status", "")
        if status and status != "computed":
            blockers.append(f"{level}_status_{status}")
    if segment == "downcomer" or any(
        row is not None and row.get("status") == "thermally_blocked_segment_right_leg" for row in rows.values()
    ):
        blockers.append("blocked_downcomer_policy")
    if not diagnostics["complete_triplet"]:
        blockers.append("missing_or_nonfinite_coarse_medium_or_fine_value")
    if quantity == "Nu":
        for level, row in rows.items():
            if row is not None and not yes(row.get("nu_direct_admitted")):
                blockers.append(f"{level}_nu_direct_not_admitted")
    for level, row in rows.items():
        if row is not None and not yes(row.get("sign_consistent_heated_wall")):
            blockers.append(f"{level}_sign_review_required")

    verdict = str(diagnostics.get("convergence_verdict") or "")
    if "blocked_downcomer_policy" in blockers:
        return (
            "blocked-downcomer-policy",
            "not_computed_blocked_downcomer_policy",
            "no",
            "blocked",
            ";".join(dict.fromkeys(blockers)),
            "resolve right-leg/downcomer thermal policy before extracting or interpreting this segment",
        )
    if not diagnostics["complete_triplet"]:
        return (
            "blocked-missing-triplet",
            "not_computed_missing_triplet",
            "no",
            "blocked",
            ";".join(dict.fromkeys(blockers)),
            "repair missing/nonfinite thermal metric before mesh comparison",
        )
    if any("sign_review_required" in blocker for blocker in blockers):
        return (
            "blocked-sign-review",
            "not_publication_gci_sign_review_required",
            "no",
            "diagnostic_triplet_only",
            ";".join(dict.fromkeys(blockers)),
            "review wallHeatFlux/enthalpy/UA sign convention before closure use",
        )
    if verdict != "monotonic_convergence":
        return (
            "non-monotone/oscillatory",
            "not_computed_non_monotone_or_divergent",
            "no",
            "diagnostic_triplet_only",
            ";".join(dict.fromkeys(blockers + [f"convergence_verdict_{verdict}"])),
            "do not compute publication GCI for non-monotone or divergent triplet",
        )
    if diagnostics["gci_trustworthy"] is True:
        return (
            "publication-ready GCI",
            "computed_publication_ready",
            "yes",
            "publication_mesh_gci",
            "",
            "eligible for closure-review use after admission owner confirms source-row policy",
        )
    return (
        "diagnostic-only",
        "computed_but_not_publication_ready",
        "no",
        "diagnostic_triplet_only",
        ";".join(dict.fromkeys(blockers + ["asymptotic_range_or_order_gate_failed"])),
        "treat as mesh-sensitivity diagnostic only",
    )


def build_thermal_rows(
    coarse_csv: Path,
    medium_csv: Path,
    fine_csv: Path,
    r21: float,
    r32: float,
) -> list[dict[str, object]]:
    coarse_rows = load_segment_rows(coarse_csv)
    medium_rows = load_segment_rows(medium_csv)
    fine_rows = load_segment_rows(fine_csv)
    segments = sorted(set(coarse_rows) | set(medium_rows) | set(fine_rows))
    rows: list[dict[str, object]] = []
    for segment in segments:
        coarse_row = coarse_rows.get(segment)
        medium_row = medium_rows.get(segment)
        fine_row = fine_rows.get(segment)
        any_computed = any(row is not None and row.get("status") == "computed" for row in (coarse_row, medium_row, fine_row))
        metric_specs = METRICS if any_computed else [("thermal_segment_closure", "thermal_segment_closure", "mixed")]
        for column, quantity, units in metric_specs:
            coarse_value = number(None if coarse_row is None else coarse_row.get(column))
            medium_value = number(None if medium_row is None else medium_row.get(column))
            fine_value = number(None if fine_row is None else fine_row.get(column))
            diagnostics = gci_diagnostics(coarse_value, medium_value, fine_value, r21, r32)
            classification, gci_status, fit_ok, evidence_use, blockers, next_action = thermal_decision(
                segment, quantity, coarse_row, medium_row, fine_row, diagnostics
            )
            publish_gci = classification == "publication-ready GCI"
            rows.append(
                {
                    "case_id": CASE_ID,
                    "source_id": SOURCE_ID,
                    "qoi_family": "thermal",
                    "lane": "thermal_segment_closure",
                    "qoi_id": f"thermal_segment_closure::{segment}::{quantity}",
                    "span": segment,
                    "segment": segment,
                    "method": "segment_htc_uaprime_repair_smoke_triplet",
                    "quantity": quantity,
                    "units": units,
                    "coarse_value": coarse_value,
                    "medium_value": medium_value,
                    "fine_value": fine_value,
                    "coarse_available": coarse_value is not None,
                    "medium_available": medium_value is not None,
                    "fine_available": fine_value is not None,
                    "complete_triplet": diagnostics["complete_triplet"],
                    "coarse_status": "" if coarse_row is None else coarse_row.get("status", ""),
                    "medium_status": "" if medium_row is None else medium_row.get("status", ""),
                    "fine_status": "" if fine_row is None else fine_row.get("status", ""),
                    "convergence_verdict": diagnostics["convergence_verdict"],
                    "gci_status": gci_status,
                    "observed_order_p": diagnostics["observed_order_p"] if publish_gci else None,
                    "gci_fine_pct": diagnostics["gci_fine_pct"] if publish_gci else None,
                    "gci_coarse_pct": diagnostics["gci_coarse_pct"] if publish_gci else None,
                    "asymptotic_range_ratio": diagnostics["asymptotic_range_ratio"] if publish_gci else None,
                    "publication_ready": "yes" if classification == "publication-ready GCI" else "no",
                    "classification": classification,
                    "fit_admissible": fit_ok,
                    "thesis_evidence_use": evidence_use,
                    "blockers": blockers,
                    "recommended_next_action": next_action,
                    "coarse_source_path": rel(coarse_csv),
                    "medium_source_path": rel(medium_csv),
                    "fine_source_path": rel(fine_csv),
                    "decision_source_path": "",
                    "gci_source_path": "",
                }
            )
    return rows


def classify_prior_closure(decision: dict[str, str], triplet: dict[str, str]) -> tuple[str, str, str]:
    if decision.get("publication_ready") == "yes":
        return "publication-ready GCI", "computed_publication_ready", "publication_mesh_gci"
    if decision.get("numeric_triplet_complete") != "yes":
        return "blocked-missing-triplet", "not_computed_missing_triplet", "blocked"
    verdict = decision.get("gci_verdict", "")
    if verdict and verdict != "monotonic_convergence":
        return "non-monotone/oscillatory", "not_computed_non_monotone_or_divergent", "diagnostic_triplet_only"
    if decision.get("admission_decision") == "diagnostic_not_publication_gci":
        return "diagnostic-only", "not_publication_gci_diagnostic_source_gate", "diagnostic_triplet_only"
    if triplet.get("source_gate") == "diagnostic_or_not_fit_safe":
        return "diagnostic-only", "not_publication_gci_diagnostic_source_gate", "diagnostic_triplet_only"
    return "diagnostic-only", "not_publication_gci_prior_gate_failed", "diagnostic_triplet_only"


def build_prior_closure_rows(closure_gci_dir: Path) -> list[dict[str, object]]:
    decisions_path = closure_gci_dir / "closure_qoi_admission_decisions.csv"
    triplets_path = closure_gci_dir / "closure_qoi_triplets.csv"
    gci_path = closure_gci_dir / "closure_qoi_gci_results.csv"
    triplets = {row["qoi_id"]: row for row in read_csv(triplets_path)}
    gci_rows = {row["qoi_id"]: row for row in read_csv(gci_path)} if gci_path.exists() else {}
    rows: list[dict[str, object]] = []
    for decision in read_csv(decisions_path):
        if decision.get("lane") == "thermal_segment_closure":
            continue
        qoi_id = decision["qoi_id"]
        triplet = triplets.get(qoi_id, {})
        gci = gci_rows.get(qoi_id, {})
        classification, gci_status, evidence_use = classify_prior_closure(decision, triplet)
        rows.append(
            {
                "case_id": decision.get("case_id", CASE_ID),
                "source_id": SOURCE_ID,
                "qoi_family": "closure",
                "lane": decision.get("lane", ""),
                "qoi_id": qoi_id,
                "span": decision.get("span", ""),
                "segment": decision.get("span", ""),
                "method": decision.get("method", ""),
                "quantity": decision.get("quantity", ""),
                "units": triplet.get("units", ""),
                "coarse_value": number(triplet.get("coarse_value")),
                "medium_value": number(triplet.get("medium_value")),
                "fine_value": number(triplet.get("fine_value")),
                "coarse_available": number(triplet.get("coarse_value")) is not None,
                "medium_available": number(triplet.get("medium_value")) is not None,
                "fine_available": number(triplet.get("fine_value")) is not None,
                "complete_triplet": decision.get("numeric_triplet_complete") == "yes",
                "coarse_status": triplet.get("coarse_admission_status", ""),
                "medium_status": triplet.get("medium_admission_status", ""),
                "fine_status": triplet.get("fine_admission_status", ""),
                "convergence_verdict": decision.get("gci_verdict", ""),
                "gci_status": gci_status,
                "observed_order_p": number(gci.get("observed_order_p")) if classification == "publication-ready GCI" else None,
                "gci_fine_pct": number(gci.get("gci_fine_pct")) if classification == "publication-ready GCI" else None,
                "gci_coarse_pct": number(gci.get("gci_coarse_pct")) if classification == "publication-ready GCI" else None,
                "asymptotic_range_ratio": number(gci.get("asymptotic_range_ratio"))
                if classification == "publication-ready GCI"
                else None,
                "publication_ready": decision.get("publication_ready", "no"),
                "classification": classification,
                "fit_admissible": "no",
                "thesis_evidence_use": evidence_use,
                "blockers": decision.get("blocker", ""),
                "recommended_next_action": decision.get("recommended_use", ""),
                "coarse_source_path": triplet.get("coarse_source_path", ""),
                "medium_source_path": triplet.get("medium_source_path", ""),
                "fine_source_path": triplet.get("fine_source_path", ""),
                "decision_source_path": rel(decisions_path),
                "gci_source_path": rel(gci_path) if qoi_id in gci_rows else "",
            }
        )
    return rows


def build_evidence_rows(
    coarse_summary: dict[str, object],
    medium_summary: dict[str, object],
    fine_summary: dict[str, object],
    coarse_summary_path: Path,
    medium_summary_path: Path,
    fine_summary_path: Path,
    closure_gci_dir: Path,
) -> list[dict[str, object]]:
    evidence: list[dict[str, object]] = []
    for level, payload, path in [
        ("coarse", coarse_summary, coarse_summary_path),
        ("medium", medium_summary, medium_summary_path),
        ("fine", fine_summary, fine_summary_path),
    ]:
        status, details = summary_gate_status(payload, level)
        evidence.append(
            {
                "case_id": CASE_ID,
                "source_id": SOURCE_ID,
                "category": "thermal_reconstructed_t_repair_smoke",
                "level": level,
                "status": status,
                "details": details,
                "source_path": rel(path),
            }
        )
    evidence.append(
        {
            "case_id": CASE_ID,
            "source_id": SOURCE_ID,
            "category": "prior_closure_qoi_mesh_gci",
            "level": "coarse_medium_fine",
            "status": "consumed_for_nonthermal_closure_rows",
            "details": "Prior closure GCI decisions are carried forward; prior thermal rows are replaced by this coarse/medium/fine thermal refresh.",
            "source_path": rel(closure_gci_dir / "closure_qoi_admission_decisions.csv"),
        }
    )
    return evidence


def rows_by_field(path: Path, field: str) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    return {row.get(field, ""): row for row in read_csv(path) if row.get("source_id") in {"", SOURCE_ID}}


def sign_convention_rows() -> list[dict[str, object]]:
    return [
        {
            "quantity": "wallHeatFlux_W / realized_wallHeatFlux_W",
            "positive_direction": "heat enters the fluid",
            "fit_use": "diagnostic energy input/output only",
            "guardrail": "total OpenFOAM wallHeatFlux already folds in rcExternalTemperature radiation where that BC is used; no separate exported qr term exists",
            "source": rel(DEFAULT_BOUNDARY_SEGMENT_CSV),
        },
        {
            "quantity": "enthalpy_change_W",
            "positive_direction": "bulk fluid enthalpy increases from the declared inlet interface to outlet interface",
            "fit_use": "validation-only heat-balance check",
            "guardrail": "do not convert wallHeatFlux-minus-enthalpy residual into internal Nu",
            "source": rel(DEFAULT_ENTHALPY_CSV),
        },
        {
            "quantity": "segment_duty_W",
            "positive_direction": "same physical orientation as total segment wallHeatFlux: positive heats fluid, negative cools fluid",
            "fit_use": "diagnostic segment energy ledger only",
            "guardrail": "q_sign labels in repaired segment extraction conflict on lower_leg/upcomer and require audit before admission",
            "source": rel(DEFAULT_SIGN_REVIEW_CSV),
        },
        {
            "quantity": "HTC / UA_prime / Nu",
            "positive_direction": "positive magnitude of an effective internal transfer diagnostic, not a heat-source direction",
            "fit_use": "not fit-admissible in this package",
            "guardrail": "internal Nu must not absorb heater, cooler, passive wall loss, wall storage, junction, recirculation, or radiation residuals",
            "source": "thermal_admission_table.csv",
        },
    ]


def blocker_list(*parts: object) -> str:
    blockers: list[str] = []
    for part in parts:
        if part is None:
            continue
        for item in str(part).replace(",", ";").split(";"):
            item = item.strip()
            if item and item not in blockers:
                blockers.append(item)
    return ";".join(blockers)


def admission_class_for(
    segment: str,
    qoi: str,
    complete_triplet: bool,
    thermal_classification: str = "",
) -> tuple[str, str, str]:
    if segment == "downcomer":
        return "blocked", "no", "no"
    if qoi == "Nu" and not complete_triplet:
        return "blocked", "no", "no"
    if thermal_classification == "publication-ready GCI":
        return "fit_admissible", "yes", "yes"
    return "validation_only", "no", "yes_diagnostic_only"


def segment_quality_blockers(segment: str, enthalpy_row: dict[str, str], sign_row: dict[str, str]) -> str:
    residual_fraction = number(enthalpy_row.get("residual_fraction"))
    recirc = number(enthalpy_row.get("max_interface_recirc_ratio"))
    blockers: list[str] = []
    if segment == "downcomer":
        blockers.append("blocked_downcomer_policy")
    if sign_row.get("repaired_q_sign_conflict") == "yes":
        blockers.append("repaired_q_sign_label_conflict")
    if sign_row.get("wall_vs_enthalpy_direction") == "opposed_direction":
        blockers.append("wallHeatFlux_enthalpy_opposed_direction")
    if residual_fraction is not None and abs(residual_fraction) > 0.25:
        blockers.append("large_wallHeatFlux_enthalpy_residual")
    if recirc is not None and recirc > 0.5:
        blockers.append("high_recirculation_interface")
    flags = enthalpy_row.get("quality_flags", "")
    if flags:
        blockers.append(flags)
    return blocker_list(*blockers)


def build_admission_rows(
    thermal_rows: list[dict[str, object]],
    enthalpy_csv: Path,
    sign_review_csv: Path,
) -> list[dict[str, object]]:
    enthalpy_by_segment = rows_by_field(enthalpy_csv, "physical_segment")
    sign_by_segment = rows_by_field(sign_review_csv, "segment")
    thermal_by_segment = {
        str(row["segment"]): [candidate for candidate in thermal_rows if candidate["segment"] == row["segment"]]
        for row in thermal_rows
    }
    segments = ["lower_leg", "upcomer", "downcomer"]
    radiation_semantics = (
        "CFD rcExternalTemperature wallHeatFlux includes radiation when that BC is used; "
        "no separate exported qr term exists, so do not add or fit radiation as an internal-Nu residual."
    )
    sign_convention = "positive wallHeatFlux/segment duty heats fluid; positive enthalpy_change increases fluid bulk enthalpy."
    nu_guardrail = "Nu/HTC/UA are internal-transfer diagnostics only and cannot absorb heater/cooler/passive-loss/wall-storage/radiation residuals."
    rows: list[dict[str, object]] = []
    for segment in segments:
        enthalpy = enthalpy_by_segment.get(segment, {})
        sign = sign_by_segment.get(segment, {})
        quality_blockers = segment_quality_blockers(segment, enthalpy, sign)
        wall_flux = number(enthalpy.get("segment_wallHeatFlux_sum_W"))
        enthalpy_change = number(enthalpy.get("enthalpy_change_W"))
        residual = number(enthalpy.get("wallHeatFlux_vs_enthalpy_residual_W"))
        residual_fraction = number(enthalpy.get("residual_fraction"))
        recirc = number(enthalpy.get("max_interface_recirc_ratio"))
        segment_duty = number(sign.get("coarse_segment_wallHeatFlux_sum_W")) or wall_flux
        for qoi, units, value in [
            ("wallHeatFlux", "W", wall_flux),
            ("enthalpy_change", "W", enthalpy_change),
            ("segment_duty", "W", segment_duty),
        ]:
            admission_class, fit_eligible, validation_use = admission_class_for(segment, qoi, value is not None)
            rows.append(
                {
                    "case_id": CASE_ID,
                    "source_id": SOURCE_ID,
                    "segment": segment,
                    "qoi": qoi,
                    "units": units,
                    "admission_class": admission_class,
                    "fit_eligible": fit_eligible,
                    "validation_use": validation_use,
                    "blockers": quality_blockers,
                    "coarse_value": value,
                    "medium_value": "",
                    "fine_value": "",
                    "wallHeatFlux_W": wall_flux,
                    "enthalpy_change_W": enthalpy_change,
                    "segment_duty_W": segment_duty,
                    "residual_W": residual,
                    "residual_fraction": residual_fraction,
                    "max_interface_recirc_ratio": recirc,
                    "wall_vs_enthalpy_direction": sign.get("wall_vs_enthalpy_direction", ""),
                    "sign_convention": sign_convention,
                    "radiation_semantics": radiation_semantics,
                    "nu_guardrail": nu_guardrail,
                    "source_paths": blocker_list(rel(enthalpy_csv), rel(sign_review_csv)),
                }
            )
        for thermal in sorted(thermal_by_segment.get(segment, []), key=lambda row: str(row["quantity"])):
            qoi = str(thermal["quantity"])
            complete_triplet = thermal.get("complete_triplet") is True
            admission_class, fit_eligible, validation_use = admission_class_for(
                segment,
                qoi,
                complete_triplet,
                str(thermal.get("classification", "")),
            )
            blockers = blocker_list(thermal.get("blockers", ""), quality_blockers, "internal_Nu_residual_absorption_forbidden")
            rows.append(
                {
                    "case_id": CASE_ID,
                    "source_id": SOURCE_ID,
                    "segment": segment,
                    "qoi": qoi,
                    "units": thermal.get("units", ""),
                    "admission_class": admission_class,
                    "fit_eligible": fit_eligible,
                    "validation_use": validation_use,
                    "blockers": blockers,
                    "coarse_value": thermal.get("coarse_value"),
                    "medium_value": thermal.get("medium_value"),
                    "fine_value": thermal.get("fine_value"),
                    "wallHeatFlux_W": wall_flux,
                    "enthalpy_change_W": enthalpy_change,
                    "segment_duty_W": segment_duty,
                    "residual_W": residual,
                    "residual_fraction": residual_fraction,
                    "max_interface_recirc_ratio": recirc,
                    "wall_vs_enthalpy_direction": sign.get("wall_vs_enthalpy_direction", ""),
                    "sign_convention": sign_convention,
                    "radiation_semantics": radiation_semantics,
                    "nu_guardrail": nu_guardrail,
                    "source_paths": blocker_list(
                        str(thermal.get("coarse_source_path", "")),
                        str(thermal.get("medium_source_path", "")),
                        str(thermal.get("fine_source_path", "")),
                        rel(enthalpy_csv),
                        rel(sign_review_csv),
                    ),
                }
            )
    return rows


def make_admission_memo(summary: dict[str, object], admission_rows: list[dict[str, object]]) -> str:
    counts = Counter(str(row["admission_class"]) for row in admission_rows)
    segment_lines: list[str] = []
    for segment in ["lower_leg", "upcomer", "downcomer"]:
        rows = [row for row in admission_rows if row["segment"] == segment]
        fit = sum(1 for row in rows if row["fit_eligible"] == "yes")
        validation = sum(1 for row in rows if row["admission_class"] == "validation_only")
        blocked = sum(1 for row in rows if row["admission_class"] == "blocked")
        segment_lines.append(f"- `{segment}`: fit `{fit}`, validation-only `{validation}`, blocked `{blocked}`.")
    return f"""# Thermal Admission Memo

Task: `{TASK_ID}`

Generated: `{summary['generated_at']}`

## Decision

No lower-leg, upcomer, or downcomer thermal UA/HTC/Nu row is fit-admissible.
Finite repaired values are validation-only diagnostics unless the table marks
the QOI blocked. The admission table is `thermal_admission_table.csv`.

## Segment Rollup

{chr(10).join(segment_lines)}

Admission counts:

```json
{json.dumps(dict(sorted(counts.items())), indent=2)}
```

## Sign Convention

- Positive `wallHeatFlux` / segment duty means heat enters the fluid.
- Positive `enthalpy_change_W` means bulk fluid enthalpy increases between the
  declared physical segment interfaces.
- `HTC`, `UA_prime`, and `Nu` are positive effective internal-transfer
  diagnostics, not heat-source directions.

## Radiation Semantics

Current CFD `rcExternalTemperature` includes radiation through emissivity and
`Tsur`, and current outputs do not export a separate `qr` term. Treat
`wallHeatFlux` as the total boundary heat flux. Do not add a separate radiation
term on top of CFD `wallHeatFlux`, and do not hide radiation or external-loss
residuals inside internal `Nu`.

## Guardrail

Internal `Nu` must not absorb heater, cooler, passive ambient loss, junction,
wall storage, or radiation residuals. The next admissible step is a heat-balance
and sign-policy review, not thermal fitting.
"""


def make_readme(summary: dict[str, object]) -> str:
    return f"""# Thermal / Closure Mesh Gate Refresh

Task: `{TASK_ID}`

Generated: `{summary['generated_at']}`

## Purpose

This package refreshes the mesh gate after the Salt2 coarse thermal repair smoke
landed. It keeps repair-smoke evidence separate from closure admission, carries
forward prior nonthermal closure-QOI decisions, and rebuilds the thermal segment
rows with coarse/medium/fine availability.

## Result

- Unified QOI rows: `{summary['unified_qoi_row_count']}`
- Thermal QOI rows: `{summary['thermal_qoi_row_count']}`
- Closure/nonthermal QOI rows carried forward: `{summary['closure_qoi_row_count']}`
- Publication-ready GCI rows: `{summary['publication_ready_count']}`
- Fit-admissible thermal rows: `{summary['fit_admissible_thermal_count']}`
- Main status: `{summary['main_status']}`

Classification counts:

```json
{json.dumps(summary['classification_counts'], indent=2)}
```

## Outputs

- `refreshed_qoi_mesh_gate_status.csv`: unified thermal plus closure QOI table
  with coarse/medium/fine availability, classification, blockers, and exact
  source paths.
- `thermal_mesh_gate_qois.csv`: refreshed thermal-only rows from coarse,
  medium, and fine repair-smoke CSVs.
- `thermal_mesh_gate_evidence.csv`: source package evidence.
- `blocked_or_diagnostic_qois.csv`: every non-publication-ready row.
- `thermal_admission_table.csv`: explicit fit/validation/blocked decision for
  lower-leg, upcomer, and downcomer wallHeatFlux, enthalpy, segment duty,
  HTC, UA', and Nu rows.
- `sign_convention_table.csv`: sign and residual guardrails used by the memo.
- `thermal_admission_memo.md`: human-readable admission decision.
- `summary.json`: machine-readable counts and source paths.

## Interpretation Boundary

No thermal or closure row in this refresh is publication-ready. Repaired
thermal rows are diagnostic until sign/enthalpy review, heat-balance review, and
downcomer policy gates admit them. GCI values are left blank for two-level,
blocked, oscillatory, or divergent rows.
"""


def build_package(
    coarse_csv: Path,
    medium_csv: Path,
    fine_csv: Path,
    coarse_summary_path: Path,
    medium_summary_path: Path,
    fine_summary_path: Path,
    closure_gci_dir: Path,
    output_dir: Path,
    enthalpy_csv: Path = DEFAULT_ENTHALPY_CSV,
    sign_review_csv: Path = DEFAULT_SIGN_REVIEW_CSV,
    r21: float = DEFAULT_R21,
    r32: float = DEFAULT_R32,
) -> dict[str, object]:
    thermal_rows = build_thermal_rows(coarse_csv, medium_csv, fine_csv, r21, r32)
    closure_rows = build_prior_closure_rows(closure_gci_dir)
    all_rows = closure_rows + thermal_rows
    admission_rows = build_admission_rows(thermal_rows, enthalpy_csv, sign_review_csv)
    sign_rows = sign_convention_rows()

    coarse_summary = load_summary(coarse_summary_path)
    medium_summary = load_summary(medium_summary_path)
    fine_summary = load_summary(fine_summary_path)
    evidence_rows = build_evidence_rows(
        coarse_summary,
        medium_summary,
        fine_summary,
        coarse_summary_path,
        medium_summary_path,
        fine_summary_path,
        closure_gci_dir,
    )
    blocked_or_diagnostic = [row for row in all_rows if row["classification"] != "publication-ready GCI"]
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "refreshed_qoi_mesh_gate_status.csv", all_rows, STATUS_FIELDS)
    write_csv(output_dir / "thermal_mesh_gate_qois.csv", thermal_rows, STATUS_FIELDS)
    write_csv(output_dir / "thermal_mesh_gate_evidence.csv", evidence_rows, EVIDENCE_FIELDS)
    write_csv(output_dir / "blocked_or_diagnostic_qois.csv", blocked_or_diagnostic, STATUS_FIELDS)
    write_csv(output_dir / "thermal_admission_table.csv", admission_rows, ADMISSION_FIELDS)
    write_csv(output_dir / "sign_convention_table.csv", sign_rows, SIGN_FIELDS)

    classification_counts = Counter(str(row["classification"]) for row in all_rows)
    classification_counts = Counter({key: classification_counts.get(key, 0) for key in CLASSIFICATION_ORDER})
    admission_counts = Counter(str(row["admission_class"]) for row in admission_rows)
    summary = {
        "task_id": TASK_ID,
        "generated_at": now(),
        "case_id": CASE_ID,
        "source_id": SOURCE_ID,
        "coarse_csv": rel(coarse_csv),
        "medium_csv": rel(medium_csv),
        "fine_csv": rel(fine_csv),
        "coarse_summary": rel(coarse_summary_path),
        "medium_summary": rel(medium_summary_path),
        "fine_summary": rel(fine_summary_path),
        "closure_gci_package": rel(closure_gci_dir),
        "enthalpy_source": rel(enthalpy_csv),
        "sign_review_source": rel(sign_review_csv),
        "boundary_segment_source": rel(DEFAULT_BOUNDARY_SEGMENT_CSV),
        "output_dir": rel(output_dir),
        "r21": r21,
        "r32": r32,
        "native_solver_outputs_mutated": False,
        "unified_qoi_row_count": len(all_rows),
        "thermal_qoi_row_count": len(thermal_rows),
        "closure_qoi_row_count": len(closure_rows),
        "complete_triplet_count": sum(1 for row in all_rows if row["complete_triplet"] is True),
        "publication_ready_count": sum(1 for row in all_rows if row["classification"] == "publication-ready GCI"),
        "fit_admissible_thermal_count": sum(1 for row in thermal_rows if row["fit_admissible"] == "yes"),
        "admission_row_count": len(admission_rows),
        "fit_admissible_admission_count": sum(1 for row in admission_rows if row["fit_eligible"] == "yes"),
        "admission_class_counts": dict(sorted(admission_counts.items())),
        "classification_counts": dict(classification_counts),
        "main_status": "no_publication_ready_gci_rows",
        "next_recommended_task": "thermal_sign_enthalpy_heat_balance_admission_review",
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(make_readme(summary), encoding="utf-8")
    (output_dir / "thermal_admission_memo.md").write_text(
        make_admission_memo(summary, admission_rows), encoding="utf-8"
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coarse-csv", default=str(DEFAULT_COARSE_CSV))
    parser.add_argument("--medium-csv", default=str(DEFAULT_MEDIUM_CSV))
    parser.add_argument("--fine-csv", default=str(DEFAULT_FINE_CSV))
    parser.add_argument("--coarse-summary", default=str(DEFAULT_COARSE_SUMMARY))
    parser.add_argument("--medium-summary", default=str(DEFAULT_MEDIUM_SUMMARY))
    parser.add_argument("--fine-summary", default=str(DEFAULT_FINE_SUMMARY))
    parser.add_argument("--closure-gci-dir", default=str(DEFAULT_CLOSURE_GCI_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--enthalpy-csv", default=str(DEFAULT_ENTHALPY_CSV))
    parser.add_argument("--sign-review-csv", default=str(DEFAULT_SIGN_REVIEW_CSV))
    parser.add_argument("--r21", type=float, default=DEFAULT_R21)
    parser.add_argument("--r32", type=float, default=DEFAULT_R32)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    build_package(
        Path(args.coarse_csv),
        Path(args.medium_csv),
        Path(args.fine_csv),
        Path(args.coarse_summary),
        Path(args.medium_summary),
        Path(args.fine_summary),
        Path(args.closure_gci_dir),
        Path(args.output_dir),
        Path(args.enthalpy_csv),
        Path(args.sign_review_csv),
        args.r21,
        args.r32,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
