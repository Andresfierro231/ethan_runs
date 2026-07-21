#!/usr/bin/env python3
"""Build TODO-PRED-HYDRAULIC-GATE from pressure-only and forward-v0 evidence."""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
PRESSURE_DIR = (
    ROOT
    / "work_products/2026-07/2026-07-13"
    / "2026-07-13_salt2_pressure_only_mesh_family_comparison"
)
GCI_DIR = (
    ROOT
    / "work_products/2026-07/2026-07-13"
    / "2026-07-13_salt2_closure_qoi_mesh_gci"
)
FORWARD_V0_DIR = (
    ROOT
    / "work_products/2026-07/2026-07-13"
    / "2026-07-13_predictive_forward_v0_imposed_cooler"
)
OUT_DIR = (
    ROOT
    / "work_products/2026-07/2026-07-13"
    / "2026-07-13_predictive_hydraulic_gate"
)

FIT_GATE_COLUMNS = [
    "lane",
    "span",
    "fit_safety",
    "basis",
    "medium_value",
    "fine_value",
    "delta_pct",
    "gci_admission_decision",
    "gci_verdict",
    "gci_publication_ready",
    "gate_decision",
    "allowed_use",
]
RESIDUAL_COLUMNS = [
    "case_id",
    "fluid_case_name",
    "variant_id",
    "engine",
    "accepted_for_validation",
    "mdot_kg_s",
    "cfd_mdot_kg_s",
    "mdot_error_vs_cfd_kg_s",
    "mdot_error_vs_cfd_pct",
    "mdot_error_vs_experimental_kg_s",
    "pressure_residual_Pa",
    "deltaP_buoyancy_Pa",
    "deltaP_losses_Pa",
    "root_status",
    "hydraulic_interpretation",
]
DECISION_COLUMNS = [
    "gate_item",
    "status",
    "evidence",
    "decision",
    "blocked_by",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column)) for column in columns})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    return str(value)


def fnum(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def pct(error: float | None, target: float | None) -> float | None:
    if error is None or target in (None, 0):
        return None
    return 100.0 * error / abs(target)


def gci_index(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    index: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        lane = row.get("lane", "")
        span = row.get("span", "")
        if lane == "pressure_gradient_friction" and row.get("method") != "section_mean_static_gradient":
            continue
        index[(lane, span)] = row
    return index


def fit_gate_decision(row: dict[str, str], gci_row: dict[str, str] | None) -> tuple[str, str]:
    lane = row["lane"]
    fit_safety = row["fit_safety"]
    publication_ready = (gci_row or {}).get("publication_ready", "no")
    if lane == "pressure_gradient_friction" and fit_safety == "fit_safe_pressure_gradient":
        if publication_ready == "yes":
            return "fit_safe_publication_candidate", "may_train_raw_pressure_gradient_friction"
        return (
            "fit_safe_but_gci_not_publication_ready",
            "may_screen_or_calibrate_hydraulic_terms_with_mesh_caveat",
        )
    if lane == "momentum_corrected_friction" and fit_safety == "fit_safe_momentum_corrected":
        return (
            "fit_safe_momentum_corrected_diagnostic",
            "may_inform_debuoyed_friction_or_profile_terms_not_raw_pressure_gradient_fit",
        )
    return (
        "not_fit_safe_for_training",
        "diagnostic_only_pressure_recovery_or_noise",
    )


def build_fit_gate_rows(pressure_dir: Path, gci_dir: Path) -> list[dict[str, Any]]:
    fit_rows = read_csv(pressure_dir / "fit_safety_summary.csv")
    gci_rows = gci_index(read_csv(gci_dir / "closure_qoi_admission_decisions.csv"))
    output: list[dict[str, Any]] = []
    for row in fit_rows:
        lane = row["lane"]
        span = row["span"]
        gci_row = gci_rows.get((lane, span))
        decision, allowed_use = fit_gate_decision(row, gci_row)
        output.append(
            {
                "lane": lane,
                "span": span,
                "fit_safety": row["fit_safety"],
                "basis": row["basis"],
                "medium_value": fnum(row.get("medium_f")),
                "fine_value": fnum(row.get("fine_f")),
                "delta_pct": fnum(row.get("delta_pct")),
                "gci_admission_decision": (gci_row or {}).get("admission_decision", "not_in_gci_table"),
                "gci_verdict": (gci_row or {}).get("gci_verdict", ""),
                "gci_publication_ready": (gci_row or {}).get("publication_ready", "no"),
                "gate_decision": decision,
                "allowed_use": allowed_use,
            }
        )
    return output


def hydraulic_interpretation(row: dict[str, str]) -> str:
    error = fnum(row.get("mdot_error_vs_cfd_kg_s"))
    residual = fnum(row.get("pressure_residual_Pa"))
    if error is not None and error > 0:
        if residual is not None and abs(residual) <= 2.5:
            return "pressure_root_converged_but_mdot_overpredicted"
        return "mdot_overpredicted_pressure_residual_review"
    if error is not None and error < 0:
        return "mdot_underpredicted"
    return "mdot_not_quantified"


def build_residual_rows(forward_dir: Path) -> list[dict[str, Any]]:
    rows = read_csv(forward_dir / "forward_v0_results.csv")
    output: list[dict[str, Any]] = []
    for row in rows:
        error = fnum(row.get("mdot_error_vs_cfd_kg_s"))
        cfd_mdot = fnum(row.get("cfd_mdot_kg_s"))
        output.append(
            {
                "case_id": row.get("case_id"),
                "fluid_case_name": row.get("fluid_case_name"),
                "variant_id": row.get("variant_id"),
                "engine": row.get("engine"),
                "accepted_for_validation": row.get("accepted_for_validation"),
                "mdot_kg_s": fnum(row.get("mdot_kg_s")),
                "cfd_mdot_kg_s": cfd_mdot,
                "mdot_error_vs_cfd_kg_s": error,
                "mdot_error_vs_cfd_pct": pct(error, cfd_mdot),
                "mdot_error_vs_experimental_kg_s": fnum(row.get("mdot_error_vs_experimental_kg_s")),
                "pressure_residual_Pa": fnum(row.get("pressure_residual_Pa")),
                "deltaP_buoyancy_Pa": fnum(row.get("deltaP_buoyancy_Pa")),
                "deltaP_losses_Pa": fnum(row.get("deltaP_losses_Pa")),
                "root_status": row.get("root_status"),
                "hydraulic_interpretation": hydraulic_interpretation(row),
            }
        )
    return output


def mean(values: Iterable[float | None]) -> float | None:
    finite = [value for value in values if value is not None and math.isfinite(value)]
    if not finite:
        return None
    return sum(finite) / len(finite)


def summarize_forward_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    variant_ids = sorted({str(row["variant_id"]) for row in rows})
    summary_rows: list[dict[str, Any]] = []
    for variant_id in variant_ids:
        subset = [row for row in rows if row["variant_id"] == variant_id]
        summary_rows.append(
            {
                "variant_id": variant_id,
                "n_rows": len(subset),
                "mean_mdot_error_vs_cfd_kg_s": mean(
                    fnum(row.get("mdot_error_vs_cfd_kg_s")) for row in subset
                ),
                "mean_mdot_error_vs_cfd_pct": mean(
                    fnum(row.get("mdot_error_vs_cfd_pct")) for row in subset
                ),
                "max_abs_pressure_residual_Pa": max(
                    abs(fnum(row.get("pressure_residual_Pa")) or 0.0) for row in subset
                ),
                "all_mdot_overpredicted": all(
                    (fnum(row.get("mdot_error_vs_cfd_kg_s")) or 0.0) > 0 for row in subset
                ),
            }
        )
    return summary_rows


def build_decision_rows(
    fit_rows: list[dict[str, Any]],
    residual_rows: list[dict[str, Any]],
    gci_summary: dict[str, Any],
    pressure_summary: dict[str, Any],
) -> list[dict[str, str]]:
    pressure_safe = [
        row["span"]
        for row in fit_rows
        if row["lane"] == "pressure_gradient_friction"
        and row["fit_safety"] == "fit_safe_pressure_gradient"
    ]
    momentum_safe = [
        row["span"]
        for row in fit_rows
        if row["lane"] == "momentum_corrected_friction"
        and row["fit_safety"] == "fit_safe_momentum_corrected"
    ]
    forward_summary = summarize_forward_rows(residual_rows)
    f1 = next(row for row in forward_summary if row["variant_id"] == "F1_heater_only")
    f0 = next(row for row in forward_summary if row["variant_id"] == "F0_current_fluid_sources")
    return [
        {
            "gate_item": "raw_pressure_gradient_fit_rows",
            "status": "limited_fit_safe",
            "evidence": ", ".join(pressure_safe),
            "decision": "Use only these rows for raw pressure-gradient friction fitting; all other raw pressure-gradient spans are diagnostic.",
            "blocked_by": "GCI publication readiness remains false for all Closure-QOI rows.",
        },
        {
            "gate_item": "momentum_corrected_fit_rows",
            "status": "fit_safe_diagnostic_lane",
            "evidence": ", ".join(momentum_safe),
            "decision": "Use as debuoyed/profile-term evidence, not as a substitute for raw pressure-gradient friction.",
            "blocked_by": "Strong buoyancy correction on lower_leg and upper_leg; GCI failed or missing for publication.",
        },
        {
            "gate_item": "forward_v0_mdot_predictivity",
            "status": "failed_overprediction_gate",
            "evidence": (
                f"F0 mean mdot error vs CFD {f0['mean_mdot_error_vs_cfd_kg_s']:.6f} kg/s; "
                f"F1 mean mdot error vs CFD {f1['mean_mdot_error_vs_cfd_kg_s']:.6f} kg/s."
            ),
            "decision": "Do not claim thermal predictivity from the heater-only Tmean improvement while mdot is high.",
            "blocked_by": "Pressure-rooted forward-v0 mdot overpredicts every Salt row.",
        },
        {
            "gate_item": "hydraulic_tuning_scope",
            "status": "supported_before_thermal_fit",
            "evidence": "Forward roots converge at low residual but high mdot; AGENT-262 fit-safe rows identify where pressure/friction evidence is usable.",
            "decision": "Tune hydraulic friction/minor-loss/profile terms before fitting thermal parameters; train only on fit-safe rows and keep diagnostic rows separate.",
            "blocked_by": "Need broader fit-safe minor-loss/profile evidence and full solve_case rerun for thesis-strength scoring.",
        },
        {
            "gate_item": "thermal_closure",
            "status": "blocked",
            "evidence": (
                f"AGENT-262 thermal status {pressure_summary.get('thermal_closure_status')}; "
                f"AGENT-284 thermal status {gci_summary.get('thermal_status')}."
            ),
            "decision": "No thermal UA/HTC/Nu fit claim is admitted by this hydraulic gate.",
            "blocked_by": "Fine thermal extraction/GCI blocker remains unresolved.",
        },
    ]


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    pressure_safe = ", ".join(summary["pressure_gradient_fit_safe_spans"])
    momentum_safe = ", ".join(summary["momentum_corrected_fit_safe_spans"])
    f0 = summary["forward_v0_variant_summary"]["F0_current_fluid_sources"]
    f1 = summary["forward_v0_variant_summary"]["F1_heater_only"]
    path.write_text(
        "\n".join(
            [
                "# Predictive Hydraulic Gate",
                "",
                "Task: `TODO-PRED-HYDRAULIC-GATE`",
                "",
                "This package gates pressure-rooted mdot predictivity before any thermal-fit claim. It reads the AGENT-262 pressure-only mesh-family package, the AGENT-284 Closure-QOI GCI package, and the TODO-PRED-FORWARD-V0 imposed-cooler fast-scan package. No native CFD solver outputs or external Fluid files are modified.",
                "",
                "## Start Here",
                "",
                "Why this exists: forward-v0 improved heater-only CFD Tmean error, but still overpredicted mdot. This gate prevents that thermal-looking improvement from hiding pressure-rooted hydraulic failure.",
                "",
                "Files to open first:",
                "",
                "- `hydraulic_gate_decisions.csv` for the admission decision.",
                "- `hydraulic_fit_safety_gate.csv` for fit-safe pressure/friction rows.",
                "- `forward_v0_hydraulic_residuals.csv` for case-level mdot and pressure residual evidence.",
                "- `summary.json` for machine-readable counts and source paths.",
                "",
                "Trusted packages: AGENT-262 Salt2 pressure-only mesh-family comparison, AGENT-284 Salt2 Closure-QOI mesh GCI, and TODO-PRED-FORWARD-V0 imposed-cooler fast-scan.",
                "",
                "Active board row: `TODO-PRED-HYDRAULIC-GATE`.",
                "",
                "Next task sequence: run a broader hydraulic-term fit using only fit-safe rows, then collect or stage minor-loss/profile evidence, then rerun forward scoring before any thermal correction fit.",
                "",
                "Output contract: keep raw pressure-gradient, momentum-corrected, forward-mdot, and thermal-blocker evidence in separate files and fields.",
                "",
                "Do-not-do guardrails: do not mutate native CFD outputs, do not edit external Fluid here, do not train thermal UA/HTC/Nu parameters from this package, and do not treat pressure-recovery/noise rows as training rows.",
                "",
                "Unresolved blockers: no publication-ready Closure-QOI GCI rows, full `solve_case` forward run not rerun here, no broadened minor-loss/profile extraction, and thermal mesh/GCI remains blocked.",
                "",
                "## Key Findings",
                "",
                f"- Raw pressure-gradient fit-safe rows: `{pressure_safe}`.",
                f"- Momentum-corrected fit-safe diagnostic rows: `{momentum_safe}`.",
                f"- `F0_current_fluid_sources` mean mdot error vs CFD: `{f0['mean_mdot_error_vs_cfd_kg_s']:.6f} kg/s` (`{f0['mean_mdot_error_vs_cfd_pct']:.2f}%`).",
                f"- `F1_heater_only` mean mdot error vs CFD: `{f1['mean_mdot_error_vs_cfd_kg_s']:.6f} kg/s` (`{f1['mean_mdot_error_vs_cfd_pct']:.2f}%`).",
                "- Both forward-v0 variants overpredict mdot for every Salt row, even where pressure residuals are small.",
                "- Pressure/friction evidence supports a dedicated hydraulic tuning lane for friction, minor-loss, and profile terms before thermal fitting. Training must stay restricted to fit-safe rows; pressure-recovery/noise rows remain diagnostic.",
                "- Thermal closure remains blocked; this package admits no thermal UA/HTC/Nu claim.",
                "",
                "## Outputs",
                "",
                "- `hydraulic_fit_safety_gate.csv`",
                "- `forward_v0_hydraulic_residuals.csv`",
                "- `hydraulic_gate_decisions.csv`",
                "- `summary.json`",
                "",
                "## Reproduce",
                "",
                "```bash",
                "python3 tools/analyze/build_predictive_hydraulic_gate.py",
                "python3 -m unittest tools.analyze.test_predictive_hydraulic_gate",
                "```",
                "",
                "## Interpretation Boundary",
                "",
                "This is a hydraulic gate. It separates pressure residual, friction fit safety, and mdot error from thermal source/sink parameters. The heater-only forward-v0 thermal improvement remains blocked from thermal-fit interpretation until mdot predictivity and thermal mesh/GCI blockers are resolved.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def build_package(
    output_dir: Path = OUT_DIR,
    pressure_dir: Path = PRESSURE_DIR,
    gci_dir: Path = GCI_DIR,
    forward_dir: Path = FORWARD_V0_DIR,
) -> dict[str, Any]:
    pressure_summary = json.loads((pressure_dir / "summary.json").read_text(encoding="utf-8"))
    gci_summary = json.loads((gci_dir / "summary.json").read_text(encoding="utf-8"))

    fit_rows = build_fit_gate_rows(pressure_dir, gci_dir)
    residual_rows = build_residual_rows(forward_dir)
    decision_rows = build_decision_rows(fit_rows, residual_rows, gci_summary, pressure_summary)
    forward_summary_rows = summarize_forward_rows(residual_rows)
    forward_summary = {row["variant_id"]: row for row in forward_summary_rows}

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "hydraulic_fit_safety_gate.csv", fit_rows, FIT_GATE_COLUMNS)
    write_csv(output_dir / "forward_v0_hydraulic_residuals.csv", residual_rows, RESIDUAL_COLUMNS)
    write_csv(output_dir / "hydraulic_gate_decisions.csv", decision_rows, DECISION_COLUMNS)

    pressure_safe = [
        row["span"]
        for row in fit_rows
        if row["lane"] == "pressure_gradient_friction"
        and row["fit_safety"] == "fit_safe_pressure_gradient"
    ]
    momentum_safe = [
        row["span"]
        for row in fit_rows
        if row["lane"] == "momentum_corrected_friction"
        and row["fit_safety"] == "fit_safe_momentum_corrected"
    ]
    summary = {
        "task_id": "TODO-PRED-HYDRAULIC-GATE",
        "generated_utc": utc_now(),
        "output_dir": rel(output_dir),
        "source_files": {
            "agent_262_pressure_package": rel(pressure_dir),
            "agent_284_closure_qoi_gci_package": rel(gci_dir),
            "forward_v0_package": rel(forward_dir),
        },
        "pressure_gradient_fit_safe_spans": pressure_safe,
        "momentum_corrected_fit_safe_spans": momentum_safe,
        "n_fit_gate_rows": len(fit_rows),
        "n_forward_v0_residual_rows": len(residual_rows),
        "forward_v0_variant_summary": forward_summary,
        "hydraulic_gate_status": "blocked_for_thermal_claim_mdot_overpredicted",
        "hydraulic_tuning_recommendation": "tune friction/minor-loss/profile terms before thermal parameters; train only on fit-safe rows",
        "thermal_closure_status": "blocked",
        "native_solver_outputs_mutated": False,
        "external_fluid_modified": False,
    }
    write_json(output_dir / "summary.json", summary)
    write_readme(output_dir / "README.md", summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--pressure-dir", type=Path, default=PRESSURE_DIR)
    parser.add_argument("--gci-dir", type=Path, default=GCI_DIR)
    parser.add_argument("--forward-dir", type=Path, default=FORWARD_V0_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_package(args.output_dir, args.pressure_dir, args.gci_dir, args.forward_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
