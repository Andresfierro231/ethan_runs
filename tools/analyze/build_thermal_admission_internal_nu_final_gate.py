#!/usr/bin/env python3
"""Build the final thermal admission/internal-Nu gate table.

This is an evidence integrator. It consumes AGENT-309's refreshed thermal
admission table and does not read or mutate native CFD solver outputs.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh"
    / "thermal_admission_table.csv"
)
DEFAULT_SIGN_INPUT = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh"
    / "sign_convention_table.csv"
)
DEFAULT_OUTPUT = (
    ROOT / "work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate"
)

ROW_COLUMNS = [
    "segment",
    "qoi",
    "units",
    "final_fit_eligible",
    "forward_v1_use",
    "admission_class",
    "validation_use",
    "blockers",
    "thermal_nu_policy",
    "radiation_policy",
    "sign_policy",
    "source_row",
]
SEGMENT_COLUMNS = [
    "segment",
    "fit_eligible_qoi_count",
    "validation_only_qoi_count",
    "blocked_qoi_count",
    "forward_v1_internal_nu_fit_allowed",
    "segment_decision",
    "dominant_blockers",
]
MANIFEST_COLUMNS = ["artifact", "role", "mutation_status", "path"]

SIGN_POLICY = (
    "positive wallHeatFlux/segment duty heats fluid; positive enthalpy_change "
    "increases fluid bulk enthalpy; HTC/UA/Nu are positive diagnostics, not heat-source directions"
)
RADIATION_POLICY = (
    "CFD rcExternalTemperature wallHeatFlux includes radiation where that BC is used; "
    "no separate exported qr term exists; do not add a separate radiation residual to internal Nu"
)
NU_POLICY = (
    "internal Nu may not absorb heater, cooler, passive loss, wall storage, junction, "
    "recirculation, or radiation residuals"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def split_blockers(value: str) -> list[str]:
    return [part for part in str(value).split(";") if part]


def forward_use(row: dict[str, str]) -> str:
    qoi = row["qoi"]
    if row["fit_eligible"] == "yes":
        return "fit_allowed"
    if qoi == "Nu":
        return "no_internal_nu_fit_use_baseline_or_literature_only"
    if row["admission_class"] == "validation_only":
        return "validation_only_diagnostic_not_runtime_fit"
    return "blocked_do_not_use"


def build_rows(input_csv: Path) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(read_csv(input_csv), start=1):
        rows.append(
            {
                "segment": row["segment"],
                "qoi": row["qoi"],
                "units": row["units"],
                "final_fit_eligible": row["fit_eligible"],
                "forward_v1_use": forward_use(row),
                "admission_class": row["admission_class"],
                "validation_use": row["validation_use"],
                "blockers": row["blockers"],
                "thermal_nu_policy": NU_POLICY,
                "radiation_policy": RADIATION_POLICY,
                "sign_policy": SIGN_POLICY,
                "source_row": f"{rel(input_csv)}:{index + 1}",
            }
        )
    return rows


def build_segment_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["segment"]].append(row)

    summaries = []
    for segment in sorted(grouped):
        segment_rows = grouped[segment]
        fit_count = sum(row["final_fit_eligible"] == "yes" for row in segment_rows)
        validation_count = sum(row["admission_class"] == "validation_only" for row in segment_rows)
        blocked_count = sum(row["admission_class"] == "blocked" for row in segment_rows)
        blockers = Counter()
        for row in segment_rows:
            blockers.update(split_blockers(row["blockers"]))
        dominant = ";".join(name for name, _ in blockers.most_common(8))
        if fit_count:
            decision = "fit_admissible"
            nu_allowed = "yes_if_qoi_specific"
        elif blocked_count and validation_count:
            decision = "mixed_validation_only_and_blocked"
            nu_allowed = "no"
        elif blocked_count:
            decision = "blocked"
            nu_allowed = "no"
        else:
            decision = "validation_only"
            nu_allowed = "no"
        summaries.append(
            {
                "segment": segment,
                "fit_eligible_qoi_count": fit_count,
                "validation_only_qoi_count": validation_count,
                "blocked_qoi_count": blocked_count,
                "forward_v1_internal_nu_fit_allowed": nu_allowed,
                "segment_decision": decision,
                "dominant_blockers": dominant,
            }
        )
    return summaries


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    path = output_dir / "README.md"
    segment_lines = [
        f"- `{row['segment']}`: `{row['segment_decision']}`, fit rows `{row['fit_eligible_qoi_count']}`, "
        f"validation-only `{row['validation_only_qoi_count']}`, blocked `{row['blocked_qoi_count']}`"
        for row in summary["segment_summary"]
    ]
    path.write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                "  - work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/thermal_admission_table.csv",
                "  - work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/sign_convention_table.csv",
                "tags: [thermal-closure, internal-nu, admission-gate, forward-model]",
                "related:",
                "  - operational_notes/maps/thermal-closures-and-internal-nu.md",
                "  - operational_notes/maps/thermal-boundary-and-radiation.md",
                "task: AGENT-319",
                "date: 2026-07-14",
                "role: Implementer/Tester/Writer",
                "type: work_product",
                "status: complete",
                "---",
                "# Thermal Admission / Internal Nu Final Gate",
                "",
                "This package freezes the thermal fit policy for final forward-v1 scoring.",
                "It consumes the refreshed AGENT-309 admission rows and does not mutate native CFD outputs.",
                "",
                "## Decision",
                "",
                f"- Fit-admissible rows: `{summary['fit_eligible_row_count']}`.",
                f"- Validation-only rows: `{summary['validation_only_row_count']}`.",
                f"- Blocked rows: `{summary['blocked_row_count']}`.",
                "- Internal Nu fitting for forward-v1: `no`.",
                "- Forward-v1 may use only baseline/literature/default internal Nu behavior unless a later gate admits a specific row.",
                "",
                "## Segment Decisions",
                "",
                *segment_lines,
                "",
                "## Guardrails",
                "",
                f"- Sign: {SIGN_POLICY}.",
                f"- Radiation: {RADIATION_POLICY}.",
                f"- Nu: {NU_POLICY}.",
                "",
                "## Files",
                "",
                "- `thermal_admission_internal_nu_final_gate.csv`",
                "- `segment_thermal_fit_summary.csv`",
                "- `sign_radiation_nu_policy.csv`",
                "- `source_manifest.csv`",
                "- `summary.json`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def build_package(
    input_csv: Path = DEFAULT_INPUT,
    sign_csv: Path = DEFAULT_SIGN_INPUT,
    output_dir: Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    rows = build_rows(input_csv)
    segment_summary = build_segment_summary(rows)
    output_dir.mkdir(parents=True, exist_ok=True)

    sign_rows = read_csv(sign_csv)
    policy_rows = sign_rows + [
        {
            "quantity": "forward_v1_internal_Nu",
            "positive_direction": "positive coefficient magnitude only",
            "fit_use": "not fit-admissible",
            "guardrail": NU_POLICY,
            "source": rel(input_csv),
        },
        {
            "quantity": "radiation_residual",
            "positive_direction": "not separately exported",
            "fit_use": "not fit-admissible",
            "guardrail": RADIATION_POLICY,
            "source": rel(sign_csv),
        },
    ]

    write_csv(output_dir / "thermal_admission_internal_nu_final_gate.csv", rows, ROW_COLUMNS)
    write_csv(output_dir / "segment_thermal_fit_summary.csv", segment_summary, SEGMENT_COLUMNS)
    write_csv(
        output_dir / "sign_radiation_nu_policy.csv",
        policy_rows,
        ["quantity", "positive_direction", "fit_use", "guardrail", "source"],
    )
    manifest = [
        {"artifact": "thermal_admission_table", "role": "source", "mutation_status": "read_only", "path": rel(input_csv)},
        {"artifact": "sign_convention_table", "role": "source", "mutation_status": "read_only", "path": rel(sign_csv)},
        {
            "artifact": "thermal_admission_internal_nu_final_gate",
            "role": "generated",
            "mutation_status": "new_artifact",
            "path": rel(output_dir / "thermal_admission_internal_nu_final_gate.csv"),
        },
    ]
    write_csv(output_dir / "source_manifest.csv", manifest, MANIFEST_COLUMNS)

    counter = Counter(row["admission_class"] for row in rows)
    summary = {
        "task": "AGENT-319",
        "generated_at_utc": utc_now(),
        "source_table": rel(input_csv),
        "row_count": len(rows),
        "fit_eligible_row_count": sum(row["final_fit_eligible"] == "yes" for row in rows),
        "validation_only_row_count": counter["validation_only"],
        "blocked_row_count": counter["blocked"],
        "forward_v1_internal_nu_fit_allowed": False,
        "radiation_double_count_allowed": False,
        "native_solver_outputs_mutated": False,
        "segment_summary": segment_summary,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(output_dir, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--sign-csv", type=Path, default=DEFAULT_SIGN_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    summary = build_package(args.input_csv, args.sign_csv, args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
