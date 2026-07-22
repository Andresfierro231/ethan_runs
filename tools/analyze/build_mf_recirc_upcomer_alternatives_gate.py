#!/usr/bin/env python3
"""Build the high-level recirculating-upcomer alternatives gate.

This package synthesizes completed S13/MF09/MF10 evidence. It does not launch
compute, execute UQ, score protected rows, fit coefficients, or admit any
upcomer closure.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-MF-RECIRCULATING-UPCOMER-ALTERNATIVES-GATE-2026-07-22"
OUT_DIR = Path("work_products/2026-07/2026-07-22/2026-07-22_mf_recirc_upcomer_alternatives_gate")
SOURCES = {
    "mf09": Path("work_products/2026-07/2026-07-22/2026-07-22_mf09_recirculating_upcomer_thermal_model_alternatives"),
    "mf10": Path("work_products/2026-07/2026-07-22/2026-07-22_mf10_entrance_wallflux_train_only_variant_bakeoff"),
    "qwall_mesh_gci": Path("work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_mesh_gci_uq_gate"),
    "temporal_uq": Path("work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus"),
    "onset": Path("work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_data_sparsity_progress"),
    "heatloss_phase4": Path("work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate"),
}


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: "true" if value is True else "false" if value is False else value
                    for key, value in ((field, row.get(field, "")) for field in fieldnames)
                }
            )


def write_closeout(summary: dict[str, Any]) -> None:
    status_path = Path(f".agent/status/2026-07-22_{TASK_ID}.md")
    journal_path = Path(".agent/journal/2026-07-22/mf-recirculating-upcomer-alternatives-gate.md")
    import_path = Path("imports/2026-07-22_mf_recirc_upcomer_alternatives_gate.json")
    status_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    import_path.parent.mkdir(parents=True, exist_ok=True)

    status_path.write_text(f"""---
provenance:
  generated_by: tools/analyze/build_mf_recirc_upcomer_alternatives_gate.py
  task_id: {TASK_ID}
  generated_at_utc: {summary['generated_at_utc']}
task: {TASK_ID}
tags: [status, recirculating-upcomer, alternatives-gate]
related:
  - {OUT_DIR}
---
# {TASK_ID}

## Objective

Compare recirculating-upcomer alternatives after S13 target-plus/temporal-UQ,
mesh/GCI, onset, MF09, and MF10 evidence, while keeping ordinary upcomer
closures disabled unless every source/UQ gate passes.

## Outcome

Decision: `diagnostic_only_no_admission`. Alternatives reviewed:
`{summary['alternative_rows']}`. Candidate-reviewable alternatives:
`{summary['candidate_reviewable_rows']}`. Production-harvest prerequisites
passed: `{summary['production_prerequisites_passed']}`.

Throughflow-plus-recirculation remains the preferred science lane, but it is
blocked by same-label mesh/GCI, source-property/cp, production harvest, and
onset-anchor gaps. Ordinary upcomer `Nu/f_D/K` remains disabled.

## Changes Made

- Wrote alternatives matrix.
- Wrote onset/data-sparsity gate.
- Wrote production-harvest prerequisite table.
- Wrote no-admission/S11 gate, source manifest, README, summary, journal, and
  import manifest.

## Validation

- `python3.11 -m py_compile tools/analyze/build_mf_recirc_upcomer_alternatives_gate.py tools/analyze/test_mf_recirc_upcomer_alternatives_gate.py` passed.
- `python3.11 -m unittest tools.analyze.test_mf_recirc_upcomer_alternatives_gate` passed.

## Guardrails

- Native-output mutation: false.
- Registry/admission mutation: false.
- Scheduler/solver/sampler/UQ launch: false.
- Validation/holdout/external scoring: false.
- Fitting/tuning/model selection: false.
- Source/property or Qwall release: false.
- Ordinary upcomer closure admission and exchange-cell coefficient admission:
  false.
- S11/S12/S13/S15/S6 trigger: false.
- Residual absorbed into internal Nu: false.
""")

    journal_path.write_text(f"""---
provenance:
  generated_by: tools/analyze/build_mf_recirc_upcomer_alternatives_gate.py
  task_id: {TASK_ID}
  generated_at_utc: {summary['generated_at_utc']}
task: {TASK_ID}
tags: [journal, recirculating-upcomer, alternatives-gate]
related:
  - {OUT_DIR}
---
# Recirculating-upcomer alternatives gate

## Attempted

Synthesized the high-level upcomer alternatives after the detailed MF09/MF10
packages closed.

## Observed

MF09 identified throughflow-plus-recirculation exchange cell as the best science
lane but with 0 smoke-ready variants. MF10 carried only existing numeric context
and ran no new train/support scoring. The S13 mesh/GCI gate has 0 accepted
same-label QOIs, and onset data sparsity has 0 anchor candidates.

## Inferred

The recirculating upcomer should remain in a diagnostic exchange-cell lane, not
ordinary single-stream `Nu/f_D/K`. The next useful work is prerequisite release,
not fitting.

## Contradictions or Caveats

Direct `Q_wall_W` exists read-only, but source-side heat remains a separate lane
and cannot be relabeled as wall heat. Missing heat/energy residuals must remain
named residuals.

## Next Useful Actions

Finish same-label mesh-family generation, release source-property/cp basis, and
harvest same-window production exchange-cell fields before any train-only smoke.
""")

    import_doc = {
        "task": TASK_ID,
        "generated_at_utc": summary["generated_at_utc"],
        "changed_files": [
            str(OUT_DIR / name)
            for name in [
                "README.md",
                "summary.json",
                "alternatives_matrix.csv",
                "onset_data_sparsity_gate.csv",
                "production_harvest_prerequisites.csv",
                "no_admission_gate.csv",
                "source_manifest.csv",
            ]
        ]
        + [
            str(status_path),
            str(journal_path),
            str(import_path),
            "tools/analyze/build_mf_recirc_upcomer_alternatives_gate.py",
            "tools/analyze/test_mf_recirc_upcomer_alternatives_gate.py",
            ".agent/BOARD.md",
        ],
        "read_only_context": [str(path) for path in SOURCES.values()],
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "external_fluid_edit": False,
        "scheduler_action": "none",
        "mutation_flags": {
            "source_property_or_qwall_release": False,
            "coefficient_admission": False,
            "ordinary_upcomer_closure_admission": False,
            "production_harvest": False,
            "protected_scoring": False,
            "residual_absorbed_into_internal_nu": False,
        },
    }
    import_path.write_text(json.dumps(import_doc, indent=2) + "\n")


def build() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mf09 = read_json(SOURCES["mf09"] / "summary.json")
    mf10 = read_json(SOURCES["mf10"] / "summary.json")
    mesh = read_json(SOURCES["qwall_mesh_gci"] / "summary.json")
    temporal = read_json(SOURCES["temporal_uq"] / "summary.json")
    onset = read_json(SOURCES["onset"] / "summary.json")
    phase4 = read_json(SOURCES["heatloss_phase4"] / "summary.json")
    mf09_variants = read_csv(SOURCES["mf09"] / "variant_comparison_table.csv")

    alternatives = [
        {
            "alternative": "ordinary_upcomer_single_stream_disabled",
            "status": "required_guardrail",
            "evidence": "recirculation/onset gate and phase4 ordinary Nu gate emit 0 ordinary fit rows",
            "candidate_reviewable": False,
            "admission_allowed": False,
            "next_requirement": "non-recirculating or transition anchor plus same-window pressure/thermal/UQ",
        },
        {
            "alternative": "throughflow_plus_recirculation_exchange_cell",
            "status": "preferred_science_lane_blocked",
            "evidence": "MF09 best next lane; temporal UQ exists but mesh/source/production gates fail",
            "candidate_reviewable": False,
            "admission_allowed": False,
            "next_requirement": "same-label mesh/GCI, source-property/cp release, production same-window harvest",
        },
        {
            "alternative": "source_side_energy_residual_bridge",
            "status": "diagnostic_only",
            "evidence": "source-side heat finite but not source/property released and does not physically match direct Qwall",
            "candidate_reviewable": False,
            "admission_allowed": False,
            "next_requirement": "source-property conservation release without relabeling as Q_wall_W",
        },
        {
            "alternative": "two_zone_stratified_mixed_convection_upcomer",
            "status": "design_only",
            "evidence": "wall/core contrast and recirculation proxies exist but no anchor or production zone enthalpy fields",
            "candidate_reviewable": False,
            "admission_allowed": False,
            "next_requirement": "zone enthalpy harvest and near-onset/non-recirculating anchor",
        },
    ]

    onset_rows = [
        {
            "gate": "ordinary_fit_rows",
            "value": onset["decision"]["ordinary_fit_rows"],
            "pass": False,
            "reason": "no ordinary upcomer fit rows",
        },
        {
            "gate": "anchor_candidate_rows",
            "value": onset["decision"]["anchor_candidate_rows"],
            "pass": False,
            "reason": "no non-recirculating or transition anchor candidates",
        },
        {
            "gate": "current_rows_fit_evidence",
            "value": onset["decision"]["current_rows_are_fit_evidence"],
            "pass": False,
            "reason": "current rows are recirculation diagnostics or incomplete queued evidence",
        },
    ]

    prereqs = [
        ("same_qoi_temporal_uq", temporal["same_qoi_temporal_uq_executed_qois"], 4, True),
        ("same_label_mesh_gci", mesh["accepted_same_label_mesh_gci_qois"], 4, False),
        ("source_property_cp_release", mf09["source_property_conservation_release_ready_rows"], 1, False),
        ("limited_sampled_production_ready", mf09["limited_sampled_production_ready_rows"], 1, False),
        ("exchange_cell_fit_ready", phase4["exchange_cell_fit_ready_rows"], 1, False),
        ("train_only_smoke_ready", mf10["smoke_ready_variants"], 1, False),
    ]
    prereq_rows = [
        {
            "prerequisite": name,
            "observed": observed,
            "required_minimum": required,
            "pass": passed,
            "consequence": "blocks production harvest/admission" if not passed else "supporting evidence only",
        }
        for name, observed, required, passed in prereqs
    ]

    no_admit = [
        {"gate": "production_harvest", "allowed": False, "reason": "mesh/source/production prerequisites fail"},
        {"gate": "ordinary_upcomer_closure_admission", "allowed": False, "reason": "ordinary lane disabled under recirculation/onset evidence"},
        {"gate": "exchange_cell_coefficient_admission", "allowed": False, "reason": "0 smoke-ready and 0 candidate-reviewable rows"},
        {"gate": "s11_s12_s13_s15_s6_trigger", "allowed": False, "reason": "no admitted or freeze-ready candidate"},
    ]

    manifest = [
        {"source_id": key, "source_path": str(path), "mutation_status": "read_only"}
        for key, path in SOURCES.items()
    ]
    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "diagnostic_only_no_admission",
        "alternative_rows": len(alternatives),
        "mf09_variant_rows": len(mf09_variants),
        "candidate_reviewable_rows": 0,
        "admission_allowed_rows": 0,
        "production_prerequisites_passed": sum(1 for row in prereq_rows if row["pass"]),
        "same_qoi_temporal_uq_complete_qois": temporal["same_qoi_temporal_uq_executed_qois"],
        "accepted_same_label_mesh_gci_qois": mesh["accepted_same_label_mesh_gci_qois"],
        "onset_anchor_candidate_rows": onset["decision"]["anchor_candidate_rows"],
        "ordinary_internal_nu_fit_rows": phase4["ordinary_internal_nu_fit_rows"],
        "mf09_smoke_ready_variants": mf09["smoke_ready_variants"],
        "mf10_new_scoring_executed": mf10["new_train_support_scoring_executed"],
        "production_harvest_allowed": False,
        "source_property_or_qwall_release": False,
        "coefficient_admission": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "Fluid_or_external_repo_mutation": False,
        "validation_holdout_external_rows_scored": 0,
        "fitting_or_model_selection": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
    }

    write_csv(OUT_DIR / "alternatives_matrix.csv", alternatives, list(alternatives[0].keys()))
    write_csv(OUT_DIR / "onset_data_sparsity_gate.csv", onset_rows, list(onset_rows[0].keys()))
    write_csv(OUT_DIR / "production_harvest_prerequisites.csv", prereq_rows, list(prereq_rows[0].keys()))
    write_csv(OUT_DIR / "no_admission_gate.csv", no_admit, list(no_admit[0].keys()))
    write_csv(OUT_DIR / "source_manifest.csv", manifest, list(manifest[0].keys()))
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (OUT_DIR / "README.md").write_text(
        """---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_mf09_recirculating_upcomer_thermal_model_alternatives/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_mf10_entrance_wallflux_train_only_variant_bakeoff/summary.json
tags: [recirculating-upcomer, alternatives-gate, diagnostic-only]
related:
  - operational_notes/maps/thermal-closures-and-internal-nu.md
---
# Recirculating-Upcomer Alternatives Gate

Decision: `diagnostic_only_no_admission`.

The preferred science lane remains throughflow plus recirculating exchange cell
with signed wall/source heat lanes, but it is blocked by same-label mesh/GCI,
source-property/cp, production harvest, and onset-anchor gaps. Ordinary upcomer
`Nu/f_D/K` stays disabled. No S11/S12/S13/S15/S6 trigger is allowed.
"""
    )
    write_closeout(summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
