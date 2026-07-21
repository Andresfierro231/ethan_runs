#!/usr/bin/env python3
"""Build Salt Q perturbation status tables from registry case rows.

The registry supplies the case set and exact staged roots. Gate/recommendation
CSV products supply the operating-point status text. Current coordinator policy
is that a converged/stationary terminal window is closure-fit admissible; the
older post-restart-advance `too_short` label is retained as context, not as an
exclusion, for rows that are otherwise converged.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = ROOT / "registry" / "case_registry.csv"
DEFAULT_MANIFEST = (
    ROOT
    / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations"
    / "corrected_case_manifest.csv"
)
DEFAULT_GATE = (
    ROOT
    / "work_products/2026-07/2026-07-09"
    / "2026-07-09_corrected_salt_q_gate_3280969_review"
    / "row_verdicts.csv"
)
DEFAULT_RECOMMENDATIONS = (
    ROOT
    / "work_products/2026-07/2026-07-09"
    / "2026-07-09_corrected_salt_q_minimal_continuation_plan"
    / "convergence_resubmit_recommendations.csv"
)
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "work_products/2026-07/2026-07-10"
    / "2026-07-10_registry_corrected_q_status_table"
)
CORRECTED_OWNER = "corrected_salt_q_sensitivity"
DEFAULT_SELECTED_CASE_KEYS = [
    "salt2_jin_lo10q_corrected",
    "salt2_jin_hi10q_corrected",
    "salt4_jin_lo10q_corrected",
]


@dataclass(frozen=True)
class StatusRow:
    source_case_key: str
    case_key: str
    label: str
    gate_latest_solver_time_s: str
    latest_registered_timestep_s: str
    latest_log_time_s: str
    post_restart_advance: str
    status: str
    registry_source_root: str
    closure_fit_admissible: str
    future_fit_label: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def index_by(rows: Iterable[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows if row.get(key)}


def corrected_registry_rows(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("source_owner") == CORRECTED_OWNER
        or row.get("source_id", "").endswith("_corrected")
    ]


def display_case_key(case_key: str) -> str:
    match = re.fullmatch(r"salt(\d+)_jin_(lo|hi)(5|10)q_corrected", case_key)
    if not match:
        return case_key
    salt, direction, pct = match.groups()
    return f"salt{salt}_{direction}{pct}q"


def seconds_with_minsec(value: str) -> str:
    if not value:
        return ""
    seconds = float(value)
    rounded = int(round(seconds))
    minutes, sec = divmod(rounded, 60)
    if minutes >= 60:
        hours, minutes = divmod(minutes, 60)
        return f"{seconds:.3f} s = {hours}h {minutes:02d}m {sec:02d}s"
    return f"{seconds:.3f} s = {minutes}m {sec:02d}s"


def format_time(value: str) -> str:
    return "" if not value else f"{float(value):.3f} s"


def parse_numeric_time(name: str) -> float | None:
    try:
        value = float(name)
    except ValueError:
        return None
    return value if value >= 0 else None


def latest_registered_timestep(source_root: str) -> tuple[str, str]:
    root = Path(source_root)
    if not source_root or not root.exists():
        return "", ""

    candidates: list[tuple[float, str, str]] = []
    processor_dirs = [
        child
        for child in root.iterdir()
        if child.is_dir() and (child.name.startswith("processors") or child.name.startswith("processor"))
    ]

    scan_roots = processor_dirs or [root]
    for scan_root in scan_roots:
        for child in scan_root.iterdir():
            if not child.is_dir():
                continue
            value = parse_numeric_time(child.name)
            if value is None:
                continue
            candidates.append((value, child.name, str(child)))

    if not candidates:
        return "", ""
    _value, time_name, path = max(candidates, key=lambda item: item[0])
    return format_time(time_name), path


def latest_log_time(source_root: str) -> str:
    root = Path(source_root)
    logs_dir = root / "logs"
    if not logs_dir.is_dir():
        return ""

    latest: float | None = None
    pattern = re.compile(r"^Time\s*=\s*([-+0-9.eE]+)s?\s*$")
    for log_path in sorted(logs_dir.glob("log.foamRun*")):
        if not log_path.is_file():
            continue
        with log_path.open("rb") as handle:
            handle.seek(0, 2)
            size = handle.tell()
            handle.seek(max(0, size - 2_000_000))
            text = handle.read().decode("utf-8", errors="replace")
        for line in text.splitlines():
            match = pattern.match(line.strip())
            if not match:
                continue
            value = parse_numeric_time(match.group(1))
            if value is not None and (latest is None or value > latest):
                latest = value

    return "" if latest is None else f"{latest:.3f} s"


def status_sentence(gate: dict[str, str], recommendation: dict[str, str]) -> str:
    gate_status = gate.get("gate_operating_point_verdict", "")
    rec = recommendation.get("recommendation", "")
    row_verdict = gate.get("row_verdict", "")
    action = gate.get("action", "")
    minimum_next = recommendation.get("minimum_next_action", "")

    if convergence_admits(gate, recommendation):
        return (
            "Converged terminal window; closure-fit admissible under current coordinator policy. "
            f"Former {gate_status or 'advance'} gate context is not an exclusion."
        )
    if gate.get("closure_fit_admissible") == "yes":
        return "Admitted by gate evidence; may be used only under its documented fit label."
    if rec == "hold_policy_then_continue":
        return f"Partial usable window, but gate says {gate_status}; hold until Salt1 policy resolves, then continue if still useful."
    if rec == "investigate_before_resubmit" or row_verdict.startswith("excluded"):
        monitor_text = f"{action} {recommendation.get('reason', '')}".lower()
        if "convergencemonitor" in monitor_text or "monitor" in monitor_text:
            return "Not accepted; early monitor/End path. Repair/rerun before treating as continuation evidence."
        return f"Not accepted; investigate before resubmission. {minimum_next}".strip()
    if rec == "defer_second_wave":
        return f"Partial usable window, but gate says {gate_status}; defer behind Salt2 +/-10Q first wave."
    if rec == "continue_first_wave":
        return f"Partial usable window, but gate says {gate_status}; first-wave continuation candidate."
    if rec.startswith("defer"):
        return f"Partial/under-advanced; gate says {gate_status}; deferred continuation candidate."
    if row_verdict.startswith("partial"):
        return f"Partial usable window, but gate says {gate_status}; needs extended continuation and formal re-gate."
    return action or minimum_next or "No gate/recommendation text available."


def convergence_admits(gate: dict[str, str], recommendation: dict[str, str]) -> bool:
    if gate.get("closure_fit_admissible") == "yes":
        return True
    terminal_status = recommendation.get("terminal_window_status", "")
    if terminal_status == "terminal_window_stationary_but_under_advanced":
        return True
    if gate.get("row_verdict") != "partial_requires_extended_continuation":
        return False
    try:
        samples = int(float(gate.get("late_window_samples", "0")))
        drift_pct = abs(float(gate.get("late_window_drift_pct", "nan")))
        amp_pct = abs(float(gate.get("late_window_amp_pct", "nan")))
    except ValueError:
        return False
    return samples >= 300 and drift_pct <= 1.0 and amp_pct <= 1.0


def build_status_rows(
    registry_rows: list[dict[str, str]],
    gate_rows: list[dict[str, str]],
    recommendation_rows: list[dict[str, str]],
    case_keys: list[str],
) -> list[StatusRow]:
    registry_by_source = index_by(corrected_registry_rows(registry_rows), "source_id")
    gate_by_key = index_by(gate_rows, "case_key")
    rec_by_key = index_by(recommendation_rows, "case_key")

    selected = case_keys or sorted(registry_by_source)
    rows: list[StatusRow] = []
    for case_key in selected:
        registry = registry_by_source.get(case_key)
        if not registry:
            continue
        gate = gate_by_key.get(case_key, {})
        rec = rec_by_key.get(case_key, {})
        latest_written, _latest_path = latest_registered_timestep(registry.get("source_root", ""))
        closure_admitted = convergence_admits(gate, rec)
        rows.append(
            StatusRow(
                source_case_key=case_key,
                case_key=display_case_key(case_key),
                label=gate.get("label") or case_key,
                gate_latest_solver_time_s=format_time(gate.get("gate_latest_time_s", "")),
                latest_registered_timestep_s=latest_written,
                latest_log_time_s=latest_log_time(registry.get("source_root", "")),
                post_restart_advance=seconds_with_minsec(gate.get("gate_advance_s", "")),
                status=status_sentence(gate, rec),
                registry_source_root=registry.get("source_root", ""),
                closure_fit_admissible="yes" if closure_admitted else gate.get("closure_fit_admissible", ""),
                future_fit_label="closure-fit admissible" if closure_admitted else rec.get("future_fit_label", "sensitivity/correlation-support"),
            )
        )
    return rows


def row_to_dict(row: StatusRow) -> dict[str, str]:
    return {
        "case_key": row.case_key,
        "source_case_key": row.source_case_key,
        "row": row.label,
        "gate_latest_solver_time": row.gate_latest_solver_time_s,
        "latest_registered_timestep": row.latest_registered_timestep_s,
        "latest_log_time": row.latest_log_time_s,
        "post_restart_advance_so_far": row.post_restart_advance,
        "status": row.status,
        "closure_fit_admissible": row.closure_fit_admissible,
        "future_fit_label": row.future_fit_label,
        "registry_source_root": row.registry_source_root,
    }


def markdown_table(rows: list[StatusRow], title: str) -> str:
    csv_rows = [row_to_dict(row) for row in rows]
    headers = [
        "Row",
        "Gate latest time",
        "Latest registered timestep",
        "Latest log time",
        "Post-restart advance so far",
        "Status",
    ]
    body_rows = [
        [
            row["row"],
            row["gate_latest_solver_time"],
            row["latest_registered_timestep"],
            row["latest_log_time"],
            row["post_restart_advance_so_far"],
            row["status"],
        ]
        for row in csv_rows
    ]
    widths = [
        max(len(headers[idx]), *(len(body[idx]) for body in body_rows)) if body_rows else len(headers[idx])
        for idx in range(len(headers))
    ]

    def fmt(values: list[str]) -> str:
        return "| " + " | ".join(value.ljust(widths[idx]) for idx, value in enumerate(values)) + " |"

    lines = [
        f"# {title}",
        "",
        "Rows are sourced from `registry/case_registry.csv`; gate/status fields are joined from the completed 3280969 Salt-Q gate and minimal continuation plan. `Latest registered timestep` is scanned from each registered case root, while `Latest log time` is parsed from recent `logs/log.foamRun*` tails when present. Short row names omit the historical `corrected` staging suffix; source keys remain in CSV outputs for provenance. Current coordinator policy admits converged/stationary terminal-window perturbation rows to closure fitting.",
        "",
        fmt(headers),
        "| " + " | ".join("-" * width for width in widths) + " |",
    ]
    lines.extend(fmt(row) for row in body_rows)
    lines.append("")
    return "\n".join(lines)


def registry_coverage_rows(
    registry_rows: list[dict[str, str]], manifest_rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    registered = index_by(corrected_registry_rows(registry_rows), "source_id")
    coverage: list[dict[str, str]] = []
    for manifest in manifest_rows:
        case_key = manifest["case_key"]
        reg = registered.get(case_key, {})
        source_root = reg.get("source_root", "")
        manifest_dir = manifest.get("case_dir", "")
        issue = ""
        if not reg:
            issue = "missing_from_registry"
        elif source_root != manifest_dir:
            issue = "source_root_mismatch"
        else:
            issue = "ok"
        coverage.append(
            {
                "case_key": case_key,
                "registered": "yes" if reg else "no",
                "registry_source_id": reg.get("source_id", ""),
                "registry_source_root": source_root,
                "manifest_case_dir": manifest_dir,
                "issue": issue,
            }
        )
    return coverage


def write_outputs(args: argparse.Namespace) -> int:
    registry_rows = read_csv(Path(args.registry))
    manifest_rows = read_csv(Path(args.manifest))
    gate_rows = read_csv(Path(args.gate))
    recommendation_rows = read_csv(Path(args.recommendations))

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    selected_case_keys = args.case_key if args.case_key is not None else DEFAULT_SELECTED_CASE_KEYS
    selected_rows = build_status_rows(
        registry_rows,
        gate_rows,
        recommendation_rows,
        selected_case_keys,
    )
    all_rows = build_status_rows(
        registry_rows,
        gate_rows,
        recommendation_rows,
        [],
    )
    fieldnames = list(row_to_dict(selected_rows[0]).keys()) if selected_rows else [
        "case_key",
        "source_case_key",
        "row",
        "gate_latest_solver_time",
        "latest_registered_timestep",
        "latest_log_time",
        "post_restart_advance_so_far",
        "status",
        "closure_fit_admissible",
        "future_fit_label",
        "registry_source_root",
    ]

    write_csv(output_dir / "selected_corrected_q_status_table.csv", [row_to_dict(row) for row in selected_rows], fieldnames)
    (output_dir / "selected_corrected_q_status_table.md").write_text(
        markdown_table(selected_rows, "Selected Corrected Salt Q Status Table"),
        encoding="utf-8",
    )
    write_csv(output_dir / "all_corrected_q_status_table.csv", [row_to_dict(row) for row in all_rows], fieldnames)
    (output_dir / "all_corrected_q_status_table.md").write_text(
        markdown_table(all_rows, "All Registered Corrected Salt Q Status Table"),
        encoding="utf-8",
    )
    write_csv(
        output_dir / "corrected_q_latest_timesteps.csv",
        [row_to_dict(row) for row in all_rows],
        fieldnames,
    )

    coverage = registry_coverage_rows(registry_rows, manifest_rows)
    write_csv(
        output_dir / "corrected_q_registry_coverage.csv",
        coverage,
        ["case_key", "registered", "registry_source_id", "registry_source_root", "manifest_case_dir", "issue"],
    )

    missing = [row for row in coverage if row["issue"] != "ok"]
    if args.strict_registry and missing:
        return 1
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--gate", default=str(DEFAULT_GATE))
    parser.add_argument("--recommendations", default=str(DEFAULT_RECOMMENDATIONS))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--case-key",
        action="append",
        default=None,
        help="Case key to include in the selected table. Repeat to set a custom selection. Defaults to the three requested Salt1 -10Q, Salt1 +10Q, and Salt4 +10Q rows.",
    )
    parser.add_argument("--strict-registry", action="store_true")
    return parser.parse_args()


def main() -> int:
    return write_outputs(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
