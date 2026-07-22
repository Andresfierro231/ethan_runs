#!/usr/bin/env python3
"""Build nondimensional regime map and fail-closed closure eligibility package."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "TODO-1D-REGIME-MAP-NONDIMENSIONAL-CLOSURE-ELIGIBILITY-2026-07-22"
SLUG = "1d_regime_map_nondimensional_closure_eligibility"
DATE = "2026-07-22"
OUTDIR = Path("work_products/2026-07/2026-07-22/2026-07-22_1d_regime_map_nondimensional_closure_eligibility")

GSSB = Path("work_products/2026-07/2026-07-21/2026-07-21_litrev_gated_single_stream_developing_branch/single_stream_developing_branch_gate.csv")
SOURCE_INVENTORY = Path("work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/litrev_source_inventory.csv")
MODEL_FORMS = Path("work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/model_form_candidates.csv")
CFD_CONTRACT = Path("work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/cfd_postprocessing_contract.csv")

SOURCE_PATHS = [
    "work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/README.md",
    str(SOURCE_INVENTORY),
    str(MODEL_FORMS),
    str(CFD_CONTRACT),
    str(GSSB),
    "work_products/2026-07/2026-07-21/2026-07-21_litrev_throughflow_recirc_exchange_cell/README.md",
    "work_products/2026-07/2026-07-22/2026-07-22_mf07_entrance_development_and_reset_source_basis/README.md",
    "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis/README.md",
    "work_products/2026-07/2026-07-22/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract/README.md",
    "work_products/2026-07/2026-07-22/2026-07-22_1d_setup_only_bc_uq_propagation/README.md",
]


@dataclass(frozen=True)
class Table:
    filename: str
    rows: list[dict[str, str]]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_csv(path: Path) -> list[dict[str, str]]:
    with (repo_root() / path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError(f"{path.name} has no rows")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fnum(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt_range(values: list[float]) -> str:
    if not values:
        return ""
    return f"{min(values):.6g} to {max(values):.6g}"


def source_manifest(root: Path) -> list[dict[str, str]]:
    return [
        {
            "source_id": f"SRC-{idx:02d}",
            "path": rel,
            "exists": str((root / rel).exists()).lower(),
            "used_as": "read_only_regime_or_litrev_context",
            "mutation_status": "not_modified_by_this_task",
        }
        for idx, rel in enumerate(SOURCE_PATHS, 1)
    ]


def formula_validity_table() -> list[dict[str, str]]:
    return [
        {
            "formula_id": "F01",
            "quantity": "Reynolds number",
            "symbolic_form": "Re = rho U D_h / mu",
            "source_or_author_title": "Shah and London; Shah hydrodynamic entry correlation",
            "validity_or_use": "flow-regime coordinate and source-envelope overlap check",
            "tamu_use": "diagnostic coordinate; not coefficient admission",
            "failure_rule": "missing property mode or velocity basis blocks closure eligibility",
        },
        {
            "formula_id": "F02",
            "quantity": "Prandtl number",
            "symbolic_form": "Pr = cp mu / k",
            "source_or_author_title": "Muzychka and Yovanovich combined-entry heat transfer and developing friction",
            "validity_or_use": "thermal-property coordinate for developing heat transfer",
            "tamu_use": "diagnostic coordinate with property-mode label",
            "failure_rule": "blank property/source labels block admission",
        },
        {
            "formula_id": "F03",
            "quantity": "Grashof number",
            "symbolic_form": "Gr = g beta DeltaT D_h^3 / nu^2",
            "source_or_author_title": "Everts and Meyer/Mahdavi developing and mixed-convection entrance studies",
            "validity_or_use": "buoyancy coordinate requiring orientation and temperature-drive provenance",
            "tamu_use": "mixed-convection screen only",
            "failure_rule": "missing wall-bulk drive or source status blocks active mixed-convection closure",
        },
        {
            "formula_id": "F04",
            "quantity": "Rayleigh number",
            "symbolic_form": "Ra = Gr Pr",
            "source_or_author_title": "Everts and Meyer/Mahdavi developing and mixed-convection entrance studies",
            "validity_or_use": "combined buoyancy/thermal diffusivity coordinate",
            "tamu_use": "diagnostic regime coordinate",
            "failure_rule": "not a threshold source for TAMU without calibration",
        },
        {
            "formula_id": "F05",
            "quantity": "Richardson number",
            "symbolic_form": "Ri = Gr / Re^2",
            "source_or_author_title": "Everts and Meyer/Mahdavi developing and mixed-convection entrance studies",
            "validity_or_use": "mixed-convection and buoyancy-importance coordinate",
            "tamu_use": "invalid-single-stream caution when large, not a universal switch",
            "failure_rule": "do not admit thresholds without TAMU envelope and same-QOI UQ",
        },
        {
            "formula_id": "F06",
            "quantity": "Graetz number",
            "symbolic_form": "Gz = Re Pr D_h / x_from_thermal_reset",
            "source_or_author_title": "Muzychka and Yovanovich; Shah/London developing-flow framework",
            "validity_or_use": "thermal entrance/development coordinate",
            "tamu_use": "bulk-to-TP promise screen and reset/development context",
            "failure_rule": "thermal reset/source basis missing keeps row diagnostic",
        },
        {
            "formula_id": "F07",
            "quantity": "reverse area fraction",
            "symbolic_form": "F_A = area(u_n < 0) / total area",
            "source_or_author_title": "Patino-Jaramillo, Iglesias, Vera planar tee flow fields and recirculation maps",
            "validity_or_use": "recirculation diagnostic, not universal threshold",
            "tamu_use": "ordinary single-stream rejection support",
            "failure_rule": "persistent reverse area blocks ordinary Nu/f_D/K/F6 admission",
        },
        {
            "formula_id": "F08",
            "quantity": "reverse mass fraction",
            "symbolic_form": "F_m = reverse absolute mass flow / total absolute mass flow",
            "source_or_author_title": "LitRev CFD postprocessing contract; recirculation diagnostics",
            "validity_or_use": "same-window recirculation diagnostic",
            "tamu_use": "ordinary single-stream rejection support",
            "failure_rule": "same-window field missing blocks coefficient eligibility",
        },
    ]


def regime_rows() -> list[dict[str, str]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(GSSB):
        groups[(row["case_id"], row["span"])].append(row)

    out: list[dict[str, str]] = []
    for (case_id, span), rows in sorted(groups.items()):
        nums = {name: [v for v in (fnum(r.get(name, "")) for r in rows) if v is not None] for name in ("Re", "Pr", "Gr", "Ri", "Ra", "Gz", "hydraulic_reset_distance_m")}
        recirc_statuses = {r["reverse_flow_metric_status"] for r in rows}
        same_qoi_statuses = {r["same_qoi_uq_gate"] for r in rows}
        source_statuses = {r["source_envelope_status"] for r in rows}
        admissions = {r["coefficient_admission_status"] for r in rows}
        single_stream_allowed = {r["single_stream_developing_allowed"] for r in rows}
        reasons = sorted({part for r in rows for part in r["blocking_reasons"].split(";") if part})
        if "blocked_recirc_evidence_present" in recirc_statuses or "fail" in recirc_statuses:
            regime_class = "recirculation_or_invalid_single_stream"
        elif "unknown_or_pass_proxy" in recirc_statuses:
            regime_class = "possible_single_stream_precheck_only"
        else:
            regime_class = "uncertain_recirculation_basis"
        closure_eligibility = "diagnostic_only_no_coefficient_admission"
        if single_stream_allowed == {"precheck_only_not_admitted"}:
            closure_eligibility = "single_stream_precheck_only_not_admitted"
        if any("recirculation_invalid_single_stream" in reason for reason in reasons):
            closure_eligibility = "ordinary_single_stream_blocked_exchange_cell_diagnostic"
        out.append(
            {
                "case_id": case_id,
                "span": span,
                "row_count": str(len(rows)),
                "property_modes": ";".join(sorted({r["property_mode"] for r in rows})),
                "orientation": ";".join(sorted({r["orientation"] for r in rows})),
                "Re_range": fmt_range(nums["Re"]),
                "Pr_range": fmt_range(nums["Pr"]),
                "Gr_range": fmt_range(nums["Gr"]),
                "Ri_range": fmt_range(nums["Ri"]),
                "Ra_range": fmt_range(nums["Ra"]),
                "Gz_range": fmt_range(nums["Gz"]),
                "hydraulic_reset_distance_m_range": fmt_range(nums["hydraulic_reset_distance_m"]),
                "recirculation_statuses": ";".join(sorted(recirc_statuses)),
                "source_envelope_statuses": ";".join(sorted(source_statuses)),
                "same_qoi_uq_statuses": ";".join(sorted(same_qoi_statuses)),
                "regime_class": regime_class,
                "closure_eligibility": closure_eligibility,
                "coefficient_admission_statuses": ";".join(sorted(admissions)),
                "blocking_reasons": ";".join(reasons),
                "scientific_interpretation": "fail closed; use as regime evidence and model-form selector, not closure fit",
            }
        )
    return out


def tamu_overlap_matrix(regimes: list[dict[str, str]]) -> list[dict[str, str]]:
    source_rows = {row["source_key"]: row for row in read_csv(SOURCE_INVENTORY)}
    selected = [
        "ShahLondon1971_Shah1978",
        "MuzychkaYovanovich2004_2009",
        "EvertsMeyer2020_EvertsMahdavi2023",
        "PatinoJaramillo2022Flow",
        "PatinoJaramillo2022Coeff",
        "Delafosse_Tajsoleiman_exchange_sources",
        "NIST_TN2206",
    ]
    regime_summary = "; ".join(sorted({row["regime_class"] for row in regimes}))
    rows = []
    for key in selected:
        src = source_rows[key]
        rows.append(
            {
                "source_key": key,
                "author_title_or_source": src["author_title_or_source"],
                "source_use_category": src["source_use_category"],
                "source_fluid_geometry_regime": src["fluid_geometry_regime"],
                "required_ranges_or_metadata": src["required_ranges_or_metadata"],
                "tamu_regime_overlap": src["tamu_overlap"],
                "current_tamu_regime_summary": regime_summary,
                "eligibility_decision": "method_or_screening_only_fail_closed",
                "reason": src["failure_criterion"],
            }
        )
    return rows


def closure_eligibility_decisions(regimes: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "model_family": "ordinary_single_stream_developing_fD_Nu",
            "evidence_rows_reviewed": str(len(regimes)),
            "eligible_rows": str(sum(1 for r in regimes if r["closure_eligibility"] == "single_stream_precheck_only_not_admitted")),
            "admitted_rows": "0",
            "decision": "precheck_only_no_fit",
            "reason": "source envelope and same-QOI UQ remain missing; recirculation invalidates many spans",
            "next_gate": "branch-local same-QOI UQ plus source/property labels",
        },
        {
            "model_family": "throughflow_recirc_exchange_cell",
            "evidence_rows_reviewed": str(len(regimes)),
            "eligible_rows": str(sum(1 for r in regimes if "exchange_cell" in r["closure_eligibility"])),
            "admitted_rows": "0",
            "decision": "diagnostic_architecture_only",
            "reason": "S13 exchange evidence remains diagnostic; exact same-label mesh/GCI and source release are missing",
            "next_gate": "post-sampler same-label GCI production harvest gate",
        },
        {
            "model_family": "section_or_cluster_pressure_K",
            "evidence_rows_reviewed": str(len(regimes)),
            "eligible_rows": "0",
            "admitted_rows": "0",
            "decision": "pressure_basis_required_no_component_K",
            "reason": "pressure rises and corner rows need hydrostatic, kinetic, straight/developing, recovery, and residual decomposition",
            "next_gate": "low-recirculation F6/source recovery anchors after terminal evidence",
        },
        {
            "model_family": "signed_flow_junction_network",
            "evidence_rows_reviewed": str(len(regimes)),
            "eligible_rows": "0",
            "admitted_rows": "0",
            "decision": "not_current_primary_mode",
            "reason": "current evidence emphasizes local reverse area/mass with net throughflow, not admitted negative net branch flow",
            "next_gate": "signed path evidence only if topology shows discrete branch reversal",
        },
        {
            "model_family": "internal_Nu_fit",
            "evidence_rows_reviewed": str(len(regimes)),
            "eligible_rows": "0",
            "admitted_rows": "0",
            "decision": "closed_to_fitting",
            "reason": "heat residual, passive loss, radiation, storage, and recirculation owners are not separable enough for Nu admission",
            "next_gate": "conservative thermal ledger plus source-bounded release and same-QOI UQ",
        },
    ]


def no_mutation_guardrails() -> list[dict[str, str]]:
    return [
        {"guardrail": "native CFD/OpenFOAM outputs", "status": "not_mutated"},
        {"guardrail": "scheduler/solver/sampler", "status": "not_launched"},
        {"guardrail": "Fluid/external repositories", "status": "not_mutated"},
        {"guardrail": "registry/admission/blocker register", "status": "not_mutated"},
        {"guardrail": "fit/model selection/coefficient admission", "status": "not_performed"},
        {"guardrail": "source/property release", "status": "not_performed"},
    ]


def write_svg(path: Path, regimes: list[dict[str, str]]) -> None:
    cases = sorted({r["case_id"] for r in regimes})
    spans = sorted({r["span"] for r in regimes})
    cell_w, cell_h = 150, 34
    width = 180 + cell_w * len(cases)
    height = 80 + cell_h * len(spans)
    color = {
        "ordinary_single_stream_blocked_exchange_cell_diagnostic": "#c9483a",
        "single_stream_precheck_only_not_admitted": "#d6a12d",
        "diagnostic_only_no_coefficient_admission": "#8a8f98",
    }
    by_key = {(r["case_id"], r["span"]): r for r in regimes}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="20" y="28" font-family="Arial" font-size="18" font-weight="700">TAMU Nondimensional Regime Eligibility Map</text>',
        '<text x="20" y="50" font-family="Arial" font-size="12">Red: ordinary single-stream blocked; amber: precheck only; gray: diagnostic only. No coefficient admission.</text>',
    ]
    for i, case in enumerate(cases):
        parts.append(f'<text x="{180 + i*cell_w + 8}" y="76" font-family="Arial" font-size="12" font-weight="700">{case}</text>')
    for j, span in enumerate(spans):
        y = 86 + j * cell_h
        parts.append(f'<text x="20" y="{y + 22}" font-family="Arial" font-size="11">{span}</text>')
        for i, case in enumerate(cases):
            x = 180 + i * cell_w
            row = by_key.get((case, span))
            decision = row["closure_eligibility"] if row else "diagnostic_only_no_coefficient_admission"
            fill = color.get(decision, "#8a8f98")
            label = "blocked" if "blocked" in decision else ("precheck" if "precheck" in decision else "diagnostic")
            parts.append(f'<rect x="{x}" y="{y}" width="{cell_w-6}" height="{cell_h-6}" fill="{fill}" rx="3"/>')
            parts.append(f'<text x="{x+8}" y="{y+19}" font-family="Arial" font-size="11" fill="#ffffff">{label}</text>')
    parts.append("</svg>\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def validate(tables: list[Table], root: Path) -> list[str]:
    errors = []
    manifest = next(t.rows for t in tables if t.filename == "source_manifest.csv")
    for row in manifest:
        if row["exists"] != "true":
            errors.append(f"missing source: {row['path']}")
    decisions = next(t.rows for t in tables if t.filename == "closure_eligibility_decisions.csv")
    for row in decisions:
        if row["admitted_rows"] != "0":
            errors.append(f"unexpected admission: {row['model_family']}")
    formulas = next(t.rows for t in tables if t.filename == "formula_validity_table.csv")
    required = {"Reynolds number", "Prandtl number", "Grashof number", "Rayleigh number", "Richardson number", "Graetz number"}
    if not required.issubset({row["quantity"] for row in formulas}):
        errors.append("missing required nondimensional formula")
    regimes = next(t.rows for t in tables if t.filename == "segment_case_regime_map.csv")
    if not regimes:
        errors.append("empty regime map")
    if not (root / ".agent/BOARD.md").exists():
        errors.append("repo root sanity check failed")
    return errors


def readme_text(generated_at: str, counts: dict[str, int], decision: str) -> str:
    return f"""---
provenance:
  - {GSSB}
  - {SOURCE_INVENTORY}
  - {MODEL_FORMS}
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_throughflow_recirc_exchange_cell/README.md
tags: [predictive-1d, regime-map, nondimensional, closure-eligibility, no-admission]
related:
  - .agent/status/{DATE}_{TASK_ID}.md
  - .agent/journal/{DATE}/1d-regime-map-nondimensional-closure-eligibility.md
  - imports/{DATE}_{SLUG}.json
task: {TASK_ID}
date: {DATE}
role: Forward-pred / Hydraulics / Thermal-modeling / LitRev / Writer / Reviewer
type: work_product
status: complete
---
# 1D Regime Map And Nondimensional Closure Eligibility

Generated: `{generated_at}`

Decision: `{decision}`.

This package builds the case/span nondimensional regime map from existing
LitRev and diagnostic gate artifacts. It is a closure-eligibility and
source-overlap packet, not a coefficient admission.

## Main Finding

All closure families fail closed for fitting. Ordinary single-stream developing
forms are at most precheck-only where recirculation is not directly flagged, and
many spans are blocked by recirculation evidence. Throughflow-plus-recirculation
exchange remains the preferred architecture for persistent local exchange, but
it is diagnostic only until same-label mesh/GCI and source/property gates pass.

## Files

- `formula_validity_table.csv`: {counts['formula_rows']} formula/provenance rows.
- `segment_case_regime_map.csv`: {counts['regime_rows']} case/span regime rows.
- `tamu_overlap_matrix.csv`: {counts['overlap_rows']} source-overlap rows.
- `closure_eligibility_decisions.csv`: {counts['decision_rows']} fail-closed model-family decisions.
- `figures/svg/regime_eligibility_map.svg`: compact map for publication planning.
- `source_manifest.csv`, `no_mutation_guardrails.csv`, `summary.json`.

## Scientific Use

Use this to justify why the 1D model ladder should not admit ordinary
single-stream `Nu`, `f_D`, component `K`, or F6 coefficients from current
evidence. It supports model-form selection and next-study design only.

## Guardrails

No native CFD output, scheduler job, Fluid/external repository, registry,
admission state, blocker register, fit, model selection, source/property
release, or coefficient admission was changed.
"""


def build(outdir: Path = OUTDIR) -> dict:
    root = repo_root()
    out = root / outdir
    generated_at = datetime.now(timezone.utc).isoformat()
    decision = "regime_map_ready_fail_closed_no_closure_admission"
    regimes = regime_rows()
    tables = [
        Table("formula_validity_table.csv", formula_validity_table()),
        Table("segment_case_regime_map.csv", regimes),
        Table("tamu_overlap_matrix.csv", tamu_overlap_matrix(regimes)),
        Table("closure_eligibility_decisions.csv", closure_eligibility_decisions(regimes)),
        Table("source_manifest.csv", source_manifest(root)),
        Table("no_mutation_guardrails.csv", no_mutation_guardrails()),
    ]
    errors = validate(tables, root)
    if errors:
        raise SystemExit("validation failed:\n" + "\n".join(errors))
    for table in tables:
        write_csv(out / table.filename, table.rows)
    write_svg(out / "figures/svg/regime_eligibility_map.svg", regimes)
    counts = {
        "formula_rows": len(tables[0].rows),
        "regime_rows": len(tables[1].rows),
        "overlap_rows": len(tables[2].rows),
        "decision_rows": len(tables[3].rows),
        "manifest_rows": len(tables[4].rows),
        "guardrail_rows": len(tables[5].rows),
        "admitted_rows": 0,
    }
    summary = {
        "task_id": TASK_ID,
        "decision": decision,
        "generated_at_utc": generated_at,
        "counts": counts,
        "ordinary_single_stream_fit_rows": 0,
        "internal_nu_fit_rows": 0,
        "component_k_or_f6_fit_rows": 0,
        "exchange_cell_admitted_rows": 0,
        "source_property_release_rows": 0,
        "candidate_admission_rows": 0,
        "scheduler_or_sampler_launched": False,
        "solver_launched": False,
        "native_output_mutated": False,
        "registry_mutated": False,
        "fluid_mutated": False,
        "external_repo_mutated": False,
        "validation_errors": errors,
        "next_recommended_tasks": [
            "post-sampler same-label S13 GCI production harvest after sampler closes",
            "source/property release atlas or preflight before candidate freeze",
            "use this packet in model hierarchy and thesis evidence packets",
        ],
    }
    write_json(out / "summary.json", summary)
    (out / "README.md").write_text(readme_text(generated_at, counts, decision), encoding="utf-8")
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
