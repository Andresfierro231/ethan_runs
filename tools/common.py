from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
DEFAULT_FIGURE_FORMATS = ("png", "svg", "pdf")


def require_yaml() -> Any:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "PyYAML is required for this workflow. Install it in the active "
            "Python environment before running these scripts."
        ) from exc
    return yaml


def load_yaml(path: Path) -> Any:
    yaml = require_yaml()
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def iso_timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def date_stamp() -> str:
    return datetime.now().astimezone().date().isoformat()


def slugify(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in value.strip())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")


def load_workspace_config() -> dict[str, Any]:
    return load_yaml(WORKSPACE_ROOT / "config" / "workspace_paths.yaml")


def resolve_workspace_path(value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    return (WORKSPACE_ROOT / candidate).resolve()


def read_registry_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def write_registry_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def upsert_registry_row(path: Path, row: dict[str, str]) -> None:
    fieldnames = list(row.keys())
    rows = read_registry_rows(path)
    filtered = [item for item in rows if item.get("source_id") != row["source_id"]]
    filtered.append(row)
    filtered.sort(key=lambda item: item["source_id"])
    write_registry_rows(path, fieldnames, filtered)


def get_registry_row(path: Path, source_id: str) -> dict[str, str]:
    for row in read_registry_rows(path):
        if row.get("source_id") == source_id:
            return row
    raise KeyError(f"source_id not found in registry: {source_id}")


def load_case_metadata(source_root: Path) -> dict[str, Any]:
    config_path = source_root / "case_config.yaml"
    if not config_path.exists():
        return {}
    return load_yaml(config_path) or {}


def path_lookup(data: dict[str, Any], dotted_path: str, default: Any = "") -> Any:
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def top_level_key_files(source_root: Path) -> list[str]:
    preferred = ["case_config.yaml", "0", "constant", "system", "postProcessing"]
    return [name for name in preferred if (source_root / name).exists()]


def source_size_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size

    total = 0
    stack = [path]
    while stack:
        current = stack.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    stack.append(Path(entry.path))
                else:
                    total += entry.stat(follow_symlinks=False).st_size
    return total


def json_dump(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=False)
        handle.write("\n")


def csv_dump(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def figure_bundle_paths(
    output_root: Path,
    stem: str,
    formats: tuple[str, ...] = DEFAULT_FIGURE_FORMATS,
) -> dict[str, Path]:
    figure_root = ensure_dir(output_root / "figures")
    paths: dict[str, Path] = {}
    for fmt in formats:
        fmt_dir = ensure_dir(figure_root / fmt)
        paths[fmt] = fmt_dir / f"{stem}.{fmt}"
    return paths


def save_matplotlib_figure(
    fig: Any,
    output_root: Path,
    stem: str,
    dpi: int = 200,
    formats: tuple[str, ...] = DEFAULT_FIGURE_FORMATS,
) -> dict[str, str]:
    paths = figure_bundle_paths(output_root, stem, formats=formats)
    for fmt, path in paths.items():
        save_kwargs: dict[str, Any] = {}
        if fmt == "png":
            save_kwargs["dpi"] = dpi
        fig.savefig(path, **save_kwargs)
    return {fmt: str(path) for fmt, path in paths.items()}


def relative_to_workspace(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(WORKSPACE_ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE_RE.sub("", text)


def safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def base_case_id(case_id: str) -> str:
    for suffix in ("_jin", "_kirst"):
        if case_id.endswith(suffix):
            return case_id[: -len(suffix)]
    return case_id


def case_variant_label(case_id: str) -> str:
    for suffix in ("_jin", "_kirst"):
        if case_id.endswith(suffix):
            return suffix.lstrip("_")
    return ""


def parse_scalar_series(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) < 2:
                continue
            time_value = safe_float(parts[0])
            scalar_value = safe_float(parts[1])
            if time_value is None or scalar_value is None:
                continue
            rows.append({"time": time_value, "value": scalar_value})
    return rows


def parse_vol_field_series(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    if not path.exists():
        return rows
    pattern = re.compile(r"^\s*([^\s]+)\s+\(([^)]+)\)\s+([^\s]+)\s+([^\s]+)\s*$")
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = pattern.match(stripped)
            if not match:
                continue
            time_value = safe_float(match.group(1))
            vector_parts = [safe_float(part, 0.0) for part in match.group(2).split()]
            mag_u = safe_float(match.group(3))
            temp_k = safe_float(match.group(4))
            if time_value is None or mag_u is None or temp_k is None or len(vector_parts) != 3:
                continue
            rows.append(
                {
                    "time": time_value,
                    "Ux": vector_parts[0] or 0.0,
                    "Uy": vector_parts[1] or 0.0,
                    "Uz": vector_parts[2] or 0.0,
                    "magU": mag_u,
                    "T": temp_k,
                }
            )
    return rows


def parse_probe_series(path: Path) -> dict[str, Any]:
    probe_positions: list[str] = []
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return {"probe_positions": probe_positions, "rows": rows}

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("# Probe"):
                probe_positions.append(stripped)
                continue
            if stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) < 2:
                continue
            time_value = safe_float(parts[0])
            values = [safe_float(part) for part in parts[1:]]
            if time_value is None or any(value is None for value in values):
                continue
            rows.append({"time": time_value, "values": values})
    return {"probe_positions": probe_positions, "rows": rows}


def parse_convergence_summary(path: Path) -> dict[str, Any]:
    summary = {
        "reached": False,
        "iteration": "",
        "dTmean": "",
        "dTsigma": "",
        "dUmean": "",
        "tol": "",
    }
    if not path.exists():
        return summary

    pattern = re.compile(
        r"\*\*\*\s+convergenceMonitor:\s+CONVERGED at iteration\s+(\d+)\s+\|\s+"
        r"dTmean=([^\s]+)\s+dTsigma=([^\s]+)\s+dUmean=([^\s]+)\s+\(tol=([^)]+)\)"
    )
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = strip_ansi(raw_line.rstrip("\n"))
            match = pattern.search(line)
            if not match:
                continue
            summary = {
                "reached": True,
                "iteration": int(match.group(1)),
                "dTmean": safe_float(match.group(2), match.group(2)),
                "dTsigma": safe_float(match.group(3), match.group(3)),
                "dUmean": safe_float(match.group(4), match.group(4)),
                "tol": safe_float(match.group(5), match.group(5)),
            }
    return summary


def parse_log_summary(path: Path) -> dict[str, Any]:
    summary = {
        "job_id": "",
        "source_case_path": "",
        "nprocs": "",
        "start_date": "",
        "start_time": "",
        "status": "unknown",
        "termination_reason": "",
        "final_time_marker": "",
        "convergence": parse_convergence_summary(path),
    }
    if not path.exists():
        summary["status"] = "missing"
        summary["termination_reason"] = "log file not found"
        return summary

    time_marker_pattern = re.compile(r"^\s*Time =\s*(.+?)\s*$")
    saw_end = False
    saw_finalising = False
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = strip_ansi(raw_line.rstrip("\n"))
            if line.startswith("TACC:  Starting up job"):
                summary["job_id"] = line.split()[-1]
            elif line.startswith("Case   :"):
                summary["source_case_path"] = line.split(":", 1)[1].strip()
            elif line.startswith("nProcs :"):
                summary["nprocs"] = line.split(":", 1)[1].strip()
            elif line.startswith("Date   :"):
                summary["start_date"] = line.split(":", 1)[1].strip()
            elif line.startswith("Time   :"):
                summary["start_time"] = line.split(":", 1)[1].strip()
            elif line.strip() == "End":
                saw_end = True
            elif "Finalising parallel run" in line:
                saw_finalising = True
            elif "BAD TERMINATION OF ONE OF YOUR APPLICATION PROCESSES" in line:
                summary["status"] = "terminated"
            elif "KILLED BY SIGNAL:" in line:
                summary["status"] = "terminated"
                summary["termination_reason"] = line.split("KILLED BY SIGNAL:", 1)[1].strip()

            time_match = time_marker_pattern.match(line)
            if time_match:
                summary["final_time_marker"] = time_match.group(1)

    if saw_end or saw_finalising:
        summary["status"] = "completed"
        summary["termination_reason"] = "normal"

    if summary["status"] == "unknown":
        summary["status"] = "incomplete"
        summary["termination_reason"] = summary["termination_reason"] or "no explicit completion marker found"
    return summary
