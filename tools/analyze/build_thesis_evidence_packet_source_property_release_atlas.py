#!/usr/bin/env python3
"""Build the thesis evidence packet source/property release atlas."""

from __future__ import annotations

import csv
import json
from pathlib import Path


TASK_ID = "TODO-THESIS-EVIDENCE-PACKET-SOURCE-PROPERTY-RELEASE-ATLAS-2026-07-22"
DATE = "2026-07-22"
REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_source_property_release_atlas"

PREFLIGHT = REPO / "work_products/2026-07/2026-07-22/2026-07-22_source_property_nominal_train_release_preflight"
MF13 = REPO / "work_products/2026-07/2026-07-22/2026-07-22_mf13_signed_source_property_heat_path_release_preflight"
S12 = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thesis_study_s12_thermal_source_property_freeze_gate"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def atlas_rows() -> list[dict[str, object]]:
    return [
        {
            "source_or_property_family": "Salt1 branch source envelope",
            "current_release_status": "blocked",
            "release_ready": "no",
            "protected_row_release_allowed": "no",
            "candidate_use_now": "diagnostic context only",
            "primary_blocker": "missing row-specific Salt1 branch source-envelope evidence",
            "next_gate": "join row-specific strict-pass source-envelope evidence before S11/S15 release",
        },
        {
            "source_or_property_family": "Salt2/Salt3/Salt4 mixed source envelope",
            "current_release_status": "blocked",
            "release_ready": "no",
            "protected_row_release_allowed": "no",
            "candidate_use_now": "diagnostic context only",
            "primary_blocker": "mixed/outside/unknown source-envelope evidence prevents strict pass",
            "next_gate": "replace mixed/outside/unknown labels with row-specific strict-pass evidence",
        },
        {
            "source_or_property_family": "heater source fraction and test-section source/loss",
            "current_release_status": "evidence_only",
            "release_ready": "no",
            "protected_row_release_allowed": "no",
            "candidate_use_now": "source-bounded residual ownership discussion",
            "primary_blocker": "independent source allocation has not been released for prediction",
            "next_gate": "independent source/property release tied to setup-known inputs",
        },
        {
            "source_or_property_family": "cooler/HX removal or UA",
            "current_release_status": "blocked",
            "release_ready": "no",
            "protected_row_release_allowed": "no",
            "candidate_use_now": "not a runtime candidate input",
            "primary_blocker": "cooler duty or realized heat removal would be post-solve leakage",
            "next_gate": "predeclared setup-known cooler model with no realized CFD duty input",
        },
        {
            "source_or_property_family": "passive wall and external hA/radiation",
            "current_release_status": "evidence_only",
            "release_ready": "no",
            "protected_row_release_allowed": "no",
            "candidate_use_now": "thermal residual attribution only",
            "primary_blocker": "passive wall repair is not released as source-bounded candidate",
            "next_gate": "runtime-legal wall basis plus row-specific source-envelope pass",
        },
        {
            "source_or_property_family": "fluid property mode",
            "current_release_status": "label_only",
            "release_ready": "no",
            "protected_row_release_allowed": "no",
            "candidate_use_now": "provenance label and gate context",
            "primary_blocker": "property sensitivity remains material-closure fit blocked",
            "next_gate": "candidate-specific property release independent of protected rows",
        },
        {
            "source_or_property_family": "wall/layer materials",
            "current_release_status": "evidence_only",
            "release_ready": "no",
            "protected_row_release_allowed": "no",
            "candidate_use_now": "wall/core temperature interpretation",
            "primary_blocker": "runtime wall profile basis is not released",
            "next_gate": "predeclared wall material/source basis with same-QOI UQ",
        },
        {
            "source_or_property_family": "signed wall flux and heat path",
            "current_release_status": "preflight_only",
            "release_ready": "no",
            "protected_row_release_allowed": "no",
            "candidate_use_now": "heat-path diagnostic and source-property blocker evidence",
            "primary_blocker": "signed source/property heat path has not passed release gate",
            "next_gate": "same-window energy residual and candidate-specific source release",
        },
        {
            "source_or_property_family": "S13 exchange Qwall",
            "current_release_status": "blocked",
            "release_ready": "no",
            "protected_row_release_allowed": "no",
            "candidate_use_now": "finite sampled-field evidence only",
            "primary_blocker": "production harvest, same-label mesh family, and same-QOI UQ gates remain blocked",
            "next_gate": "production exchange-state harvest plus same-window Qwall UQ",
        },
        {
            "source_or_property_family": "empirical correction",
            "current_release_status": "diagnostic_only",
            "release_ready": "no",
            "protected_row_release_allowed": "no",
            "candidate_use_now": "bias-shape interpretation only",
            "primary_blocker": "not a physical source/property release",
            "next_gate": "convert to a physical source-bounded candidate or keep diagnostic",
        },
        {
            "source_or_property_family": "junction/stub source or pressure coupling",
            "current_release_status": "blocked",
            "release_ready": "no",
            "protected_row_release_allowed": "no",
            "candidate_use_now": "blocker localization",
            "primary_blocker": "no independent source/property release and pressure anchors remain insufficient",
            "next_gate": "low-recirculation pressure anchors plus independent source/property release",
        },
    ]


def runtime_legality_rows() -> list[dict[str, object]]:
    return [
        {"input_family": "CFD mdot", "runtime_allowed": "no", "release_status": "blocked", "reason": "forbidden runtime input: observed flow solution, not setup-known input"},
        {"input_family": "realized wallHeatFlux or total_Q", "runtime_allowed": "no", "release_status": "blocked", "reason": "forbidden runtime input: post-solve heat-path evidence would leak targets"},
        {"input_family": "cooler duty or realized heat removal", "runtime_allowed": "no", "release_status": "blocked", "reason": "forbidden runtime input: not released as setup-only source/property"},
        {"input_family": "validation/holdout/external temperatures", "runtime_allowed": "no", "release_status": "blocked", "reason": "forbidden runtime input: protected targets cannot tune or drive prediction"},
        {"input_family": "row-specific source envelope labels", "runtime_allowed": "label_only", "release_status": "blocked", "reason": "labels are complete but strict-pass release is not complete"},
    ]


def writer_brief(summary: dict[str, object]) -> str:
    return f"""# Source/Property Release Atlas Writer Brief

Decision: `{summary["decision"]}`.

Use this packet to explain why the thesis has diagnostic CFD evidence but no
source/property release for a frozen predictive candidate.

Safe claims:

- All four nominal train rows have source/property labels, but zero rows are
  release-ready.
- Protected validation/holdout/external rows remain unreleased.
- S12/S13/wall/source/empirical paths are useful as evidence, not as frozen
  candidates.

Forbidden claims:

- Do not claim a source/property release.
- Do not claim a final score, candidate freeze, validation score, holdout score,
  or external-test score.
- Do not absorb thermal residuals into internal Nu.
- Do not use realized CFD mdot, wall heat flux, cooler duty, protected
  temperatures, or protected residuals as runtime inputs.
"""


def build() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    nominal_rows = read_csv(PREFLIGHT / "nominal_train_release_audit.csv")
    protected_rows = read_csv(PREFLIGHT / "protected_row_release_audit.csv")
    blocker_rows = read_csv(PREFLIGHT / "source_family_blocker_rollup.csv")
    candidate_rows = read_csv(PREFLIGHT / "candidate_lane_consequences.csv")
    mf13_summary = read_json(MF13 / "summary.json")
    s12_summary = read_json(S12 / "summary.json")
    preflight_summary = read_json(PREFLIGHT / "summary.json")

    rows = atlas_rows()
    legality_rows = runtime_legality_rows()
    source_manifest = [
        {"source_id": "nominal_train_release_audit", "path": rel(PREFLIGHT / "nominal_train_release_audit.csv"), "use": "nominal release row basis", "mutation_status": "read_only"},
        {"source_id": "protected_row_release_audit", "path": rel(PREFLIGHT / "protected_row_release_audit.csv"), "use": "protected release count basis", "mutation_status": "read_only"},
        {"source_id": "source_family_blocker_rollup", "path": rel(PREFLIGHT / "source_family_blocker_rollup.csv"), "use": "source-family blocker basis", "mutation_status": "read_only"},
        {"source_id": "candidate_lane_consequences", "path": rel(PREFLIGHT / "candidate_lane_consequences.csv"), "use": "candidate consequence basis", "mutation_status": "read_only"},
        {"source_id": "mf13_summary", "path": rel(MF13 / "summary.json"), "use": "signed heat-path preflight context", "mutation_status": "read_only"},
        {"source_id": "s12_summary", "path": rel(S12 / "summary.json"), "use": "S12 source/property freeze-gate context", "mutation_status": "read_only"},
    ]
    no_mutation_rows = [
        {"guardrail": "native_output_mutation", "value": "False"},
        {"guardrail": "registry_or_admission_mutation", "value": "False"},
        {"guardrail": "scheduler_action", "value": "False"},
        {"guardrail": "fluid_or_external_edit", "value": "False"},
        {"guardrail": "validation_holdout_external_scoring", "value": "False"},
        {"guardrail": "source_property_release", "value": "False"},
        {"guardrail": "protected_row_release", "value": "False"},
        {"guardrail": "candidate_freeze", "value": "False"},
        {"guardrail": "residual_absorbed_into_internal_nu", "value": "False"},
    ]

    write_csv(OUT / "source_property_release_atlas.csv", rows, ["source_or_property_family", "current_release_status", "release_ready", "protected_row_release_allowed", "candidate_use_now", "primary_blocker", "next_gate"])
    write_csv(OUT / "nominal_train_release_context.csv", nominal_rows, list(nominal_rows[0].keys()))
    write_csv(OUT / "protected_row_release_audit.csv", protected_rows, list(protected_rows[0].keys()))
    write_csv(OUT / "source_family_blocker_rollup.csv", blocker_rows, list(blocker_rows[0].keys()))
    write_csv(OUT / "candidate_consequence_table.csv", candidate_rows, list(candidate_rows[0].keys()))
    write_csv(OUT / "runtime_legality_audit.csv", legality_rows, ["input_family", "runtime_allowed", "release_status", "reason"])
    write_csv(OUT / "source_manifest.csv", source_manifest, ["source_id", "path", "use", "mutation_status"])
    write_csv(OUT / "no_mutation_guardrails.csv", no_mutation_rows, ["guardrail", "value"])

    summary = {
        "task_id": TASK_ID,
        "date": DATE,
        "decision": "source_property_release_atlas_ready_no_release_no_freeze",
        "atlas_rows": len(rows),
        "nominal_train_rows": preflight_summary.get("nominal_train_rows"),
        "labels_complete_rows": preflight_summary.get("labels_complete_rows"),
        "release_ready_rows": preflight_summary.get("release_ready_rows"),
        "protected_rows_released": preflight_summary.get("protected_rows_released"),
        "source_property_release": False,
        "candidate_freeze": False,
        "validation_holdout_external_scoring": False,
        "final_score": "not_performed",
        "mf13_decision": mf13_summary.get("decision"),
        "s12_decision": s12_summary.get("decision"),
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "fluid_or_external_edit": False,
        "residual_absorbed_into_internal_nu": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "writer_brief.md").write_text(writer_brief(summary), encoding="utf-8")
    (OUT / "README.md").write_text(readme(summary), encoding="utf-8")
    return summary


def readme(summary: dict[str, object]) -> str:
    return f"""---
provenance:
  - {rel(PREFLIGHT / 'summary.json')}
  - {rel(MF13 / 'summary.json')}
  - {rel(S12 / 'summary.json')}
tags: [thesis, source-property, release-atlas, no-freeze]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/thesis-evidence-packet-source-property-release-atlas.md
  - imports/2026-07-22_thesis_evidence_packet_source_property_release_atlas.json
task: {TASK_ID}
date: {DATE}
role: Writer/Reviewer/Tester
type: work_product
status: complete
---
# Source/Property Release Atlas

Decision: `{summary["decision"]}`.

This packet maps each source/property family to its current release state for
thesis use. It preserves the central result: complete labels are not the same
thing as a candidate-specific source/property release.

Key outcomes:

- atlas rows: `{summary["atlas_rows"]}`
- nominal train rows reviewed: `{summary["nominal_train_rows"]}`
- release-ready rows: `{summary["release_ready_rows"]}`
- protected rows released: `{summary["protected_rows_released"]}`
- source/property release: `{summary["source_property_release"]}`

Outputs:

- `source_property_release_atlas.csv`
- `nominal_train_release_context.csv`
- `protected_row_release_audit.csv`
- `source_family_blocker_rollup.csv`
- `candidate_consequence_table.csv`
- `runtime_legality_audit.csv`
- `writer_brief.md`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

Guardrails: no native CFD/OpenFOAM output, registry/admission state, scheduler
state, Fluid source, external repository, validation/holdout/external-test
score, final score, source/property release, protected-row release, candidate
freeze, or residual absorption into internal Nu was changed.
"""


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
