#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

HEATER_PATCHES = [
    "pipeleg_lower_04_straight",
    "pipeleg_lower_05_straight",
    "pipeleg_lower_06_straight",
]
COOLER_PATCHES = [
    "pipeleg_upper_04_reducer",
    "pipeleg_upper_05_cooler",
    "pipeleg_upper_06_reducer",
]


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def latest_time(processors64: Path) -> str:
    times = [p.name for p in processors64.iterdir() if p.is_dir() and re.fullmatch(r"[0-9.]+", p.name)]
    if not times:
        raise RuntimeError(f"No numeric time directories under {processors64}")
    return sorted(times, key=float)[-1]


def patch_block_q(text: str, patch: str, value: float) -> tuple[str, int]:
    lines = text.splitlines()
    out = list(lines)
    count = 0
    i = 0
    while i < len(lines):
        stripped = lines[i].strip().strip('"')
        if stripped != patch:
            i += 1
            continue
        depth = 0
        j = i
        in_q_dict = False
        while j < len(lines):
            depth += lines[j].count("{") - lines[j].count("}")
            if j > i and depth <= 0:
                break
            q_stripped = lines[j].strip()
            if q_stripped == "Q":
                in_q_dict = True
            if q_stripped.startswith("Q") and "constant" in q_stripped and q_stripped.endswith(";"):
                indent = lines[j][: len(lines[j]) - len(lines[j].lstrip())]
                out[j] = f"{indent}Q               constant {value:.15g};"
                count += 1
                break
            if in_q_dict and q_stripped.startswith("value") and j > i:
                indent = lines[j][: len(lines[j]) - len(lines[j].lstrip())]
                out[j] = f"{indent}value           {value:.15g};"
                count += 1
                break
            j += 1
        i = j + 1
    return "\n".join(out) + ("\n" if text.endswith("\n") else ""), count


def patch_file(path: Path, heater_q: float, cooler_values: list[float]) -> dict[str, str]:
    raw = path.read_bytes()
    if b"class       decomposedBlockData" in raw[:2048]:
        return patch_decomposed_block_data(path, raw, heater_q, cooler_values)

    text = raw.decode("utf-8")
    counts: dict[str, str] = {}
    for patch in HEATER_PATCHES:
        text, count = patch_block_q(text, patch, heater_q)
        counts[patch] = str(count)
    for patch, value in zip(COOLER_PATCHES, cooler_values):
        text, count = patch_block_q(text, patch, value)
        counts[patch] = str(count)
    path.write_text(text, encoding="utf-8")
    return counts


def patch_decomposed_block_data(path: Path, raw: bytes, heater_q: float, cooler_values: list[float]) -> dict[str, str]:
    totals: dict[str, int] = {patch: 0 for patch in HEATER_PATCHES + COOLER_PATCHES}
    out = bytearray()
    header = re.compile(rb"// Processor(\d+)\n\n(\d+)\n\(")
    last = 0
    processor_count = 0
    for match in header.finditer(raw):
        processor_count += 1
        pre_start = match.start()
        out += raw[last:pre_start]
        proc = match.group(1)
        count = int(match.group(2))
        block_start = match.end()
        block_end = block_start + count
        if raw[block_end:block_end + 1] != b")":
            raise RuntimeError(f"decomposedBlockData framing mismatch in {path} processor {proc.decode()}")
        text = raw[block_start:block_end].decode("latin-1")
        for patch in HEATER_PATCHES:
            text, patched = patch_block_q(text, patch, heater_q)
            totals[patch] += patched
        for patch, value in zip(COOLER_PATCHES, cooler_values):
            text, patched = patch_block_q(text, patch, value)
            totals[patch] += patched
        new_block = text.encode("latin-1")
        out += b"// Processor" + proc + b"\n\n" + str(len(new_block)).encode("ascii") + b"\n("
        out += new_block
        last = block_end
    if processor_count == 0:
        raise RuntimeError(f"No processor blocks found in decomposedBlockData field: {path}")
    out += raw[last:]
    path.write_bytes(out)
    return {patch: str(count) for patch, count in totals.items()}


def update_case_config(path: Path, heater_power: float, walltime: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^(\s*heater_power_W:\s*)[-+0-9.eE]+", rf"\g<1>{heater_power:.12g}", text, count=1)
    text = re.sub(r"(?m)^(\s*Q:\s*)[-+0-9.eE]+", rf"\g<1>{heater_power:.12g}", text, count=1)
    text = re.sub(r"walltime:\s*'[^']+'", f"walltime: '{walltime}'", text)
    path.write_text(text, encoding="utf-8")


def update_control_dict(path: Path, end_time: float) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^(\s*endTime\s+)[-+0-9.eE]+(\s*;)", rf"\g<1>{end_time:.12g}\2", text, count=1)
    text = re.sub(r"(?m)^(\s*purgeWrite\s+)[-+0-9.eE]+(\s*;)", r"\g<1>21\2", text, count=1)
    path.write_text(text, encoding="utf-8")


def patch_case(row: dict[str, str], patch_processors: bool, processor_time: str = "") -> dict[str, str]:
    case_dir = Path(row["case_dir"])
    heater_power = float(row["target_heater_power_W"])
    heater_q = heater_power / 3.0
    cooler_values = [
        float(row["target_cooler_q04_W"]),
        float(row["target_cooler_q05_W"]),
        float(row["target_cooler_q06_W"]),
    ]
    update_case_config(case_dir / "case_config.yaml", heater_power, row["walltime"])
    update_control_dict(case_dir / "system/controlDict", float(row["target_end_time_s"]))
    root_counts = patch_file(case_dir / "0/T", heater_q, cooler_values)
    proc_counts: dict[str, str] = {}
    restart = ""
    if patch_processors and (case_dir / "processors64").is_dir():
        restart = processor_time or latest_time(case_dir / "processors64")
        proc_counts = patch_file(case_dir / "processors64" / restart / "T", heater_q, cooler_values)
    return {
        "case_key": row["case_key"],
        "case_dir": str(case_dir),
        "restart_time_s": restart,
        "target_heater_power_W": row["target_heater_power_W"],
        "target_heater_patch_Q_W": f"{heater_q:.12g}",
        "root_patch_counts": str(root_counts),
        "processor_patch_counts": str(proc_counts),
        "root_patch_ok": str(all(value == "1" for value in root_counts.values())),
        "processor_patch_ok": str((not patch_processors) or all(int(value) >= 1 for value in proc_counts.values())),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--case-key", action="append", default=[])
    parser.add_argument("--processor-time", default="")
    parser.add_argument("--patch-processors", action="store_true")
    parser.add_argument("--audit-out")
    args = parser.parse_args()
    rows = read_manifest(Path(args.manifest))
    wanted = set(args.case_key)
    audit = []
    for row in rows:
        if wanted and row["case_key"] not in wanted:
            continue
        audit.append(patch_case(row, patch_processors=args.patch_processors, processor_time=args.processor_time))
    if args.audit_out:
        out = Path(args.audit_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(audit[0].keys()) if audit else ["case_key"])
            writer.writeheader()
            writer.writerows(audit)
    for row in audit:
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
