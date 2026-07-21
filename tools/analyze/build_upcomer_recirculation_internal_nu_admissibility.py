#!/usr/bin/env python3
"""Build the upcomer recirculation/internal-Nu admissibility package."""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility"

ONSET_STATUS = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_onset_blocker_resolution/upcomer_onset_evidence_status.csv"
PRIOR_ONSET = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_upcomer_onset/upcomer_onset_regime_table.csv"
UPCOMER_DATASET = ROOT / "work_products/2026-07/2026-07-07/2026-07-07_upcomer_correlation_v2/upcomer_dataset.csv"
VALIDITY = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_litrev_cfd_validity_diagnostics/cfd_single_stream_validity.csv"
NAMING = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_litrev_cfd_validity_diagnostics/coefficient_naming_limits.csv"
THERMAL_GATE = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate/thermal_admission_internal_nu_final_gate.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def case_id_from_label(label: str) -> str:
    parts = label.split("_")
    if len(parts) >= 2 and parts[0] == "salt":
        return "_".join(parts[:2])
    return label


def by_key(rows: Iterable[dict[str, str]], *keys: str) -> dict[tuple[str, ...], dict[str, str]]:
    return {tuple(row[key] for key in keys): row for row in rows}


def validity_for_case(rows: list[dict[str, str]], case_id: str) -> dict[str, str]:
    for section in ("left_upper_leg", "upper_leg"):
        for row in rows:
            if row["case_id"] == case_id and row["section"] == section:
                return row
    return {}


def source_paths(*paths: Path) -> str:
    return ";".join(rel(path) for path in paths)


def build_onset_rows() -> list[dict[str, Any]]:
    onset = read_csv(ONSET_STATUS)
    prior = by_key(read_csv(PRIOR_ONSET), "label")
    dataset = by_key(read_csv(UPCOMER_DATASET), "label")
    validity = read_csv(VALIDITY)
    thermal_gate = read_csv(THERMAL_GATE)
    upcomer_nu_gate = next(row for row in thermal_gate if row["segment"] == "upcomer" and row["qoi"] == "Nu")

    rows: list[dict[str, Any]] = []
    for raw in onset:
        case_id = case_id_from_label(raw["label"])
        prior_row = prior.get((raw["label"],), {})
        dataset_row = dataset.get((raw["label"],), {})
        validity_row = validity_for_case(validity, case_id)
        recirc_observed = "yes" if raw["regime_class"] == "recirculation_cell_observed" else "no"
        reverse_area = validity_row.get("reverse_flow_area_fraction", "")
        reverse_mass = validity_row.get("reverse_mass_fraction", "")
        flow_evidence = (
            "backflow_fraction=%s; Ri_median=%s; validity_section=%s; reverse_flow_area_fraction=%s"
            % (
                raw["backflow_fraction"],
                raw["Ri_median"],
                validity_row.get("section", "not_available"),
                reverse_area or "not_available",
            )
        )
        correlation = (
            "Across admitted Salt2-4 evidence, backflow fraction and recirculation intensity decrease as Re rises, "
            "but all rows remain recirculating with Ri_median>1 and no non-recirculating anchor; Pr decreases while Ra/Gr rise, "
            "so onset cannot be separated by one nondimensional group today."
        )
        blockers = [
            "ordinary_pipe_anchor_points",
            "direct_wall_bulk_delta_T",
            "Gz",
            "secondary_velocity_fraction",
            "mesh_GCI",
            "terminal_corrected_Q_admission",
            "source_time_window_metadata",
        ]
        rows.append(
            {
                "case_id": case_id,
                "label": raw["label"],
                "source_id": raw["source_id"],
                "admission_group": "admitted_CFD_diagnostic_not_fit",
                "branch": "left_upcomer",
                "section": "upcomer",
                "mesh_level": "coarse_no_publication_gci",
                "time_window": prior_row.get("time_window", "") or "not_in_source_table",
                "heating_cooling_orientation": "opposed wallHeatFlux/enthalpy direction in thermal gate; Nu is positive diagnostic only",
                "flow_direction_evidence": flow_evidence,
                "recirculation_observed": recirc_observed,
                "Re_upcomer": raw["Re_upcomer"],
                "Re_section_median": raw["Re_section_median"],
                "Pr_median": raw["Pr_median"],
                "Ra_median": raw["Ra_median"],
                "Gr_proxy_from_Ra_Pr": raw["Gr_proxy_from_Ra_Pr"],
                "Ri_median": raw["Ri_median"],
                "Gz_available": "no",
                "Gz": "",
                "wall_bulk_delta_T_K": prior_row.get("wall_bulk_delta_T_K", ""),
                "wall_bulk_delta_T_status": "missing_direct_wall_core_delta_T",
                "backflow_fraction": raw["backflow_fraction"],
                "reverse_flow_area_fraction": reverse_area,
                "reverse_mass_fraction": reverse_mass,
                "secondary_velocity_fraction": validity_row.get("secondary_velocity_fraction", ""),
                "recirculation_intensity": raw["recirculation_intensity"],
                "Nu_upcomer": raw["Nu_upcomer"],
                "htc_wm2k": dataset_row.get("htc_wm2k", ""),
                "T_bulk_K": raw["T_bulk_K"],
                "u_bulk_m_s": raw["u_bulk_m_s"],
                "regime_class": raw["regime_class"],
                "correlation_statement": correlation,
                "coefficient_label_rule": "single_stream_Nu_f_D_K_invalid_use_section_effective_or_diagnostic",
                "internal_nu_fit_admissible": "no",
                "admissibility_decision": "validation_only_diagnostic_not_fit",
                "blocked_missing_metrics": ";".join(blockers),
                "thermal_gate_forward_use": upcomer_nu_gate["forward_v1_use"],
                "source_paths": source_paths(ONSET_STATUS, PRIOR_ONSET, UPCOMER_DATASET, VALIDITY, THERMAL_GATE),
            }
        )
    return rows


def build_naming_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    trigger = "backflow_fraction>=0.10 or Ri_median>=1 or reverse_flow_area_fraction>0 or recirculation_zone_flag=yes"
    for family in ("Nu", "f_D", "K"):
        rows.append(
            {
                "scope": "general_upcomer_recirculation_rule",
                "case_id": "any",
                "section": "upcomer",
                "coefficient_family": family,
                "allowed_label": f"{family}_section_effective_upcomer_diagnostic",
                "rejected_labels": f"universal_{family};transferable_{family};fit_{family}_internal_closure",
                "rule_status": "reject_universal_name",
                "trigger_conditions": trigger,
                "admitted_use": "diagnostic_validation_only",
                "excluded_use": "fit_closure_or_forward_runtime_residual_absorption",
                "source_path": source_paths(ONSET_STATUS, VALIDITY, NAMING, THERMAL_GATE),
            }
        )

    for row in read_csv(NAMING):
        if row["section"] not in {"left_upper_leg", "upper_leg"}:
            continue
        if row["naming_status"] != "reject_universal_name":
            continue
        rows.append(
            {
                "scope": "case_specific_source_rule",
                "case_id": row["case_id"],
                "section": row["section"],
                "coefficient_family": row["coefficient_family"],
                "allowed_label": row["allowed_name"],
                "rejected_labels": row["rejected_names"],
                "rule_status": row["naming_status"],
                "trigger_conditions": row["reason"],
                "admitted_use": "section_effective_diagnostic_or_validation_only",
                "excluded_use": "universal_or_transferable_single_stream_label",
                "source_path": rel(NAMING),
            }
        )
    return rows


def build_blocked_metrics_rows() -> list[dict[str, str]]:
    return [
        {
            "blocked_metric": "ordinary_pipe_anchor_points",
            "current_status": "missing",
            "why_it_matters": "All admitted rows are already recirculating, so no onset threshold or ordinary-pipe side can be calibrated.",
            "next_extraction_request": "Add admitted/candidate cases near Re 150, 200, 250 and at least one higher-Re non-recirculating or transition anchor if physically present.",
        },
        {
            "blocked_metric": "direct_wall_bulk_delta_T",
            "current_status": "missing",
            "why_it_matters": "Nu/HTC labels need a defensible thermal driving temperature and cannot absorb wall storage, branch mixing, radiation, or sign residuals.",
            "next_extraction_request": "Export mass-flux-weighted bulk temperature and area-weighted wall temperature at upcomer inlet/mid/outlet planes over the same time window.",
        },
        {
            "blocked_metric": "Gz",
            "current_status": "missing",
            "why_it_matters": "Developing-flow thermal entry length cannot be assessed without a Graetz number or equivalent streamwise thermal-development metric.",
            "next_extraction_request": "Compute Gz from Re, Pr, hydraulic diameter, and section length for every upcomer evidence row.",
        },
        {
            "blocked_metric": "secondary_velocity_fraction",
            "current_status": "missing",
            "why_it_matters": "Reverse-flow proxies show recirculation but do not fully quantify cross-stream mixing or single-stream invalidity strength.",
            "next_extraction_request": "Add vector-plane extraction for reverse area fraction, reverse mass fraction, and secondary velocity fraction on matched upcomer planes.",
        },
        {
            "blocked_metric": "mesh_GCI",
            "current_status": "missing",
            "why_it_matters": "The current evidence is coarse/no-publication-GCI, so it is diagnostic rather than fit-admissible.",
            "next_extraction_request": "Repeat the recirculation metrics on mesh-family cases before any closure-fit admission.",
        },
    ]


def write_source_manifest() -> None:
    rows = [
        {"path": rel(ONSET_STATUS), "role": "primary admitted/candidate recirculation evidence"},
        {"path": rel(PRIOR_ONSET), "role": "prior onset table and missing wall-bulk delta T status"},
        {"path": rel(UPCOMER_DATASET), "role": "upcomer HTC and nondimensional source dataset"},
        {"path": rel(VALIDITY), "role": "single-stream validity and reverse-flow proxy evidence"},
        {"path": rel(NAMING), "role": "case-specific coefficient naming source rules"},
        {"path": rel(THERMAL_GATE), "role": "thermal/internal-Nu final admission gate"},
    ]
    write_csv(OUT / "source_manifest.csv", rows, ["path", "role"])


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""# Upcomer Recirculation And Internal-Nu Admissibility

Date: 2026-07-14

Task: AGENT-330

## Decision

No internal Nu row is fit-admissible today. The admitted Salt2-4 upcomer evidence is useful as a physics/admission diagnostic, but every current row remains in a recirculating regime and the thermal gate forbids internal Nu from absorbing heater, cooler, passive loss, wall storage, branch mixing, radiation, or sign residuals.

## Observed Facts

- Admitted diagnostic cases span Re_upcomer {summary['re_min']:.3f}-{summary['re_max']:.3f}; all {summary['n_onset_rows']} rows are classified as recirculation_cell_observed.
- Backflow fraction decreases with Re across Salt2-4, from {summary['backflow_max']:.6f} to {summary['backflow_min']:.6f}, but it does not approach zero in the admitted evidence.
- Ri_median remains above one in all rows, from {summary['ri_min']:.6f} to {summary['ri_max']:.6f}.
- Pr decreases while Ra/Gr increase across the same monotone case sequence. With only three recirculating points and no ordinary-pipe anchor, those correlations are not separable into a threshold law.
- Direct wall-bulk or wall-core Delta T and Gz are not present in the upcomer onset source tables. They are carried as blocked metrics, not inferred.
- The lit-review CFD validity package marks left_upper_leg and upper_leg coefficient names as section-effective only under reverse/recirculation proxies.
- CFD rcExternalTemperature wallHeatFlux includes radiation where that boundary condition is used; there is no separate exported qr term to add to an internal-Nu residual.

## Interpretation

Upcomer recirculation is now an admission rule: when backflow_fraction >= 0.10, Ri_median >= 1, reverse-flow area/mass is material, or recirculation_zone_flag is yes, single-stream `Nu`, `f_D`, and `K` labels are invalid. Use section-effective or diagnostic names and keep those rows out of closure fitting.

Current correlations are qualitative only: higher Re coincides with lower backflow fraction and lower recirculation intensity over Salt2-4, while the entire observed range remains recirculating. That supports a recirculation caveat and naming rule, not a calibrated onset threshold or a transferable internal-Nu closure.

## Blocked Missing Metrics

- Ordinary-pipe or transition anchors bracketing the onset.
- Direct upcomer wall-bulk or wall-core Delta T over the same time window as the flow metrics.
- Gz or equivalent thermal-development metric.
- Secondary velocity fraction and plane-resolved reverse mass/area fractions.
- Mesh/time uncertainty for the recirculation diagnostics.
- Terminal corrected-Q admission for any candidate cases used beyond diagnostic screening.

## Next Extraction Request

Extract matched vector and thermal planes at upcomer inlet, midpoint, and outlet for each admitted/candidate case: reverse area fraction, reverse mass fraction, secondary velocity fraction, mass-flux-weighted bulk temperature, area-weighted wall temperature, local wallHeatFlux, Re, Pr, Ri, Ra/Gr, Gz, and the exact time window. Add cases near Re 150, 200, and 250, plus a non-recirculating or transition anchor if available, before any internal-Nu fit gate is reopened.

## Outputs

- `upcomer_recirculation_onset_conditions.csv`
- `coefficient_naming_rules_for_recirculation.csv`
- `blocked_missing_metrics.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    onset_rows = build_onset_rows()
    naming_rows = build_naming_rows()
    blocked_rows = build_blocked_metrics_rows()
    write_csv(
        OUT / "upcomer_recirculation_onset_conditions.csv",
        onset_rows,
        [
            "case_id",
            "label",
            "source_id",
            "admission_group",
            "branch",
            "section",
            "mesh_level",
            "time_window",
            "heating_cooling_orientation",
            "flow_direction_evidence",
            "recirculation_observed",
            "Re_upcomer",
            "Re_section_median",
            "Pr_median",
            "Ra_median",
            "Gr_proxy_from_Ra_Pr",
            "Ri_median",
            "Gz_available",
            "Gz",
            "wall_bulk_delta_T_K",
            "wall_bulk_delta_T_status",
            "backflow_fraction",
            "reverse_flow_area_fraction",
            "reverse_mass_fraction",
            "secondary_velocity_fraction",
            "recirculation_intensity",
            "Nu_upcomer",
            "htc_wm2k",
            "T_bulk_K",
            "u_bulk_m_s",
            "regime_class",
            "correlation_statement",
            "coefficient_label_rule",
            "internal_nu_fit_admissible",
            "admissibility_decision",
            "blocked_missing_metrics",
            "thermal_gate_forward_use",
            "source_paths",
        ],
    )
    write_csv(
        OUT / "coefficient_naming_rules_for_recirculation.csv",
        naming_rows,
        [
            "scope",
            "case_id",
            "section",
            "coefficient_family",
            "allowed_label",
            "rejected_labels",
            "rule_status",
            "trigger_conditions",
            "admitted_use",
            "excluded_use",
            "source_path",
        ],
    )
    write_csv(
        OUT / "blocked_missing_metrics.csv",
        blocked_rows,
        ["blocked_metric", "current_status", "why_it_matters", "next_extraction_request"],
    )
    write_source_manifest()

    re_vals = [float(row["Re_upcomer"]) for row in onset_rows]
    bf_vals = [float(row["backflow_fraction"]) for row in onset_rows]
    ri_vals = [float(row["Ri_median"]) for row in onset_rows]
    summary = {
        "task": "AGENT-330",
        "status": "complete",
        "decision": "no_internal_Nu_fit_admissible_today",
        "n_onset_rows": len(onset_rows),
        "n_naming_rows": len(naming_rows),
        "re_min": min(re_vals),
        "re_max": max(re_vals),
        "backflow_min": min(bf_vals),
        "backflow_max": max(bf_vals),
        "ri_min": min(ri_vals),
        "ri_max": max(ri_vals),
        "recirculation_rule": "single-stream Nu/f_D/K invalid under material backflow, Ri>=1, reverse-flow proxy, or recirculation flag",
        "fit_admissible_internal_nu_rows": 0,
        "outputs": [
            "upcomer_recirculation_onset_conditions.csv",
            "coefficient_naming_rules_for_recirculation.csv",
            "blocked_missing_metrics.csv",
            "source_manifest.csv",
            "README.md",
            "summary.json",
        ],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    write_readme(summary)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
