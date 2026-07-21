#!/usr/bin/env python3
"""Build a compact thermal control-volume admission review.

This report consumes the July 9 canonical observation table and compresses the
physical-interface thermal evidence into review rows. It does not promote any
thermal target into a fit row; it makes the validation-only admission reasons
easy to cite.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OBS = ROOT / "work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/closure_observations.csv"
OUT = ROOT / "work_products/2026-07/2026-07-09/2026-07-09_thermal_control_volume_admission_review"

SAMPLE_SOURCE_SUFFIX = "2026-07-09_thermal_openfoam_interface_sampling/combined_openfoam_interface_samples.csv"
RESIDUAL_SOURCE_SUFFIX = "2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/patchwise_heat_ledger_enthalpy_interfaces.csv"

CV_CLASS_MAP = {
    "heater": "heater",
    "heater_interior": "heater",
    "cooler": "cooler_reducer",
    "cooler_reducer": "cooler_reducer",
    "cooler_reducer_interior": "cooler_reducer",
    "junction": "junction",
    "junction_other": "junction",
    "lower_left_junction": "junction",
    "lower_right_junction": "junction",
    "upper_left_junction": "junction",
    "upper_right_junction": "junction",
    "test_section_lower_junction": "junction",
    "test_section_upper_junction": "junction",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
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


def finite(value: Any) -> bool:
    if value is None or value == "":
        return False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number)


def fnum(value: Any) -> float:
    return float(value) if finite(value) else 0.0


def cv_class(row: dict[str, str]) -> str:
    for key in (row.get("control_volume_group", ""), row.get("control_volume", ""), row.get("span", "")):
        if key in CV_CLASS_MAP:
            return CV_CLASS_MAP[key]
    return row.get("control_volume_group") or row.get("control_volume") or "other"


def admission_verdict(
    *,
    recirculation_flag: str,
    bracket_statuses: set[str],
    residual_statuses: set[str],
    radiation_present_rows: int,
    has_residual: bool,
) -> tuple[str, str]:
    if radiation_present_rows:
        return "validation_only_radiation_output_present_review_required", "qr/radiation output present requires separate accounting"
    if recirculation_flag == "yes":
        return "validation_only_recirc_contaminated", "recirculation/backflow contaminates at least one interface"
    if any("not_bracketed" in status for status in bracket_statuses):
        return "validation_only_not_bracketed", "available physical interfaces do not bracket the control volume"
    if not has_residual:
        return "validation_only_sampled_interface_no_residual", "OpenFOAM planes sampled, but no enthalpy residual row is assigned to this control-volume class"
    if any("partial" in status for status in residual_statuses | bracket_statuses):
        return "validation_only_partial_bracket", "residual exists but bracketing is partial"
    return "validation_only_defensible_cv_reviewed", "bracketed validation evidence; still not promoted to fit without reviewed control-volume method"


def sampled_interface_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if not row.get("source_path", "").endswith(SAMPLE_SOURCE_SUFFIX):
            continue
        key = (
            row["case_id"],
            row.get("control_volume", ""),
            row.get("control_volume_group", ""),
            row.get("span", ""),
        )
        groups[key].append(row)

    out: list[dict[str, Any]] = []
    for (case_id, control_volume, group, span), items in sorted(groups.items()):
        backflow = [fnum(row["value"]) for row in items if row.get("quantity") == "backflow_fraction" and finite(row.get("value"))]
        interfaces = sorted({row.get("interface_role", "") for row in items if row.get("interface_role", "")})
        directions = sorted({row.get("dominant_flow_direction", "") for row in items if row.get("dominant_flow_direction", "")})
        recirc = "yes" if any(row.get("recirculation_flag") == "yes" for row in items) else "no"
        radiation_present = sum(1 for row in items if row.get("radiation_present") == "yes")
        bracket_statuses = {row.get("physical_interface_bracket_status", "") for row in items}
        verdict, reason = admission_verdict(
            recirculation_flag=recirc,
            bracket_statuses=bracket_statuses,
            residual_statuses=set(),
            radiation_present_rows=radiation_present,
            has_residual=False,
        )
        out.append(
            {
                "case_id": case_id,
                "evidence_type": "openfoam_sampled_interface_planes",
                "control_volume": control_volume,
                "control_volume_group": group,
                "control_volume_class": cv_class(items[0]),
                "span": span,
                "sampled_interface_count": len(interfaces),
                "sampled_qoi_rows": len(items),
                "residual_qoi_rows": 0,
                "max_backflow_fraction": max(backflow) if backflow else "",
                "recirculation_flag": recirc,
                "radiation_present_rows": radiation_present,
                "radiation_output_terms": ";".join(sorted({row.get("radiation_output_term", "") for row in items if row.get("radiation_output_term", "")})),
                "bracket_statuses": ";".join(sorted(bracket_statuses)),
                "residual_statuses": "",
                "residual_assignment": "",
                "mean_abs_residual_W": "",
                "max_abs_residual_fraction": "",
                "temperature_selection_rules": ";".join(sorted({row.get("interface_temperature_selection_rule", "") for row in items if row.get("interface_temperature_selection_rule", "")})),
                "dominant_flow_directions": ";".join(directions),
                "interface_roles": ";".join(interfaces),
                "admission_verdict": verdict,
                "admission_reason": reason,
                "fit_eligible": "no",
                "validation_eligible": "yes",
                "source_paths": SAMPLE_SOURCE_SUFFIX,
            }
        )
    return out


def residual_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if not row.get("source_path", "").endswith(RESIDUAL_SOURCE_SUFFIX):
            continue
        key = (
            row["case_id"],
            row.get("control_volume", ""),
            row.get("control_volume_group", ""),
            row.get("span", ""),
        )
        groups[key].append(row)

    out: list[dict[str, Any]] = []
    for (case_id, control_volume, group, span), items in sorted(groups.items()):
        residual_w = [abs(fnum(row["value"])) for row in items if row.get("quantity") == "wallHeatFlux_vs_enthalpy_residual_W" and finite(row.get("value"))]
        residual_fraction = [abs(fnum(row["value"])) for row in items if row.get("quantity") == "residual_fraction" and finite(row.get("value"))]
        backflow = [fnum(row.get("max_interface_recirc_ratio")) for row in items if finite(row.get("max_interface_recirc_ratio"))]
        recirc = "yes" if any(row.get("recirculation_flag") == "yes" for row in items) else "no"
        radiation_present = sum(1 for row in items if row.get("radiation_present") == "yes")
        bracket_statuses = {row.get("physical_interface_bracket_status", "") for row in items}
        residual_statuses = {row.get("thermal_residual_status", "") for row in items}
        verdict, reason = admission_verdict(
            recirculation_flag=recirc,
            bracket_statuses=bracket_statuses,
            residual_statuses=residual_statuses,
            radiation_present_rows=radiation_present,
            has_residual=bool(residual_w or residual_fraction),
        )
        out.append(
            {
                "case_id": case_id,
                "evidence_type": "physical_interface_enthalpy_residual",
                "control_volume": control_volume,
                "control_volume_group": group,
                "control_volume_class": cv_class(items[0]),
                "span": span,
                "sampled_interface_count": 0,
                "sampled_qoi_rows": 0,
                "residual_qoi_rows": len(items),
                "max_backflow_fraction": max(backflow) if backflow else "",
                "recirculation_flag": recirc,
                "radiation_present_rows": radiation_present,
                "radiation_output_terms": ";".join(sorted({row.get("radiation_output_term", "") for row in items if row.get("radiation_output_term", "")})),
                "bracket_statuses": ";".join(sorted(bracket_statuses)),
                "residual_statuses": ";".join(sorted(residual_statuses)),
                "residual_assignment": ";".join(sorted({row.get("thermal_residual_assignment", "") for row in items if row.get("thermal_residual_assignment", "")})),
                "mean_abs_residual_W": sum(residual_w) / len(residual_w) if residual_w else "",
                "max_abs_residual_fraction": max(residual_fraction) if residual_fraction else "",
                "temperature_selection_rules": ";".join(sorted({row.get("interface_temperature_selection_rule", "") for row in items if row.get("interface_temperature_selection_rule", "")})),
                "dominant_flow_directions": "",
                "interface_roles": "",
                "admission_verdict": verdict,
                "admission_reason": reason,
                "fit_eligible": "no",
                "validation_eligible": "yes",
                "source_paths": RESIDUAL_SOURCE_SUFFIX,
            }
        )
    return out


def thesis_evidence_rows(detail_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in detail_rows:
        if row["control_volume_class"] not in {"heater", "cooler_reducer", "junction"}:
            continue
        groups[(row["case_id"], row["control_volume_class"])].append(row)

    out: list[dict[str, Any]] = []
    for (case_id, cvclass), items in sorted(groups.items()):
        verdict_counts = Counter(row["admission_verdict"] for row in items)
        recirc = "yes" if any(row["recirculation_flag"] == "yes" for row in items) else "no"
        radiation_rows = sum(int(row["radiation_present_rows"]) for row in items if row["radiation_present_rows"] != "")
        max_backflows = [fnum(row["max_backflow_fraction"]) for row in items if finite(row["max_backflow_fraction"])]
        residuals = [fnum(row["mean_abs_residual_W"]) for row in items if finite(row["mean_abs_residual_W"])]
        fractions = [fnum(row["max_abs_residual_fraction"]) for row in items if finite(row["max_abs_residual_fraction"])]
        if recirc == "yes":
            overall = "validation_only_recirc_contaminated"
        elif any("not_bracketed" in row["admission_verdict"] for row in items):
            overall = "validation_only_not_bracketed"
        elif any("partial" in row["admission_verdict"] for row in items):
            overall = "validation_only_partial_bracket"
        else:
            overall = "validation_only_defensible_cv_reviewed"
        out.append(
            {
                "case_id": case_id,
                "control_volume_class": cvclass,
                "detail_row_count": len(items),
                "openfoam_sampled_detail_rows": sum(1 for row in items if row["evidence_type"] == "openfoam_sampled_interface_planes"),
                "enthalpy_residual_detail_rows": sum(1 for row in items if row["evidence_type"] == "physical_interface_enthalpy_residual"),
                "max_backflow_fraction": max(max_backflows) if max_backflows else "",
                "mean_abs_residual_W": sum(residuals) / len(residuals) if residuals else "",
                "max_abs_residual_fraction": max(fractions) if fractions else "",
                "recirculation_flag": recirc,
                "radiation_present_rows": radiation_rows,
                "overall_admission": overall,
                "verdict_counts": ";".join(f"{key}={value}" for key, value in sorted(verdict_counts.items())),
                "fit_eligible": "no",
                "validation_eligible": "yes",
                "thesis_use": "thermal_validation_evidence_only",
            }
        )
    return out


def write_readme(detail: list[dict[str, Any]], thesis: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    verdict_counts = Counter(row["admission_verdict"] for row in detail)
    text = f"""# Thermal Control-Volume Admission Review

Generated: `{datetime.now().isoformat(timespec='seconds')}`

## Scope

This package compresses the July 9 canonical observation table into
thermal-control-volume admission rows. It is a review/index package, not a new
OpenFOAM extraction and not a fit promotion.

## Outputs

- `thermal_control_volume_admission.csv`: detailed evidence rows from sampled
  OpenFOAM planes and physical-interface enthalpy residuals.
- `thermal_thesis_evidence_table.csv`: compact case/control-volume-class table
  suitable for thesis validation notes.
- `summary.json`: counts and source paths.

## Counts

- Detail rows: `{len(detail)}`
- Thesis evidence rows: `{len(thesis)}`
- Admission verdicts: `{dict(sorted(verdict_counts.items()))}`
- Recirculation-contaminated detail rows: `{summary['recirculation_detail_rows']}`
- Radiation-present detail rows: `{summary['radiation_present_detail_rows']}`

## Interpretation

All rows remain `fit_eligible=no`. Heater and cooler/reducer rows are usable as
thermal validation evidence where bracketing is explicit, but recirculation,
partial bracketing, and missing model-specific thermal predictions prevent fit
promotion. Junction evidence is mostly sampled-interface diagnostics unless
separate residual assignment exists.

Radiation remains absent in the current OpenFOAM outputs; this package carries
no inferred radiation term.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    obs_rows = read_csv(OBS)
    detail = sampled_interface_rows(obs_rows) + residual_rows(obs_rows)
    thesis = thesis_evidence_rows(detail)
    detail.sort(key=lambda row: (row["case_id"], row["control_volume_class"], row["evidence_type"], row["control_volume"], row["span"]))
    thesis.sort(key=lambda row: (row["case_id"], row["control_volume_class"]))
    detail_fields = [
        "case_id",
        "evidence_type",
        "control_volume",
        "control_volume_group",
        "control_volume_class",
        "span",
        "sampled_interface_count",
        "sampled_qoi_rows",
        "residual_qoi_rows",
        "max_backflow_fraction",
        "recirculation_flag",
        "radiation_present_rows",
        "radiation_output_terms",
        "bracket_statuses",
        "residual_statuses",
        "residual_assignment",
        "mean_abs_residual_W",
        "max_abs_residual_fraction",
        "temperature_selection_rules",
        "dominant_flow_directions",
        "interface_roles",
        "admission_verdict",
        "admission_reason",
        "fit_eligible",
        "validation_eligible",
        "source_paths",
    ]
    thesis_fields = [
        "case_id",
        "control_volume_class",
        "detail_row_count",
        "openfoam_sampled_detail_rows",
        "enthalpy_residual_detail_rows",
        "max_backflow_fraction",
        "mean_abs_residual_W",
        "max_abs_residual_fraction",
        "recirculation_flag",
        "radiation_present_rows",
        "overall_admission",
        "verdict_counts",
        "fit_eligible",
        "validation_eligible",
        "thesis_use",
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "thermal_control_volume_admission.csv", detail, detail_fields)
    write_csv(OUT / "thermal_thesis_evidence_table.csv", thesis, thesis_fields)
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task": "AGENT-247",
        "source_observation_table": rel(OBS),
        "detail_rows": len(detail),
        "thesis_evidence_rows": len(thesis),
        "admission_verdict_counts": dict(sorted(Counter(row["admission_verdict"] for row in detail).items())),
        "overall_admission_counts": dict(sorted(Counter(row["overall_admission"] for row in thesis).items())),
        "recirculation_detail_rows": sum(1 for row in detail if row["recirculation_flag"] == "yes"),
        "radiation_present_detail_rows": sum(1 for row in detail if int(row["radiation_present_rows"] or 0) > 0),
        "fit_eligible_detail_rows": sum(1 for row in detail if row["fit_eligible"] == "yes"),
        "outputs": [
            "thermal_control_volume_admission.csv",
            "thermal_thesis_evidence_table.csv",
            "README.md",
            "summary.json",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_readme(detail, thesis, summary)
    return summary


def main() -> int:
    summary = build()
    print(json.dumps({"output_dir": rel(OUT), "detail_rows": summary["detail_rows"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
