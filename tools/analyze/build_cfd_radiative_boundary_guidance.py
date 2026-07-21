#!/usr/bin/env python3
"""Build authoritative CFD radiative-boundary guidance for 1D agents.

This AGENT-287 package corrects the stale no-radiation parity assumption after
AGENT-277 showed that the custom rcExternalTemperature boundary responds to
emissivity and Tsur. The package is documentation-oriented, but the run-level
emissivity/Tsur table is generated from AGENT-263 so future readers do not have
to infer values from the full patch table by hand.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import platform
import socket
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_cfd_radiative_boundary_guidance"
PATCH_TABLE = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv"
)
AGENT277_DECISION = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_rc_external_temperature_publication_evidence/publication_evidence_decision.json"
)
AGENT277_DELTAS = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_rc_external_temperature_publication_evidence/wallHeatFlux_delta_summary.csv"
)

RUN_FIELDS = [
    "case_id",
    "source_id",
    "run_class",
    "rcExternalTemperature_patch_count",
    "rcExternalTemperature_roles",
    "emissivity_values",
    "Tsur_values_K",
    "Ta_values_K",
    "h_min_W_m2K",
    "h_max_W_m2K",
    "thickness_total_values_m",
    "realized_rc_wallHeatFlux_sum_W",
    "radiative_boundary_interpretation",
    "one_d_agent_instruction",
]

SOURCE_FIELDS = ["source_id", "source_path", "role"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_value(row.get(field, "")) for field in fields})


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float) and not math.isfinite(value):
        return ""
    return value


def fnum(value: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return math.nan
    return parsed if math.isfinite(parsed) else math.nan


def sorted_numeric_strings(values: set[str], digits: int = 9) -> str:
    parsed = sorted({fnum(value) for value in values if math.isfinite(fnum(value))})
    if not parsed:
        return ""
    return ";".join(f"{value:.{digits}g}" for value in parsed)


def build_run_rows(patch_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in patch_rows:
        if row.get("bc_type") != "rcExternalTemperature":
            continue
        grouped[(row.get("case_id", ""), row.get("source_id", ""), row.get("run_class", ""))].append(row)

    out: list[dict[str, Any]] = []
    for (case_id, source_id, run_class), rows in sorted(grouped.items()):
        h_values = [fnum(row.get("h_W_m2K", "")) for row in rows]
        h_values = [value for value in h_values if math.isfinite(value)]
        flux_values = [fnum(row.get("realized_wallHeatFlux_W", "")) for row in rows]
        flux_values = [value for value in flux_values if math.isfinite(value)]
        out.append(
            {
                "case_id": case_id,
                "source_id": source_id,
                "run_class": run_class,
                "rcExternalTemperature_patch_count": len(rows),
                "rcExternalTemperature_roles": ";".join(sorted({row.get("role", "") for row in rows if row.get("role")})),
                "emissivity_values": sorted_numeric_strings({row.get("emissivity", "") for row in rows}),
                "Tsur_values_K": sorted_numeric_strings({row.get("Tsur_K", "") for row in rows}),
                "Ta_values_K": sorted_numeric_strings({row.get("Ta_K", "") for row in rows}),
                "h_min_W_m2K": min(h_values) if h_values else "",
                "h_max_W_m2K": max(h_values) if h_values else "",
                "thickness_total_values_m": sorted_numeric_strings({row.get("thickness_total_m", "") for row in rows}),
                "realized_rc_wallHeatFlux_sum_W": sum(flux_values) if flux_values else "",
                "radiative_boundary_interpretation": (
                    "rcExternalTemperature carries emissivity/Tsur and AGENT-277 microcases show those inputs affect wallHeatFlux; "
                    "radiation is embedded in total wallHeatFlux, not exported as a separate qr term."
                ),
                "one_d_agent_instruction": (
                    "For CFD-informed replay, do not add a separate radiation term on top of CFD wallHeatFlux. "
                    "For predictive 1D setup, include a radiation-capable external loss model or explicitly document radiation disabled as a sensitivity, not CFD parity."
                ),
            }
        )
    return out


def build_source_rows() -> list[dict[str, str]]:
    return [
        {
            "source_id": "AGENT-263_patch_role_table",
            "source_path": rel(PATCH_TABLE),
            "role": "authoritative per-run patch names, roles, emissivity, Ta, Tsur, h, wall/layer metadata, and wallHeatFlux",
        },
        {
            "source_id": "AGENT-277_microcase_decision",
            "source_path": rel(AGENT277_DECISION),
            "role": "publication evidence decision: emissivity/Tsur affect wallHeatFlux; radiation inseparable from total wallHeatFlux",
        },
        {
            "source_id": "AGENT-277_microcase_deltas",
            "source_path": rel(AGENT277_DELTAS),
            "role": "OF13 microcase final-time wallHeatFlux deltas when only emissivity or Tsur changes",
        },
        {
            "source_id": "external_boundary_reference",
            "source_path": "reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/README.md",
            "role": "human-readable authoritative CFD setup and boundary-condition description",
        },
        {
            "source_id": "repo_decisions",
            "source_path": ".agent/DECISIONS.md",
            "role": "agent-facing policy for CFD wallHeatFlux and 1D radiation handling",
        },
    ]


def read_agent277_decision() -> dict[str, Any]:
    if not AGENT277_DECISION.exists():
        return {}
    return json.loads(AGENT277_DECISION.read_text(encoding="utf-8"))


def read_agent277_deltas() -> list[dict[str, str]]:
    if not AGENT277_DELTAS.exists():
        return []
    return read_csv(AGENT277_DELTAS)


def write_guidance_md(output_dir: Path, run_rows: list[dict[str, Any]], decision: dict[str, Any], deltas: list[dict[str, str]]) -> None:
    run_lines = [
        "| Case | rcExternalTemperature patches | Roles | emissivity | Tsur K | Ta K |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    for row in run_rows:
        run_lines.append(
            f"| {row['case_id']} | {row['rcExternalTemperature_patch_count']} | "
            f"{row['rcExternalTemperature_roles']} | {row['emissivity_values']} | "
            f"{row['Tsur_values_K']} | {row['Ta_values_K']} |"
        )

    delta_lines = [
        f"- `{row['comparison_id']}`: `delta_Q = {row['delta_wallHeatFlux_integral_W']} W`, "
        f"`effect_detected = {row['effect_detected']}`"
        for row in deltas
    ]
    if not delta_lines:
        delta_lines = ["- AGENT-277 delta table was not available when this package was generated."]

    text = f"""# CFD Radiative Boundary Guidance

Generated: `{utc_now()}`
Task: `AGENT-287`

## Decision

Ethan CFD should not be described as no-radiation. The admitted Salt CFD
`rcExternalTemperature` patches carry `emissivity` and `Tsur`, and AGENT-277's
OF13 microcase evidence shows those fields affect realized `wallHeatFlux`.

AGENT-277 decision: `{decision.get('emissivity_Tsur_affect_heat_flux', 'unknown')}`
with evidence class `{decision.get('evidence_class', 'unknown')}`.

There is still no separate exported `qr`/radiation heat ledger. Radiation is
therefore inseparable from total OpenFOAM `wallHeatFlux` in the available CFD
outputs.

## Per-Run Values

{chr(10).join(run_lines)}

## Microcase Evidence

{chr(10).join(delta_lines)}

## Instructions For 1D Agents

- For CFD-informed replay that consumes CFD `wallHeatFlux`, do not add a
  separate 1D radiation term on top of that heat rate.
- For forward/predictive 1D modeling from physical setup inputs, the external
  loss model must be radiation-capable, or the run must be labeled explicitly
  as a radiation-disabled sensitivity rather than CFD parity.
- The old AGENT-279 no-radiation replay remains useful as a diagnostic
  sensitivity. It is superseded as a statement of what the CFD did.

## Authoritative Sources

- `cfd_emissivity_by_run.csv` in this package.
- AGENT-263 patch table:
  `{rel(PATCH_TABLE)}`.
- AGENT-277 publication evidence:
  `{rel(AGENT277_DECISION)}` and `{rel(AGENT277_DELTAS)}`.
- Human-readable CFD setup reference:
  `reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/README.md`.
- Agent-facing policy:
  `.agent/DECISIONS.md`.
"""
    (output_dir / "README.md").write_text(text, encoding="utf-8")


def build_package(output_dir: Path) -> dict[str, Any]:
    patch_rows = read_csv(PATCH_TABLE)
    run_rows = build_run_rows(patch_rows)
    source_rows = build_source_rows()
    decision = read_agent277_decision()
    deltas = read_agent277_deltas()

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "cfd_emissivity_by_run.csv", run_rows, RUN_FIELDS)
    write_csv(output_dir / "source_index.csv", source_rows, SOURCE_FIELDS)

    guidance = {
        "task": "AGENT-287",
        "generated_utc": utc_now(),
        "emissivity_Tsur_affect_heat_flux": decision.get("emissivity_Tsur_affect_heat_flux", "unknown"),
        "evidence_class": decision.get("evidence_class", "unknown"),
        "separate_radiation_output_available": "no",
        "cfd_radiative_exchange_status": "present_in_rcExternalTemperature_inseparable_from_wallHeatFlux",
        "cfd_emissivity_summary": {
            row["case_id"]: {
                "emissivity_values": row["emissivity_values"],
                "Tsur_values_K": row["Tsur_values_K"],
                "rcExternalTemperature_patch_count": row["rcExternalTemperature_patch_count"],
            }
            for row in run_rows
        },
        "one_d_agent_instruction": (
            "Do not call no-radiation replay CFD parity. Do not double-count radiation when using CFD wallHeatFlux. "
            "Predictive 1D models should include radiative external loss capability or label radiation-off runs as sensitivity only."
        ),
    }
    (output_dir / "radiation_guidance_decision.json").write_text(
        json.dumps(guidance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    metadata = {
        "task": "AGENT-287",
        "generated_utc": utc_now(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "patch_table": rel(PATCH_TABLE),
        "agent277_decision": rel(AGENT277_DECISION),
        "run_rows": len(run_rows),
        "source_rows": len(source_rows),
    }
    (output_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_guidance_md(output_dir, run_rows, decision, deltas)
    return metadata


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    metadata = build_package(args.output_dir)
    print(f"Wrote CFD radiative-boundary guidance to {args.output_dir}")
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
