#!/usr/bin/env python3
"""Build N2 panel addendum after S13 neighbor-window sampling."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "TODO-THESIS-N2-UPCOMER-EXCHANGE-QWALL-UQ-PAPER-PANELS-REFRESH-AFTER-NEIGHBOR-SAMPLING-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_n2_upcomer_exchange_qwall_uq_paper_panels_refresh_after_neighbor_sampling"
PRIOR_N2 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_n2_upcomer_exchange_qwall_uq_paper_panels"
SAMPLING = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling"


def now_iso() -> str:
    return datetime.now(ZoneInfo("America/Chicago")).replace(microsecond=0).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def qwall_time_drift_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    qwall_rows = [row for row in rows if row["qoi_label"] == "Q_wall_W"]
    out: list[dict[str, object]] = []
    for row in qwall_rows:
        minus = float(row["target_minus_value"])
        target = float(row["target_value"])
        delta = target - minus
        rel = delta / target if target else 0.0
        out.append(
            {
                "case_id": row["case_id"],
                "target_minus_time_window_s": row["target_minus_time_window_s"],
                "target_time_window_s": row["target_time_window_s"],
                "target_plus_time_window_s": row["target_plus_time_window_s"],
                "Q_wall_target_minus_W": f"{minus:.12g}",
                "Q_wall_target_W": f"{target:.12g}",
                "Q_wall_target_minus_to_target_delta_W": f"{delta:.12g}",
                "Q_wall_target_minus_to_target_relative_delta": f"{rel:.12g}",
                "target_plus_status": row["target_plus_status"],
                "paper_claim": "one-sided adjacent-window drift only; not same-QOI UQ",
            }
        )
    return out


def qoi_blocker_rows(matrix_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in matrix_rows:
        out.append(
            {
                "qoi_label": row["qoi_label"],
                "case_count": row["case_count"],
                "target_ready_rows": row["target_ready_rows"],
                "target_minus_ready_rows": row["target_minus_ready_rows"],
                "target_plus_ready_rows": row["target_plus_ready_rows"],
                "same_qoi_neighbor_uq_ready": row["same_qoi_neighbor_uq_ready"],
                "paper_panel_status": "ready_as_blocker_panel",
                "claim_boundary": "diagnostic target-minus plus target; no production harvest/admission",
                "blocking_reason": row["blocking_reason"],
            }
        )
    return out


def panel_manifest_rows() -> list[dict[str, str]]:
    return [
        {
            "panel_id": "A",
            "panel_type": "prior_N2_context",
            "source": str((PRIOR_N2 / "panel_manifest.csv").relative_to(ROOT)),
            "status": "ready_existing_artifact",
            "claim_boundary": "diagnostic N2 package remains valid",
        },
        {
            "panel_id": "B",
            "panel_type": "Q_wall_one_sided_time_drift",
            "source": str((OUT / "qwall_target_minus_time_drift_table.csv").relative_to(ROOT)),
            "status": "table_ready",
            "claim_boundary": "target-minus adjacent drift only; not UQ",
        },
        {
            "panel_id": "C",
            "panel_type": "same_QOI_neighbor_UQ_blocker",
            "source": str((OUT / "same_qoi_neighbor_uq_blocker_table.csv").relative_to(ROOT)),
            "status": "table_ready",
            "claim_boundary": "target-plus missing for all QOIs",
        },
        {
            "panel_id": "D",
            "panel_type": "production_admission_gate",
            "source": str((SAMPLING / "production_readiness_gate.csv").relative_to(ROOT)),
            "status": "caption_ready",
            "claim_boundary": "production harvest, mesh/GCI UQ, and admission remain closed",
        },
    ]


def claim_boundary_rows(summary: dict[str, object]) -> list[dict[str, object]]:
    return [
        {
            "claim": "Direct target-window Q_wall_W exists for Salt2/Salt3/Salt4",
            "allowed": "true",
            "basis": "prior exact-pressure/Qwall package and N2 package",
        },
        {
            "claim": "Target-minus adjacent rows now exist for four requested S13 QOIs",
            "allowed": "true",
            "basis": f"{summary['target_minus_ready_rows']} sampled target-minus rows",
        },
        {
            "claim": "Same-QOI neighbor-window UQ is complete",
            "allowed": "false",
            "basis": f"{summary['target_plus_ready_rows']} target-plus rows; latest stored target directories",
        },
        {
            "claim": "Move to mesh/GCI UQ or production harvest",
            "allowed": "false",
            "basis": "neighbor-window UQ gate failed closed",
        },
        {
            "claim": "Admit an ordinary or exchange-cell coefficient",
            "allowed": "false",
            "basis": "no same-QOI UQ-ready labels and no production harvest release",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {
            "source_path": str((PRIOR_N2 / "README.md").relative_to(ROOT)),
            "source_type": "completed_prior_panel_package",
            "use": "baseline N2 diagnostic package",
            "mutation": "read_only",
        },
        {
            "source_path": str((SAMPLING / "same_qoi_neighbor_window_rows.csv").relative_to(ROOT)),
            "source_type": "completed_neighbor_sampling_table",
            "use": "target-minus and target rows for panel addendum",
            "mutation": "read_only",
        },
        {
            "source_path": str((SAMPLING / "same_qoi_uq_matrix.csv").relative_to(ROOT)),
            "source_type": "completed_neighbor_uq_matrix",
            "use": "same-QOI UQ blocker table",
            "mutation": "read_only",
        },
    ]


def guardrail_rows() -> list[dict[str, str]]:
    rows = {
        "native_output_mutation": "false",
        "registry_or_admission_mutation": "false",
        "scheduler_action": "false",
        "solver_sampler_harvest_uq_launched": "false",
        "thesis_current_file_edit": "false",
        "Q_wall_W_release_or_relabel": "false",
        "source_property_release": "false",
        "coefficient_admission": "false",
        "s11_s12_s13_s15_s6_trigger": "false",
        "blocker_register_change": "false",
        "residual_absorbed_into_internal_nu": "false",
    }
    return [{"guardrail": key, "value": value} for key, value in rows.items()]


def write_markdown(summary: dict[str, object]) -> None:
    rel_rows = qwall_time_drift_rows(read_csv(SAMPLING / "same_qoi_neighbor_window_rows.csv"))
    lines = [
        "---",
        "provenance:",
        f"  - {SAMPLING.relative_to(ROOT)}/same_qoi_neighbor_window_rows.csv",
        f"  - {SAMPLING.relative_to(ROOT)}/same_qoi_uq_matrix.csv",
        f"  - {PRIOR_N2.relative_to(ROOT)}/README.md",
        "tags: [thesis, n2, s13, upcomer-exchange, qwall, panels, fail-closed]",
        "related:",
        "  - .agent/status/2026-07-22_TODO-THESIS-N2-UPCOMER-EXCHANGE-QWALL-UQ-PAPER-PANELS-REFRESH-AFTER-NEIGHBOR-SAMPLING-2026-07-22.md",
        f"  - {SAMPLING.relative_to(ROOT)}/README.md",
        f"task: {TASK_ID}",
        "date: 2026-07-22",
        "role: Hydraulics / Thermal-modeling / cfd-pp / Figures / Tester / Writer / Reviewer",
        "type: work_product",
        "status: complete",
        "---",
        "# N2 Qwall/UQ Panel Refresh After Neighbor Sampling",
        "",
        f"Decision: `{summary['decision']}`.",
        "",
        "This addendum updates the N2 thesis/paper panel package with the new",
        "target-minus sampling result. It preserves the diagnostic-only claim",
        "boundary because target-plus rows are still absent.",
        "",
        f"- target rows ready: `{summary['target_ready_rows']}`",
        f"- target-minus rows sampled: `{summary['target_minus_ready_rows']}`",
        f"- target-plus rows sampled: `{summary['target_plus_ready_rows']}`",
        f"- same-QOI UQ-ready labels: `{summary['same_qoi_neighbor_uq_ready_qois']}`",
        f"- production harvest allowed: `{str(summary['production_harvest_allowed']).lower()}`",
        "",
        "Qwall adjacent-window drift rows:",
        "",
        "| case | target-minus s | target s | Qwall delta W | relative delta |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rel_rows:
        lines.append(
            f"| {row['case_id']} | {row['target_minus_time_window_s']} | {row['target_time_window_s']} | "
            f"{row['Q_wall_target_minus_to_target_delta_W']} | {row['Q_wall_target_minus_to_target_relative_delta']} |"
        )
    lines.extend(
        [
            "",
            "Use this package as a paper/thesis blocker panel, not as admission",
            "evidence. Same-QOI UQ still requires target-minus / target /",
            "target-plus triplets for each requested label.",
        ]
    )
    write_text(OUT / "README.md", "\n".join(lines) + "\n")

    write_text(
        OUT / "caption_bank.md",
        "\n".join(
            [
                "# Caption Bank",
                "",
                "**Qwall one-sided drift panel.** Direct trusted-wall `Q_wall_W` changes",
                "only slightly between target-minus and target windows for the three",
                "retained Salt cases, but this is one-sided diagnostic evidence because",
                "no target-plus window is stored.",
                "",
                "**Same-QOI UQ blocker panel.** All four S13 QOI labels have target and",
                "target-minus rows, while target-plus rows remain `0/12`; production",
                "harvest and coefficient admission therefore remain closed.",
            ]
        )
        + "\n",
    )

    write_text(
        OUT / "scientific_addendum.md",
        "\n".join(
            [
                "# Scientific Addendum",
                "",
                "The new evidence improves the N2 narrative by replacing a generic",
                "missing-neighbor statement with an observed one-sided target-minus",
                "sample. The result is still fail-closed for S13: a one-sided adjacent",
                "window cannot establish the same-QOI neighbor-window UQ required before",
                "mesh/GCI UQ, production harvest, or coefficient admission.",
                "",
                "The thesis-safe claim is that target-window Qwall and exchange proxies",
                "are diagnostic evidence with a documented target-plus availability",
                "blocker. The thesis-unsafe claim would be that these rows support a",
                "production exchange coefficient or final predictive candidate.",
            ]
        )
        + "\n",
    )


def build() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    sampling_summary = json.loads((SAMPLING / "summary.json").read_text())
    neighbor_rows = read_csv(SAMPLING / "same_qoi_neighbor_window_rows.csv")
    matrix_rows = read_csv(SAMPLING / "same_qoi_uq_matrix.csv")

    qwall_rows = qwall_time_drift_rows(neighbor_rows)
    blocker_rows = qoi_blocker_rows(matrix_rows)
    panels = panel_manifest_rows()
    claims = claim_boundary_rows(sampling_summary)

    write_csv(
        OUT / "qwall_target_minus_time_drift_table.csv",
        qwall_rows,
        [
            "case_id",
            "target_minus_time_window_s",
            "target_time_window_s",
            "target_plus_time_window_s",
            "Q_wall_target_minus_W",
            "Q_wall_target_W",
            "Q_wall_target_minus_to_target_delta_W",
            "Q_wall_target_minus_to_target_relative_delta",
            "target_plus_status",
            "paper_claim",
        ],
    )
    write_csv(
        OUT / "same_qoi_neighbor_uq_blocker_table.csv",
        blocker_rows,
        [
            "qoi_label",
            "case_count",
            "target_ready_rows",
            "target_minus_ready_rows",
            "target_plus_ready_rows",
            "same_qoi_neighbor_uq_ready",
            "paper_panel_status",
            "claim_boundary",
            "blocking_reason",
        ],
    )
    write_csv(OUT / "panel_manifest.csv", panels, ["panel_id", "panel_type", "source", "status", "claim_boundary"])
    write_csv(OUT / "claim_boundary_table.csv", claims, ["claim", "allowed", "basis"])
    write_csv(OUT / "source_manifest.csv", source_manifest_rows(), ["source_path", "source_type", "use", "mutation"])
    write_csv(OUT / "no_mutation_guardrails.csv", guardrail_rows(), ["guardrail", "value"])

    summary = {
        "task_id": TASK_ID,
        "generated_at": now_iso(),
        "decision": "n2_refresh_ready_diagnostic_only_target_plus_missing",
        "source_sampling_decision": sampling_summary["decision"],
        "panel_rows": len(panels),
        "qwall_time_drift_rows": len(qwall_rows),
        "same_qoi_blocker_rows": len(blocker_rows),
        "target_ready_rows": sampling_summary["target_ready_rows"],
        "target_minus_ready_rows": sampling_summary["target_minus_ready_rows"],
        "target_plus_ready_rows": sampling_summary["target_plus_ready_rows"],
        "same_qoi_neighbor_uq_ready_qois": sampling_summary["same_qoi_neighbor_uq_ready_qois"],
        "production_harvest_allowed": False,
        "admission_allowed": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "thesis_current_file_edit": False,
        "Q_wall_W_release_or_relabel": False,
        "source_property_release": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    write_markdown(summary)
    return summary


def main() -> int:
    summary = build()
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
