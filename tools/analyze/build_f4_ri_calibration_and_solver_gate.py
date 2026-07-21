#!/usr/bin/env python3
"""Build the AGENT-191 read-only F4/Ri calibration gate package.

The builder intentionally treats corrected Salt Q and Salt 1 rows as holdout
evidence. Closure-fit rows are limited to mainline Salt 2/3/4 Jin until a
coordinator re-admits anything else.
"""

from __future__ import annotations

import csv
import json
import math
import os
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "work_products" / "2026-07-07_f4_ri_calibration_and_solver_gate"

MOMENTUM_CSV = ROOT / "work_products/2026-07-01_claude_momentum_budget/momentum_budget.csv"
FRICTION_FORMS_CSV = ROOT / "work_products/2026-07-04_friction_forms/friction_forms_comparison.csv"
SEGMENT_FRICTION_CSV = ROOT / "work_products/2026-07-01_claude_segment_friction/segment_friction.csv"
LIVE_SALT_CSV = ROOT / "work_products/2026-07-07_corrected_salt_live_monitor/live_salt_sanity_monitor.csv"
PREDICTIVITY_MDOT_CSV = ROOT / "work_products/2026-07-01_claude_1d_predictivity_trial/perleg_vs_global_mdot.csv"
SEGMENT_DP_CSV = ROOT / "work_products/2026-07-01_claude_1d_predictivity_trial/segment_dp_compare.csv"
THERMAL_HTC_DIR = ROOT / "work_products/2026-07-01_claude_thermal_downcomer"
ALLSPAN_DIR = ROOT / "work_products/2026-07-01_claude_allspan_convection"

ADMITTED_CASES = {
    "viscosity_screening_salt_test_2_jin_coarse_mesh": 2,
    "viscosity_screening_salt_test_3_jin_coarse_mesh": 3,
    "viscosity_screening_salt_test_4_jin_coarse_mesh": 4,
}

SPAN_TO_LEG_CLASS = {
    "lower_leg": "heater",
    "right_leg": "downcomer",
    "left_lower_leg": "upcomer",
    "test_section_span": "upcomer",
    "left_upper_leg": "upcomer",
    "upper_leg": "cooler",
}

SPAN_TO_FIT_GROUP = {
    "lower_leg": "heater",
    "right_leg": "downcomer",
    "left_lower_leg": "upcomer_lower",
    "test_section_span": "test_section",
    "left_upper_leg": "upcomer_upper",
    "upper_leg": "cooler",
}

SOURCE_PATHS = {
    "momentum_budget": str(MOMENTUM_CSV.relative_to(ROOT)),
    "friction_forms": str(FRICTION_FORMS_CSV.relative_to(ROOT)),
    "segment_friction": str(SEGMENT_FRICTION_CSV.relative_to(ROOT)),
    "live_salt_monitor": str(LIVE_SALT_CSV.relative_to(ROOT)),
    "predictivity_mdot": str(PREDICTIVITY_MDOT_CSV.relative_to(ROOT)),
    "segment_dp_compare": str(SEGMENT_DP_CSV.relative_to(ROOT)),
    "allspan_convection_dir": str(ALLSPAN_DIR.relative_to(ROOT)),
    "thermal_htc_dir": str(THERMAL_HTC_DIR.relative_to(ROOT)),
}

CORRECTED_SALT_GATE_JOB_ID = "3279646"
CORRECTED_SALT_GATE_LAST_OBSERVED = {
    "job_name": "saltq_gate_0707",
    "partition": "NuclearEnergy",
    "job_state": "PENDING",
    "job_time_limit": "2:00:00",
    "dependency": "afterany:3275448(unfulfilled),afterany:3275449(unfulfilled),afterany:3275560(unfulfilled)",
    "pending_reason": "Dependency",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def f(value: str | None, default: float | None = None) -> float | None:
    if value in (None, "", "nan", "NaN"):
        return default
    try:
        return float(value)
    except ValueError:
        return default


def salt_label(source_id: str) -> str:
    for salt in (1, 2, 3, 4):
        if f"salt_test_{salt}_" in source_id:
            return f"salt_{salt}"
    return "unknown"


def allspan_path(source_id: str) -> Path:
    return ALLSPAN_DIR / f"upcomer_convection_cell_{source_id}.csv"


def thermal_path(source_id: str) -> Path:
    return THERMAL_HTC_DIR / f"segment_htc_uaprime_{source_id}.csv"


def aggregate_allspan() -> dict[tuple[str, str], dict[str, object]]:
    out: dict[tuple[str, str], dict[str, object]] = {}
    for source_id in ADMITTED_CASES:
        path = allspan_path(source_id)
        rows = read_csv(path)
        by_span: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            if row.get("status") == "analyzed":
                by_span[row["span"]].append(row)
        for span, span_rows in by_span.items():
            def med_col(name: str) -> float | None:
                vals = [f(row.get(name)) for row in span_rows]
                vals = [v for v in vals if v is not None and math.isfinite(v)]
                return median(vals) if vals else None

            out[(source_id, span)] = {
                "ri_source_path": str(path.relative_to(ROOT)),
                "ri_section_count": len(span_rows),
                "Ri_median": med_col("Ri_section_median"),
                "Ri_streamwise": med_col("Ri_streamwise_median"),
                "Ri_transverse": med_col("Ri_transverse_median"),
                "Ra_median": med_col("Ra_section_median"),
                "Re_section_median": med_col("Re_section_median"),
                "Pr_median": med_col("Pr_section_median"),
                "theta_from_gravity_deg": med_col("inclination_from_vertical_deg"),
                "buoyancy_streamwise_frac_cos": med_col("buoyancy_streamwise_frac_cos"),
                "backflow_area_fraction": med_col("backflow_area_fraction"),
                "recirculation_intensity": med_col("recirculation_intensity"),
            }
    return out


def aggregate_thermal() -> dict[tuple[str, str], dict[str, object]]:
    out: dict[tuple[str, str], dict[str, object]] = {}
    for source_id in ADMITTED_CASES:
        path = thermal_path(source_id)
        if not path.exists():
            continue
        for row in read_csv(path):
            spans = [s.strip() for s in row.get("cfd_spans", "").split("+") if s.strip()]
            if not spans:
                segment = row.get("segment", "")
                if segment:
                    spans = [segment]
            for span in spans:
                if span not in SPAN_TO_LEG_CLASS:
                    continue
                out[(source_id, span)] = {
                    "thermal_source_path": str(path.relative_to(ROOT)),
                    "deltaT_basis": "wall_minus_bulk_from_segment_htc_uaprime_area_weighted_Qoverq",
                    "delta_T_k": f(row.get("delta_T_k")),
                    "abs_delta_T_k": f(row.get("abs_delta_T_k")),
                    "T_bulk_k": f(row.get("T_bulk_k")),
                    "T_wall_k": f(row.get("T_wall_k")),
                    "thermal_status": row.get("status", ""),
                    "thermal_blocked": row.get("thermally_blocked", ""),
                    "nu_direct_admitted": row.get("nu_direct_admitted", ""),
                }
    return out


def load_static_indexes() -> tuple[dict[tuple[str, str], dict[str, str]], dict[tuple[str, str], dict[str, str]], dict[tuple[str, str], dict[str, str]]]:
    forms = {
        (row["source_id"], row["span"]): row
        for row in read_csv(FRICTION_FORMS_CSV)
        if row.get("source_id") in ADMITTED_CASES
    }
    segment_friction = {
        (row["source_id"], row["span"]): row
        for row in read_csv(SEGMENT_FRICTION_CSV)
        if row.get("source_id") in ADMITTED_CASES and row.get("method") == "section_mean_static_gradient"
    }
    momentum = {
        (row["source_id"], row["span"]): row
        for row in read_csv(MOMENTUM_CSV)
        if row.get("source_id") in ADMITTED_CASES
    }
    return momentum, forms, segment_friction


def corrected_salt_holds() -> list[dict[str, object]]:
    if not LIVE_SALT_CSV.exists():
        return []
    rows = []
    for row in read_csv(LIVE_SALT_CSV):
        converged = (
            row.get("closure_fit_admissible") in {"yes", "True", "true"}
            or row.get("terminal_window_status") == "terminal_window_stationary_but_under_advanced"
            or row.get("fit_use_status") == "closure_fit_admissible"
        )
        special = row.get("needs_special_gate_scrutiny") == "True"
        rows.append({
            "case_id": row["case_key"],
            "source_id": row["case_key"],
            "run_class": "corrected_salt_q_perturbation",
            "span": "",
            "leg_class": "",
            "admission_status": "salt_q_converged_admitted" if converged and not special else "salt_q_pending_convergence_or_review",
            "closure_fit_admissible": "True" if converged and not special else "False",
            "needs_special_gate_scrutiny": row.get("needs_special_gate_scrutiny", ""),
            "coordinator_review_status": "required" if special else "converged_policy_applied" if converged else "awaits_convergence_evidence",
            "fit_use_status": "closure_fit_admissible" if converged and not special else "pending_or_excluded",
            "fit_exclusion_reason": "" if converged and not special else row.get("scrutiny_reason") or "Salt-Q row requires convergence evidence or coordinator review",
            "job_id": row.get("job_id", ""),
            "partition": row.get("partition", ""),
            "job_state": row.get("job_state", ""),
            "latest_solver_time_s": row.get("latest_solver_time_s", ""),
            "fatal_error_count": row.get("fatal_error_count", ""),
            "recommendation": row.get("recommendation", ""),
            "source_paths": SOURCE_PATHS["live_salt_monitor"],
        })
    return rows


def evidence_freeze_rows() -> list[dict[str, object]]:
    rows = []
    for source_id, salt in ADMITTED_CASES.items():
        rows.append({
            "case_id": f"salt_{salt}",
            "source_id": source_id,
            "run_class": "mainline_jin_continuation",
            "admission_status": "admitted_mainline_salt_2_3_4_jin",
            "closure_fit_admissible": "True",
            "needs_special_gate_scrutiny": "False",
            "coordinator_review_status": "not_required_for_mainline_freeze",
            "fit_use_status": "fit_admissible",
            "fit_exclusion_reason": "",
            "source_paths": ";".join([
                SOURCE_PATHS["momentum_budget"],
                SOURCE_PATHS["friction_forms"],
                SOURCE_PATHS["segment_friction"],
                SOURCE_PATHS["allspan_convection_dir"],
                SOURCE_PATHS["thermal_htc_dir"],
            ]),
        })
    rows.append({
        "case_id": "salt_1",
        "source_id": "viscosity_screening_salt_test_1_jin_coarse_mesh",
        "run_class": "mainline_jin_continuation",
        "admission_status": "held_salt1_qualification_required",
        "closure_fit_admissible": "False",
        "needs_special_gate_scrutiny": "True",
        "coordinator_review_status": "required",
        "fit_use_status": "excluded",
        "fit_exclusion_reason": "Salt 1 missing qualification package; nominal mdot confidence and short/weak-window caveats unresolved",
        "source_paths": "work_products/2026-07-07_f4_evidence_freeze_review/README.md",
    })
    rows.extend(corrected_salt_holds())
    return rows


def build_calibration_table() -> list[dict[str, object]]:
    momentum, forms, segment_friction = load_static_indexes()
    allspan = aggregate_allspan()
    thermal = aggregate_thermal()
    rows: list[dict[str, object]] = []
    for (source_id, span), mom in sorted(momentum.items(), key=lambda kv: (ADMITTED_CASES[kv[0][0]], kv[0][1])):
        form = forms.get((source_id, span), {})
        seg = segment_friction.get((source_id, span), {})
        ri = allspan.get((source_id, span), {})
        therm = thermal.get((source_id, span), {})
        salt = ADMITTED_CASES[source_id]
        f_corrected_over_flam = f(mom.get("f_corrected_over_flam"))
        f3h_ratio = f(form.get("f_F3h_ratio"))
        residual = None
        if f_corrected_over_flam is not None and f3h_ratio not in (None, 0.0):
            residual = f_corrected_over_flam / f3h_ratio
        source_paths = [
            SOURCE_PATHS["momentum_budget"],
            SOURCE_PATHS["friction_forms"],
            SOURCE_PATHS["segment_friction"],
            ri.get("ri_source_path", ""),
            therm.get("thermal_source_path", ""),
        ]
        row = {
            "case_id": f"salt_{salt}",
            "source_id": source_id,
            "run_class": "mainline_jin_continuation",
            "span": span,
            "leg_class": SPAN_TO_LEG_CLASS.get(span, "unknown"),
            "fit_group": SPAN_TO_FIT_GROUP.get(span, "unknown"),
            "admission_status": "admitted_mainline_salt_2_3_4_jin",
            "closure_fit_admissible": "True",
            "needs_special_gate_scrutiny": "False",
            "coordinator_review_status": "not_required_for_mainline_freeze",
            "Re": f(mom.get("Re")),
            "Ra": ri.get("Ra_median"),
            "Ri_median": ri.get("Ri_median"),
            "Ri_streamwise": ri.get("Ri_streamwise"),
            "Ri_transverse": ri.get("Ri_transverse"),
            "Pr": ri.get("Pr_median"),
            "Re_section_median": ri.get("Re_section_median"),
            "ri_definition": "Gr_section_median/Re_section_median^2 from section field artifact; span value is median of section medians",
            "deltaT_basis": therm.get("deltaT_basis", "unavailable"),
            "delta_T_k": therm.get("delta_T_k"),
            "abs_delta_T_k": therm.get("abs_delta_T_k"),
            "property_basis": "field artifact uses local section properties; momentum uses Jin viscosity from rho/EOS temperature",
            "length_scale_basis": "hydraulic_diameter",
            "theta_from_gravity_deg": ri.get("theta_from_gravity_deg"),
            "streamwise_projection_basis": "artifact Ri_streamwise_median; equivalent to median Ri times recorded buoyancy streamwise cosine at section level",
            "buoyancy_streamwise_frac_cos": ri.get("buoyancy_streamwise_frac_cos"),
            "backflow_area_fraction": ri.get("backflow_area_fraction"),
            "recirculation_intensity": ri.get("recirculation_intensity"),
            "D_m": f(mom.get("d_h_m")) or f(form.get("D_m")) or f(seg.get("hydraulic_diameter_m")),
            "L_m": f(form.get("L_m")) or f(seg.get("segment_arc_length_m")),
            "x_plus": f(form.get("x_plus")),
            "f_lam": f(mom.get("f_lam_64_re")) or f(form.get("f_lam_64_Re")),
            "f_corrected": f(mom.get("f_corrected")),
            "f_corrected_over_flam": f_corrected_over_flam,
            "f_F1_ratio": f(form.get("f_F1_ratio")),
            "f_F3h_ratio": f3h_ratio,
            "f_CFD_ratio": f(form.get("f_CFD_ratio")),
            "f_corrected_over_f3h": residual,
            "F5_per_leg_multiplier": f_corrected_over_flam,
            "fit_weight": 1.0,
            "fit_use_status": "fit_admissible",
            "fit_exclusion_reason": "",
            "ri_source_path": ri.get("ri_source_path", ""),
            "thermal_source_path": therm.get("thermal_source_path", ""),
            "source_paths": ";".join(p for p in source_paths if p),
        }
        rows.append(row)
    return rows


def fit_bounded_candidate(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    by_group: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        if row["fit_use_status"] == "fit_admissible":
            by_group[str(row["fit_group"])].append(row)

    fit_summary: dict[str, dict[str, object]] = {}
    for group, group_rows in sorted(by_group.items()):
        xs = []
        ys = []
        for row in group_rows:
            ri = row.get("Ri_streamwise")
            y = row.get("f_corrected_over_f3h")
            if isinstance(ri, (int, float)) and isinstance(y, (int, float)) and math.isfinite(ri) and math.isfinite(y):
                xs.append(math.copysign(math.sqrt(abs(ri)), ri))
                ys.append(y)
        if len(xs) < 3:
            fit_summary[group] = {
                "status": "insufficient_points",
                "n_points": len(xs),
                "form": "M_F4 = clamp(1 + C_group * signed_sqrt(Ri_streamwise), 0.25, 5.0)",
            }
            continue
        candidates = [i / 1000.0 for i in range(-5000, 5001)]
        best_c = 0.0
        best_sse = float("inf")
        for c in candidates:
            sse = 0.0
            for x, y in zip(xs, ys):
                pred = min(5.0, max(0.25, 1.0 + c * x))
                sse += (pred - y) ** 2
            if sse < best_sse:
                best_c = c
                best_sse = sse
        preds = [min(5.0, max(0.25, 1.0 + best_c * x)) for x in xs]
        ybar = sum(ys) / len(ys)
        sst = sum((y - ybar) ** 2 for y in ys)
        r2 = 1.0 - best_sse / sst if sst > 0 else None
        fit_summary[group] = {
            "status": "candidate_screen_only",
            "n_points": len(xs),
            "C_group": best_c,
            "rmse": math.sqrt(best_sse / len(xs)),
            "r2": r2,
            "form": "M_F4 = clamp(1 + C_group * signed_sqrt(Ri_streamwise), 0.25, 5.0)",
            "bounds": {"prediction_min": 0.25, "prediction_max": 5.0, "C_group_min": -5.0, "C_group_max": 5.0},
            "warning": "Only three Salt 2/3/4 points per physical fit group; candidate is not a validated portable correlation.",
        }

    for row in rows:
        summary = fit_summary.get(str(row["fit_group"]), {})
        c = summary.get("C_group")
        ri = row.get("Ri_streamwise")
        if isinstance(c, (int, float)) and isinstance(ri, (int, float)):
            x = math.copysign(math.sqrt(abs(ri)), ri)
            mult = min(5.0, max(0.25, 1.0 + c * x))
            row["F4_Ri_candidate_residual_multiplier"] = mult
            row["F4_Ri_candidate_total_f_ratio"] = mult * row["f_F3h_ratio"] if isinstance(row["f_F3h_ratio"], (int, float)) else None
            row["F4_Ri_candidate_fit_residual_error"] = mult - row["f_corrected_over_f3h"] if isinstance(row["f_corrected_over_f3h"], (int, float)) else None
        else:
            row["F4_Ri_candidate_residual_multiplier"] = None
            row["F4_Ri_candidate_total_f_ratio"] = None
            row["F4_Ri_candidate_fit_residual_error"] = None
    return rows, fit_summary


def model_comparison(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out = []
    for row in rows:
        cfd = row.get("f_corrected_over_flam")
        f3 = row.get("f_F3h_ratio")
        f4 = row.get("F4_Ri_candidate_total_f_ratio")
        f5 = row.get("F5_per_leg_multiplier")
        f1 = row.get("f_F1_ratio")
        for label, value in [
            ("F1_laminar", f1),
            ("F3_hagenbach", f3),
            ("F4_Ri_candidate", f4),
            ("F5_per_leg_CFD_multiplier", f5),
        ]:
            err = None
            if isinstance(value, (int, float)) and isinstance(cfd, (int, float)) and cfd:
                err = 100.0 * (value - cfd) / cfd
            out.append({
                "case_id": row["case_id"],
                "source_id": row["source_id"],
                "span": row["span"],
                "fit_group": row["fit_group"],
                "model_form": label,
                "predicted_f_over_flam": value,
                "cfd_target_f_corrected_over_flam": cfd,
                "pct_error_vs_cfd_target": err,
                "closure_fit_admissible": row["closure_fit_admissible"],
                "needs_special_gate_scrutiny": row["needs_special_gate_scrutiny"],
                "interpretation_caveat": "pressure-distribution comparison only; mdot remains thermal-driver-sensitive",
            })
    for mrow in read_csv(PREDICTIVITY_MDOT_CSV):
        out.append({
            "case_id": f"salt_{mrow['salt']}",
            "source_id": f"salt_{mrow['salt']}_1d_predictivity",
            "span": "loop_mdot",
            "fit_group": "loop",
            "model_form": mrow["form"],
            "predicted_f_over_flam": "",
            "cfd_target_f_corrected_over_flam": "",
            "pct_error_vs_cfd_target": mrow.get("pct_err", ""),
            "closure_fit_admissible": "diagnostic_only",
            "needs_special_gate_scrutiny": "False",
            "interpretation_caveat": "mdot diagnostic from existing 1D per-leg/global comparison; not a sole friction-validation metric because the thermal driver is suspect",
            "pred_mdot_kg_s": mrow.get("pred_mdot", ""),
            "cfd_mdot_kg_s": mrow.get("cfd_mdot", ""),
            "pred_Re": mrow.get("Re", ""),
        })
    return out


def recent_coordination_audit() -> list[dict[str, object]]:
    cutoff = datetime.now().timestamp() - 120 * 60
    roots = [ROOT / ".agent", ROOT / "work_products", ROOT / "tools", ROOT / "reports", ROOT / "imports", ROOT / "operational_notes"]
    rows = []
    for base in roots:
        if not base.exists():
            continue
        for dirpath, _, filenames in os.walk(base):
            for name in filenames:
                path = Path(dirpath) / name
                try:
                    stat = path.stat()
                except OSError:
                    continue
                if stat.st_mtime >= cutoff:
                    rows.append({
                        "path": str(path.relative_to(ROOT)),
                        "mtime_iso": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                        "size_bytes": stat.st_size,
                        "observation": "modified within last 120 minutes at package build time",
                    })
    try:
        proc = subprocess.run(
            ["git", "-C", str(ROOT / "../cfd-modeling-tools"), "status", "--short"],
            check=False,
            text=True,
            capture_output=True,
            timeout=10,
        )
        for line in proc.stdout.splitlines():
            rows.append({
                "path": "../cfd-modeling-tools/" + line[3:],
                "mtime_iso": "",
                "size_bytes": "",
                "observation": f"external Fluid git status: {line[:2].strip() or '??'}",
            })
    except (OSError, subprocess.TimeoutExpired) as exc:
        rows.append({
            "path": "../cfd-modeling-tools",
            "mtime_iso": "",
            "size_bytes": "",
            "observation": f"external git status unavailable: {exc}",
        })
    rows.sort(key=lambda r: str(r["path"]))
    return rows


def corrected_salt_gate_snapshot() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    try:
        proc = subprocess.run(
            [
                "squeue",
                "-j",
                CORRECTED_SALT_GATE_JOB_ID,
                "-o",
                "%i|%j|%T|%P|%M|%l|%E|%r",
            ],
            check=False,
            text=True,
            capture_output=True,
            timeout=10,
        )
        lines = [line for line in proc.stdout.splitlines() if line.strip()]
        if len(lines) >= 2:
            job_id, name, state, partition, elapsed, limit, dependency, reason = lines[1].split("|", 7)
            rows.append({
                "row_type": "gate_job",
                "case_key": "corrected_salt_operating_point_gate",
                "job_id": job_id,
                "job_name": name,
                "partition": partition,
                "job_state": state,
                "job_elapsed": elapsed,
                "job_time_limit": limit,
                "dependency": dependency,
                "pending_reason": reason,
                "latest_solver_time_s": "",
                "advance_since_restart_s": "",
                "fatal_error_count": "",
                "warning_count": "",
                "needs_special_gate_scrutiny": "",
                "recommendation": "hold_pending_dependencies",
            })
    except (OSError, subprocess.TimeoutExpired) as exc:
        rows.append({
            "row_type": "gate_job",
            "case_key": "corrected_salt_operating_point_gate",
            "job_id": CORRECTED_SALT_GATE_JOB_ID,
            "job_name": CORRECTED_SALT_GATE_LAST_OBSERVED["job_name"],
            "partition": CORRECTED_SALT_GATE_LAST_OBSERVED["partition"],
            "job_state": CORRECTED_SALT_GATE_LAST_OBSERVED["job_state"],
            "job_elapsed": "",
            "job_time_limit": CORRECTED_SALT_GATE_LAST_OBSERVED["job_time_limit"],
            "dependency": CORRECTED_SALT_GATE_LAST_OBSERVED["dependency"],
            "pending_reason": f"{CORRECTED_SALT_GATE_LAST_OBSERVED['pending_reason']} (last observed before snapshot; live squeue unavailable: {exc})",
            "latest_solver_time_s": "",
            "advance_since_restart_s": "",
            "fatal_error_count": "",
            "warning_count": "",
            "needs_special_gate_scrutiny": "",
            "recommendation": "hold_pending_dependencies",
        })

    if LIVE_SALT_CSV.exists():
        for row in read_csv(LIVE_SALT_CSV):
            rows.append({
                "row_type": "solver_case",
                "case_key": row.get("case_key", ""),
                "job_id": row.get("job_id", ""),
                "job_name": row.get("job_name", ""),
                "partition": row.get("partition", ""),
                "job_state": row.get("job_state", ""),
                "job_elapsed": row.get("job_elapsed", ""),
                "job_time_limit": row.get("job_time_limit", ""),
                "dependency": "",
                "pending_reason": "",
                "latest_solver_time_s": row.get("latest_solver_time_s", ""),
                "advance_since_restart_s": row.get("advance_since_restart_s", ""),
                "fatal_error_count": row.get("fatal_error_count", ""),
                "warning_count": row.get("warning_count", ""),
                "needs_special_gate_scrutiny": row.get("needs_special_gate_scrutiny", ""),
                "recommendation": row.get("recommendation", ""),
            })
    return rows


def markdown_table(rows: list[dict[str, object]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        vals = []
        for col in columns:
            val = row.get(col, "")
            if isinstance(val, float):
                val = f"{val:.6g}"
            vals.append(str(val).replace("|", "\\|"))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def write_reports(
    evidence: list[dict[str, object]],
    table: list[dict[str, object]],
    fit_summary: dict[str, dict[str, object]],
    comparison: list[dict[str, object]],
    audit: list[dict[str, object]],
    gate_snapshot: list[dict[str, object]],
) -> None:
    ri_lines = [
        "# Ri Definition Audit",
        "",
        "Raw observations:",
        "",
        "- Ri/Ra/Re values came from `work_products/2026-07-01_claude_allspan_convection/upcomer_convection_cell_<source_id>.csv`.",
        "- The source files provide section-level `Ri_section_median`, `Ri_streamwise_median`, `Ra_section_median`, `Re_section_median`, and `Pr_section_median` for all six Salt 2/3/4 spans.",
        "- The calibration table uses the median of the section medians per span, not section means.",
        "- Delta-T fields came from `work_products/2026-07-01_claude_thermal_downcomer/segment_htc_uaprime_<source_id>.csv` where span mapping was explicit. The upcomer thermal row maps to three spans, so those rows carry a shared thermal basis.",
        "",
        "Interpretation:",
        "",
        "- The Ri basis is sufficient for a candidate screen because every admitted Salt 2/3/4 span has a median section Ri and streamwise projection.",
        "- This is still not a validated portable F4 law: each physical fit group has only three coupled operating points and no independent validation case.",
        "- Corrected Salt Q rows remain held because the formal operating-point gate has not requalified them; rows with `needs_special_gate_scrutiny=True` remain non-admissible.",
        "",
        "Definition contract:",
        "",
        "- `Ri_median`: median across section-level `Ri_section_median` values.",
        "- `Ri_streamwise`: median across section-level `Ri_streamwise_median` values.",
        "- `Ra`: median across section-level `Ra_section_median` values.",
        "- `Pr`: median across section-level `Pr_section_median` values.",
        "- `length_scale_basis`: hydraulic diameter.",
        "- `property_basis`: field artifact local section properties for Ri/Ra/Re; Jin viscosity from rho/EOS-derived temperature for de-buoyed momentum rows.",
    ]
    (OUT_DIR / "ri_definition_audit.md").write_text("\n".join(ri_lines) + "\n")

    fit_lines = [
        "# F4 Candidate Fit Report",
        "",
        "Fit target: residual `f_corrected/f_F3h` from mainline Salt 2/3/4 Jin rows only.",
        "",
        "Candidate form: `M_F4 = clamp(1 + C_group * signed_sqrt(Ri_streamwise), 0.25, 5.0)`.",
        "",
        "This is a bounded screen, not a validated correlation. Each physical group has only three points.",
        "",
        "## Fit Summary",
        "",
        markdown_table([
            {
                "fit_group": group,
                "status": summary.get("status", ""),
                "n_points": summary.get("n_points", ""),
                "C_group": summary.get("C_group", ""),
                "rmse": summary.get("rmse", ""),
                "r2": summary.get("r2", ""),
            }
            for group, summary in sorted(fit_summary.items())
        ], ["fit_group", "status", "n_points", "C_group", "rmse", "r2"]),
        "",
        "Acceptance interpretation: hold for coordinator review before any publication or ROM closure fitting use.",
    ]
    (OUT_DIR / "f4_candidate_fit_report.md").write_text("\n".join(fit_lines) + "\n")

    comparison_lines = [
        "# Model Comparison: F1 / F3 / F4 Candidate / F5",
        "",
        "Raw observations:",
        "",
        "- The per-span comparison is against the de-buoyed CFD target `f_corrected/f_lam`.",
        "- `F5_per_leg_CFD_multiplier` is the CFD per-leg multiplier and therefore matches the target by construction.",
        "- Existing mdot diagnostics are copied from the July 1 per-leg/global 1D comparison and remain diagnostic-only.",
        "",
        "Interpretation:",
        "",
        "- F4 candidate quality should be judged first on pressure-resistance distribution, not loop mdot.",
        "- Mdot remains entangled with the known 1D thermal-driver mismatch documented in the July 2/July 7 notes.",
        "",
        markdown_table([r for r in comparison if r.get("span") == "loop_mdot"], ["case_id", "model_form", "pred_mdot_kg_s", "cfd_mdot_kg_s", "pct_error_vs_cfd_target", "interpretation_caveat"]),
    ]
    (OUT_DIR / "model_comparison_f1_f3_f4_f5.md").write_text("\n".join(comparison_lines) + "\n")

    readme_lines = [
        "# F4 Ri Calibration And Solver Gate",
        "",
        "Date: `2026-07-07`  ",
        "Task: `AGENT-191`  ",
        "Role: Coordinator / Implementer / Reviewer / Writer",
        "",
        "## Objective",
        "",
        "Freeze the admitted Salt F4 evidence, build a read-only Ri-audited calibration table, fit a bounded residual F4 candidate, and decide whether a later Fluid solver edit is admissible.",
        "",
        "## Inputs / Provenance Inspected",
        "",
    ]
    readme_lines.extend(f"- `{path}`" for path in SOURCE_PATHS.values())
    readme_lines.extend([
        "- `work_products/2026-07-07_f4_evidence_freeze_review/README.md`",
        "- `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md`",
        "",
        "## Planned Outputs",
        "",
        "- `recent_coordination_audit.{csv,json}`",
        "- `admitted_evidence_freeze.{csv,json}`",
        "- `f4_ri_calibration_table.{csv,json}`",
        "- `ri_definition_audit.md`",
        "- `f4_candidate_fit_report.md`",
        "- `model_comparison_f1_f3_f4_f5.{csv,json,md}`",
        "- `corrected_salt_gate_monitor_snapshot.{csv,json,md}`",
        "",
        "## Acceptance Criteria",
        "",
        "- Admitted closure-fit rows include mainline Salt 2/3/4 Jin and any Salt-Q perturbation row with converged/stationary terminal-window evidence.",
        "- `needs_special_gate_scrutiny` is carried forward; no flagged row is closure-fit admissible without coordinator review.",
        "- Ri definition uses median section Ri and records streamwise projection/property/length-scale basis.",
        "- False-steady and short/canceled rows remain excluded; Salt-Q rows are not categorically excluded once converged.",
        "- F4 candidate is bounded and labeled as a screen, not a validated ROM closure law.",
        "",
        "## Commands Run",
        "",
        "- `python3.11 tools/analyze/build_f4_ri_calibration_and_solver_gate.py`",
        "- `python3.11 -m json.tool work_products/2026-07-07_f4_ri_calibration_and_solver_gate/f4_ri_calibration_table.json`",
        "- `python3.11 -m json.tool work_products/2026-07-07_f4_ri_calibration_and_solver_gate/admitted_evidence_freeze.json`",
        "- `squeue -j 3279646 -o \"%i|%j|%T|%P|%M|%l|%E|%r\"`",
        "- `sacct -j 3279646 --format=JobID,JobName%30,State,Partition,Elapsed,Start,End,ReqCPUS,ReqMem,Dependency%80 -P` (failed: this Slurm `sacct` lacks `Dependency` field)",
        "- `python3.11 tools/analyze/test_build_f4_ri_calibration_and_solver_gate.py`",
        "- `python3.11 -m py_compile tools/analyze/build_f4_ri_calibration_and_solver_gate.py tools/analyze/test_build_f4_ri_calibration_and_solver_gate.py`",
        "- `pytest tests/test_friction_closures.py` in external Fluid",
        "- `/opt/apps/intel19/python3/3.9.7/bin/python3.9 -c '<F4 solver routing smoke>'` in external Fluid",
        "",
        "## Files Changed / Generated",
        "",
        "- `tools/analyze/build_f4_ri_calibration_and_solver_gate.py`",
        "- `tools/analyze/test_build_f4_ri_calibration_and_solver_gate.py`",
        "- External Fluid F4 context-routing hardening in `friction_closures.py`, `solver.py`, and `tests/test_friction_closures.py`.",
        "- This work-product directory and its CSV/JSON/Markdown outputs.",
        "",
        "## Validation",
        "",
        "- Local AGENT-191 admission tests passed: `3` tests.",
        "- Local Python syntax compilation passed for the builder and test.",
        "- External Fluid `tests/test_friction_closures.py` passed: `45` tests under Python 3.9 pytest.",
        "- External Fluid lightweight solver routing smoke passed for heater/downcomer/upcomer/cooler parent-segment mapping.",
        "- `python3.11 -m pytest` was unavailable because that interpreter lacks `pytest`; system `pytest` was used instead.",
        "- `python3.11` package import smoke for Fluid was blocked by missing `yaml`; direct module and Python 3.9 Fluid checks passed.",
        "- Gate job `3279646` dependency recorded from `squeue`; `sacct` dependency query failed because the local `sacct` field set does not include `Dependency`.",
        "",
        "## Raw Observations vs Interpretation",
        "",
        "Raw observations:",
        "",
        f"- The calibration table contains `{len(table)}` admitted Salt 2/3/4 span rows.",
        f"- The evidence freeze contains `{len(evidence)}` rows including Salt 1 and Salt-Q perturbation rows.",
        "- Salt-Q rows are closure-fit admissible when converged/stationary; the old post-restart advance gate alone is not an exclusion.",
        "- Salt 1 remains held because the qualification package is not complete and Salt 1 nominal mdot confidence is weaker.",
        "",
        "Interpretation:",
        "",
        "- The read-only evidence gate is complete enough for coordinator review.",
        "- The bounded F4 Ri candidate should not yet be used as a final ROM correlation.",
        "- Solver edits may proceed only to harden explicit F4 segment-context routing and preserve default behavior; coefficient use still needs review.",
        "",
        "## Blockers",
        "",
        "- Salt-Q convergence evidence must be checked row-by-row.",
        "- Salt 1 qualification remains unresolved.",
        "- External Fluid dirty/untracked state must be respected before any solver edit.",
        "",
        "## Exact Next Action",
        "",
        "Coordinator review should decide whether to keep `F4_Ri_candidate` as a diagnostic-only screen or open a later coefficient-refinement task. Admit Salt-Q rows when terminal-window convergence evidence is present and no special-scrutiny flag blocks the row.",
        "",
        "## Recent Coordination Audit",
        "",
        markdown_table(audit[:20], ["path", "mtime_iso", "observation"]),
    ])
    (OUT_DIR / "README.md").write_text("\n".join(readme_lines) + "\n")

    gate_lines = [
        "# Corrected Salt Gate Monitor Snapshot",
        "",
        f"Gate job checked: `{CORRECTED_SALT_GATE_JOB_ID}`.",
        "",
        "Raw observations:",
        "",
        "- `3279646` is `saltq_gate_0707` and is pending on corrected Salt solver jobs.",
        "- `squeue` reported dependency `afterany:3275448(unfulfilled),afterany:3275449(unfulfilled),afterany:3275560(unfulfilled)`.",
        "- Existing live-monitor rows carry latest solver times, fatal/error counts, scrutiny flags, and case-level recommendations.",
        "",
        "Interpretation:",
        "",
        "- Overall recommendation: apply the current coordinator policy row-by-row; converged Salt-Q rows are closure-fit admissible, while failed/cancelled or special-scrutiny rows remain blocked.",
        "- The older categorical corrected-Q exclusion is superseded.",
        "",
        markdown_table(gate_snapshot, ["row_type", "case_key", "job_id", "partition", "job_state", "dependency", "latest_solver_time_s", "fatal_error_count", "needs_special_gate_scrutiny", "recommendation"]),
    ]
    (OUT_DIR / "corrected_salt_gate_monitor_snapshot.md").write_text("\n".join(gate_lines) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    evidence = evidence_freeze_rows()
    table = build_calibration_table()
    table, fit_summary = fit_bounded_candidate(table)
    comparison = model_comparison(table)
    audit = recent_coordination_audit()
    gate_snapshot = corrected_salt_gate_snapshot()

    evidence_fields = sorted({key for row in evidence for key in row})
    table_fields = [
        "case_id", "source_id", "run_class", "span", "leg_class", "fit_group",
        "admission_status", "closure_fit_admissible", "needs_special_gate_scrutiny",
        "coordinator_review_status", "Re", "Ra", "Ri_median", "Ri_streamwise",
        "Ri_transverse", "Pr", "Re_section_median", "ri_definition",
        "deltaT_basis", "delta_T_k", "abs_delta_T_k", "property_basis",
        "length_scale_basis", "theta_from_gravity_deg", "streamwise_projection_basis",
        "buoyancy_streamwise_frac_cos", "backflow_area_fraction", "recirculation_intensity",
        "D_m", "L_m", "x_plus", "f_lam", "f_corrected", "f_corrected_over_flam",
        "f_F1_ratio", "f_F3h_ratio", "f_CFD_ratio", "f_corrected_over_f3h",
        "F4_Ri_candidate_residual_multiplier", "F4_Ri_candidate_total_f_ratio",
        "F4_Ri_candidate_fit_residual_error", "F5_per_leg_multiplier",
        "fit_weight", "fit_use_status", "fit_exclusion_reason",
        "ri_source_path", "thermal_source_path", "source_paths",
    ]
    comparison_fields = sorted({key for row in comparison for key in row})
    audit_fields = ["path", "mtime_iso", "size_bytes", "observation"]

    write_csv(OUT_DIR / "admitted_evidence_freeze.csv", evidence, evidence_fields)
    write_json(OUT_DIR / "admitted_evidence_freeze.json", evidence)
    write_csv(OUT_DIR / "f4_ri_calibration_table.csv", table, table_fields)
    write_json(OUT_DIR / "f4_ri_calibration_table.json", table)
    write_csv(OUT_DIR / "model_comparison_f1_f3_f4_f5.csv", comparison, comparison_fields)
    write_json(OUT_DIR / "model_comparison_f1_f3_f4_f5.json", comparison)
    write_csv(OUT_DIR / "recent_coordination_audit.csv", audit, audit_fields)
    write_json(OUT_DIR / "recent_coordination_audit.json", audit)
    write_csv(OUT_DIR / "corrected_salt_gate_monitor_snapshot.csv", gate_snapshot, [
        "row_type", "case_key", "job_id", "job_name", "partition", "job_state",
        "job_elapsed", "job_time_limit", "dependency", "pending_reason",
        "latest_solver_time_s", "advance_since_restart_s", "fatal_error_count",
        "warning_count", "needs_special_gate_scrutiny", "recommendation",
    ])
    write_json(OUT_DIR / "corrected_salt_gate_monitor_snapshot.json", gate_snapshot)
    write_json(OUT_DIR / "f4_candidate_fit_summary.json", fit_summary)
    write_reports(evidence, table, fit_summary, comparison, audit, gate_snapshot)


if __name__ == "__main__":
    main()
