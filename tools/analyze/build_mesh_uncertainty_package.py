#!/usr/bin/env python3
"""Build a current fail-closed mesh uncertainty package."""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mesh_uncertainty"

RECON = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_candidate_coarse_medium_fine_reconciliation"
MEDFINE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_mesh_gci_disposition"
COARSE_UNLOCK = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_same_label_coarse_gci_unlock"


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


def bool_text(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def qoi_disposition_rows() -> list[dict[str, Any]]:
    recon_rows = read_csv(RECON / "qoi_reconciliation_summary.csv")
    med_rows = {row["qoi_label"]: row for row in read_csv(MEDFINE / "qoi_mesh_disposition_summary.csv")}
    out: list[dict[str, Any]] = []
    for row in recon_rows:
        qoi = row["qoi_label"]
        medium_fine = med_rows.get(qoi, {})
        max_cf = float(row["max_coarse_fine_relative_percent_vs_fine"])
        max_mf = float(row["max_medium_fine_relative_percent_vs_fine"])
        if not bool_text(row["coarse_equivalence_admitted_all_cases"]):
            publication_status = "diagnostic_only_no_formal_gci"
            formal_gci_allowed = False
        elif max_mf > 5.0:
            publication_status = "mesh_sensitive_fail_closed"
            formal_gci_allowed = False
        else:
            publication_status = "candidate_for_formal_gci"
            formal_gci_allowed = True
        out.append(
            {
                "qoi_label": qoi,
                "case_count": row["case_count"],
                "max_medium_fine_relative_percent_vs_fine": max_mf,
                "max_coarse_fine_relative_percent_vs_fine": max_cf,
                "same_qoi_temporal_uq_status": medium_fine.get("same_qoi_temporal_uq_status", ""),
                "same_label_coarse_evidence": medium_fine.get("same_label_coarse_evidence", ""),
                "coarse_equivalence_admitted_all_cases": row["coarse_equivalence_admitted_all_cases"],
                "candidate_three_level_classes": row["candidate_three_level_classes"],
                "formal_gci_allowed": formal_gci_allowed,
                "formal_gci_status": row["formal_gci_status"],
                "publication_status": publication_status,
                "admission_allowed": False,
                "coefficient_fit_allowed": False,
                "reason": "same_label_coarse_not_admitted" if not bool_text(row["coarse_equivalence_admitted_all_cases"]) else "large_mesh_spread_or_pending_gci",
            }
        )
    return out


def case_rows() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in read_csv(RECON / "candidate_triplet_reconciliation.csv"):
        out.append(
            {
                "case_id": row["case_id"],
                "qoi_label": row["qoi_label"],
                "unit": row["unit"],
                "coarse_candidate_value": row["coarse_candidate_value"],
                "medium_value": row["medium_value"],
                "fine_value": row["fine_value"],
                "coarse_fine_relative_percent_vs_fine": row["coarse_fine_relative_percent_vs_fine"],
                "medium_fine_relative_percent_vs_fine": row["medium_fine_relative_percent_vs_fine"],
                "candidate_three_level_convergence_class": row["candidate_three_level_convergence_class"],
                "coarse_equivalence_admitted": row["coarse_equivalence_admitted"],
                "formal_gci_status": row["formal_gci_status"],
                "publication_use": "diagnostic_only",
            }
        )
    return out


def gci_matrix_rows(qoi_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "criterion": "three_same_label_mesh_levels",
            "status": "fail",
            "evidence": rel(COARSE_UNLOCK / "summary.json"),
            "reason": "formal_gci_ready_rows=0",
        },
        {
            "criterion": "coarse_equivalence_admitted",
            "status": "fail",
            "evidence": rel(RECON / "qoi_reconciliation_summary.csv"),
            "reason": "coarse_equivalence_admitted_all_cases=false_for_all_qois",
        },
        {
            "criterion": "same_qoi_temporal_uq_available",
            "status": "pass_context_only",
            "evidence": rel(MEDFINE / "qoi_mesh_disposition_summary.csv"),
            "reason": "temporal_uq_executed_but_mesh_gci_still_blocked",
        },
        {
            "criterion": "formal_gci_permitted",
            "status": "fail",
            "evidence": f"qoi_rows={len(qoi_rows)};formal_gci_allowed=0",
            "reason": "do_not_fabricate_gci_from_proxy_or_non_admitted_coarse_data",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {"source_path": rel(RECON / "qoi_reconciliation_summary.csv"), "role": "qoi_level_current_coarse_medium_fine_reconciliation", "mutation_status": "read_only"},
        {"source_path": rel(RECON / "candidate_triplet_reconciliation.csv"), "role": "case_qoi_triplet_values", "mutation_status": "read_only"},
        {"source_path": rel(MEDFINE / "qoi_mesh_disposition_summary.csv"), "role": "medium_fine_mesh_and_temporal_uq_context", "mutation_status": "read_only"},
        {"source_path": rel(COARSE_UNLOCK / "summary.json"), "role": "same_label_coarse_unlock_fail_closed_summary", "mutation_status": "read_only"},
        {"source_path": "tools/analyze/compute_gci.py", "role": "available_gci_method_not_invoked_for_blocked_data", "mutation_status": "read_only"},
    ]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""# Mesh Uncertainty Package

Generated: `{datetime.now().isoformat(timespec='seconds')}`

Decision: `{summary['decision']}`.

## Observed Facts

- QOI disposition rows: `{summary['qoi_rows']}`.
- Case/QOI triplet rows: `{summary['case_qoi_rows']}`.
- Formal GCI-ready rows: `{summary['formal_gci_allowed_rows']}`.
- `Q_wall_W` has low medium/fine spread but still lacks an admitted same-label
  coarse member.
- Exchange flux, residence-time, and wall/core contrast proxies remain highly
  mesh-sensitive and diagnostic only.

## Inferred Interpretation

The current S13 mesh evidence is scientifically useful as a sensitivity and
failure-boundary result, but it is not a formal uncertainty estimate. The
package preserves the low-spread `Q_wall_W` observation as diagnostic context
while blocking production harvest, coefficient admission, and formal GCI.

## Blockers

- Same-label coarse evidence is not admitted.
- Current coarse rows are candidates/proxies, not a release-ready mesh level.
- Some QOIs have large medium/fine and coarse/fine spreads.
- Source/property and Qwall release remain closed in the upstream packages.

## Recommended Next Action

If mesh uncertainty must be unlocked, create a true same-label coarse/medium/fine
family with matched control volumes, fields, signs, units, source/property
basis, and same-window QOIs before invoking `compute_gci.py`.

## Guardrails

No native solver output, registry/admission state, scheduler state, Fluid source,
external repository, source/property release, Qwall release, production harvest,
formal GCI, coefficient admission, final score, or residual absorption into
internal Nu was mutated.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    qoi_rows = qoi_disposition_rows()
    triplets = case_rows()
    gci_rows = gci_matrix_rows(qoi_rows)
    write_csv(
        OUT / "qoi_mesh_uncertainty_disposition.csv",
        qoi_rows,
        [
            "qoi_label",
            "case_count",
            "max_medium_fine_relative_percent_vs_fine",
            "max_coarse_fine_relative_percent_vs_fine",
            "same_qoi_temporal_uq_status",
            "same_label_coarse_evidence",
            "coarse_equivalence_admitted_all_cases",
            "candidate_three_level_classes",
            "formal_gci_allowed",
            "formal_gci_status",
            "publication_status",
            "admission_allowed",
            "coefficient_fit_allowed",
            "reason",
        ],
    )
    write_csv(
        OUT / "case_qoi_mesh_sensitivity.csv",
        triplets,
        [
            "case_id",
            "qoi_label",
            "unit",
            "coarse_candidate_value",
            "medium_value",
            "fine_value",
            "coarse_fine_relative_percent_vs_fine",
            "medium_fine_relative_percent_vs_fine",
            "candidate_three_level_convergence_class",
            "coarse_equivalence_admitted",
            "formal_gci_status",
            "publication_use",
        ],
    )
    write_csv(OUT / "formal_gci_admissibility_matrix.csv", gci_rows, ["criterion", "status", "evidence", "reason"])
    write_csv(OUT / "source_manifest.csv", source_manifest_rows(), ["source_path", "role", "mutation_status"])
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task": "TODO-MESH-UNCERTAINTY",
        "decision": "mesh_uncertainty_fail_closed_no_formal_gci_current_s13",
        "qoi_rows": len(qoi_rows),
        "case_qoi_rows": len(triplets),
        "formal_gci_allowed_rows": sum(1 for row in qoi_rows if row["formal_gci_allowed"]),
        "production_harvest_allowed": False,
        "admission_allowed": False,
        "outputs": [
            "qoi_mesh_uncertainty_disposition.csv",
            "case_qoi_mesh_sensitivity.csv",
            "formal_gci_admissibility_matrix.csv",
            "source_manifest.csv",
            "README.md",
            "summary.json",
        ],
    }
    write_readme(summary)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
