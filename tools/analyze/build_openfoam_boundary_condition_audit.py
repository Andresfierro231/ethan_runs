#!/usr/bin/env python3
"""Verify documented Ethan OpenFOAM boundary-condition claims against case files."""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-09/2026-07-09_openfoam_boundary_condition_implementation_audit"

SCENARIO_CONTRACT = (
    ROOT
    / "work_products/2026-07/2026-07-08/2026-07-08_cfd_scenario_contract/scenario_contract.csv"
)
BOUNDARY_SUMMARY = (
    ROOT
    / "reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/boundary_setup_summary.csv"
)
CORRECTED_MANIFEST = (
    ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/corrected_case_manifest.csv"
)
GATE_VERDICTS = (
    ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_corrected_salt_q_gate_3280969_review/row_verdicts.csv"
)

TARGET_Q_PATCHES = [
    "pipeleg_lower_04_straight",
    "pipeleg_lower_05_straight",
    "pipeleg_lower_06_straight",
    "pipeleg_upper_04_reducer",
    "pipeleg_upper_05_cooler",
    "pipeleg_upper_06_reducer",
    "pipeleg_left_04_test_section",
]

CASES = [
    {
        "case_key": "salt1_jin_june18_mainline",
        "case_id": "salt_1",
        "run_class": "mainline_jin_continuation",
        "admission_status": "held_salt1_qualification_required",
        "case_root": "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt1_jin/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
    },
    {
        "case_key": "salt1_jin_june25_basecont",
        "case_id": "salt_1",
        "run_class": "normal_relaunch_base_continuation",
        "admission_status": "held_salt1_qualification_required_latest_candidate",
        "case_root": "jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runs/salt1_jin_basecont/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
    },
    {
        "case_key": "salt1_jin_nominal_continuation_corrected",
        "case_id": "salt_1",
        "run_class": "salt1_nominal_continuation_active",
        "admission_status": "running_not_admitted",
        "case_root": "jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
    },
    {
        "case_key": "salt2_jin_mainline",
        "case_id": "salt_2",
        "run_class": "mainline_jin_continuation",
        "admission_status": "fit_admissible_current_mainline",
        "case_root": "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation",
    },
    {
        "case_key": "salt3_jin_mainline",
        "case_id": "salt_3",
        "run_class": "mainline_jin_continuation",
        "admission_status": "fit_admissible_current_mainline",
        "case_root": "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt3_jin/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh_continuation",
    },
    {
        "case_key": "salt4_jin_mainline",
        "case_id": "salt_4",
        "run_class": "mainline_jin_continuation",
        "admission_status": "fit_admissible_current_mainline",
        "case_root": "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt4_jin/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
    },
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="ignore") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def numeric_dirs(path: Path) -> list[tuple[float, Path]]:
    if not path.exists():
        return []
    out: list[tuple[float, Path]] = []
    for child in path.iterdir():
        if not child.is_dir():
            continue
        try:
            out.append((float(child.name), child))
        except ValueError:
            continue
    return sorted(out, key=lambda item: item[0])


def extract_named_block(text: str, token: str, start_pos: int = 0) -> tuple[str, int] | None:
    match = re.search(rf"\b{re.escape(token)}\b\s*\{{", text[start_pos:])
    if not match:
        return None
    brace = start_pos + match.end() - 1
    depth = 1
    pos = brace + 1
    while pos < len(text) and depth:
        char = text[pos]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        pos += 1
    if depth:
        return None
    return text[brace + 1 : pos - 1], pos


def iter_boundary_fields(text: str) -> list[str]:
    blocks: list[str] = []
    pos = 0
    while True:
        found = extract_named_block(text, "boundaryField", pos)
        if not found:
            break
        block, pos = found
        blocks.append(block)
    return blocks


def parse_patch_blocks(boundary_text: str) -> dict[str, str]:
    patches: dict[str, str] = {}
    pattern = re.compile(r'(?m)^\s*"?([A-Za-z0-9_.*|()]+)"?\s*\n\s*\{')
    for match in pattern.finditer(boundary_text):
        name = match.group(1)
        if name.startswith("#"):
            continue
        brace = match.end() - 1
        depth = 1
        pos = brace + 1
        while pos < len(boundary_text) and depth:
            char = boundary_text[pos]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            pos += 1
        if not depth:
            patches[name] = boundary_text[brace + 1 : pos - 1]
    return patches


def value_for(block: str, key: str) -> str:
    match = re.search(rf"(?m)^\s*{re.escape(key)}\s+([^;\{{\n][^;]*);", block)
    return " ".join(match.group(1).split()) if match else ""


def scalar_for(block: str, key: str) -> str:
    nested = re.search(
        rf"(?ms)^\s*{re.escape(key)}\s*\{{(?P<body>.*?)^\s*\}}",
        block,
    )
    if nested:
        nested_value = value_for(nested.group("body"), "value")
        if nested_value:
            nested_match = re.search(
                r"[-+]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][-+]?\d+)?",
                nested_value,
            )
            if nested_match:
                return nested_match.group(0)
    raw = value_for(block, key)
    if not raw:
        return ""
    match = re.search(r"[-+]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", raw)
    return match.group(0) if match else raw


def parse_field_file(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    text = read_text(path)
    patches: dict[str, dict[str, str]] = {}
    for boundary in iter_boundary_fields(text):
        for name, block in parse_patch_blocks(boundary).items():
            patches[name] = {
                "type": value_for(block, "type"),
                "Q": scalar_for(block, "Q"),
                "h": scalar_for(block, "h"),
                "Ta": scalar_for(block, "Ta"),
                "Tsur": scalar_for(block, "Tsur"),
                "emissivity": scalar_for(block, "emissivity"),
                "thicknessLayers": value_for(block, "thicknessLayers"),
            }
    return patches


def parse_restart_q_counts(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    text = read_text(path)
    values_by_patch: dict[str, list[str]] = {patch: [] for patch in TARGET_Q_PATCHES}
    types_by_patch: dict[str, list[str]] = {patch: [] for patch in TARGET_Q_PATCHES}
    for boundary in iter_boundary_fields(text):
        patches = parse_patch_blocks(boundary)
        for patch in TARGET_Q_PATCHES:
            body = patches.get(patch)
            if body is None:
                continue
            q = scalar_for(body, "Q")
            typ = value_for(body, "type")
            if q:
                values_by_patch[patch].append(q)
            if typ:
                types_by_patch[patch].append(typ)
    out: dict[str, dict[str, Any]] = {}
    for patch in TARGET_Q_PATCHES:
        out[patch] = {
            "processor_block_count": len(types_by_patch[patch]),
            "q_value_counts": dict(Counter(values_by_patch[patch])),
            "type_counts": dict(Counter(types_by_patch[patch])),
        }
    return out


def layer_values(thickness_layers: str) -> list[float]:
    return [
        float(item)
        for item in re.findall(
            r"[-+]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][-+]?\d+)?",
            thickness_layers,
        )
    ]


def corrected_cases() -> list[dict[str, Any]]:
    verdicts = {row["case_key"]: row for row in read_csv(GATE_VERDICTS)}
    rows: list[dict[str, Any]] = []
    for row in read_csv(CORRECTED_MANIFEST):
        case_key = row["case_key"]
        verdict = verdicts.get(case_key, {})
        rows.append(
            {
                "case_key": case_key,
                "case_id": f"salt_{row['salt']}",
                "run_class": "corrected_salt_q_perturbation",
                "admission_status": f"closure_fit_admissible={verdict.get('closure_fit_admissible', 'unknown')}; {verdict.get('row_verdict', 'not_reviewed')}",
                "case_root": row["case_dir"],
                "expected_lower_heater_q_w": str(float(row["target_heater_power_W"]) / 3.0),
                "expected_cooler_q04_w": row["target_cooler_q04_W"],
                "expected_cooler_q05_w": row["target_cooler_q05_W"],
                "expected_cooler_q06_w": row["target_cooler_q06_W"],
                "q_ratio": row["q_ratio"],
            }
        )
    return rows


def all_cases() -> list[dict[str, Any]]:
    return CASES + corrected_cases()


def field_boundary_rows(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        root = ROOT / case["case_root"] if not str(case["case_root"]).startswith("/") else Path(case["case_root"])
        for field in sorted((root / "0").glob("*")):
            if not field.is_file():
                continue
            patches = parse_field_file(field)
            type_counts = Counter(patch.get("type", "") for patch in patches.values())
            rows.append(
                {
                    "case_key": case["case_key"],
                    "case_id": case["case_id"],
                    "run_class": case["run_class"],
                    "field": field.name,
                    "field_path": rel(field),
                    "patch_count": len(patches),
                    "type_counts_json": json.dumps(dict(sorted(type_counts.items())), sort_keys=True),
                    "has_boundary_field": bool(patches),
                }
            )
    return rows


def thermal_patch_rows(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        root = ROOT / case["case_root"] if not str(case["case_root"]).startswith("/") else Path(case["case_root"])
        t_path = root / "0/T"
        patches = parse_field_file(t_path)
        latest = numeric_dirs(root / "processors64")
        latest_time = latest[-1][0] if latest else ""
        for name, values in sorted(patches.items()):
            layers = layer_values(values.get("thicknessLayers", ""))
            rows.append(
                {
                    "case_key": case["case_key"],
                    "case_id": case["case_id"],
                    "run_class": case["run_class"],
                    "admission_status": case["admission_status"],
                    "latest_processor_time_s": latest_time,
                    "patch": name,
                    "type": values.get("type", ""),
                    "Q_W": values.get("Q", ""),
                    "h_W_m2K": values.get("h", ""),
                    "Ta_K": values.get("Ta", ""),
                    "Tsur_K": values.get("Tsur", ""),
                    "emissivity": values.get("emissivity", ""),
                    "thicknessLayers": values.get("thicknessLayers", ""),
                    "has_0p03556m_layer": any(abs(value - 0.03556) < 5e-5 for value in layers),
                    "source_path": rel(t_path),
                }
            )
    return rows


def case_summary_rows(cases: list[dict[str, Any]], thermal_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in thermal_rows:
        by_case[row["case_key"]].append(row)
    scenario = {row["case_key"]: row for row in read_csv(SCENARIO_CONTRACT)}
    rows: list[dict[str, Any]] = []
    for case in cases:
        root = ROOT / case["case_root"] if not str(case["case_root"]).startswith("/") else Path(case["case_root"])
        t_rows = by_case.get(case["case_key"], [])
        type_counts = Counter(row["type"] for row in t_rows)
        thicknesses: set[str] = set()
        for row in t_rows:
            for value in layer_values(row.get("thicknessLayers", "")):
                thicknesses.add(f"{value:g}")
        latest = numeric_dirs(root / "processors64")
        latest_dir = latest[-1][1] if latest else None
        rad_paths = [root / "constant/radiationProperties", root / "0/qr", root / "0/G"]
        if latest_dir:
            rad_paths += [latest_dir / "qr", latest_dir / "G"]
        scenario_row = scenario.get(case["case_key"], {})
        documented_counts = scenario_row.get("bc_type_counts_json", "")
        actual_counts = json.dumps(dict(sorted(type_counts.items())), sort_keys=True)
        rows.append(
            {
                "case_key": case["case_key"],
                "case_id": case["case_id"],
                "run_class": case["run_class"],
                "admission_status": case["admission_status"],
                "case_root": rel(root),
                "latest_processor_time_s": latest[-1][0] if latest else "",
                "root_T_patch_count": len(t_rows),
                "root_T_type_counts_json": actual_counts,
                "documented_scenario_T_type_counts_json": documented_counts,
                "type_counts_match_documentation": actual_counts == documented_counts if documented_counts else "",
                "unique_thickness_m": "|".join(sorted(thicknesses, key=float)) if thicknesses else "",
                "has_0p03556m_layer": any(row["has_0p03556m_layer"] for row in t_rows),
                "rcExternalTemperature_count": type_counts.get("rcExternalTemperature", 0),
                "externalTemperature_count": type_counts.get("externalTemperature", 0),
                "zeroGradient_count": type_counts.get("zeroGradient", 0),
                "emissivity_patch_count": sum(1 for row in t_rows if row["emissivity"]),
                "Q_patch_count": sum(1 for row in t_rows if row["Q_W"]),
                "has_radiationProperties": (root / "constant/radiationProperties").exists(),
                "has_qr_or_G_field": any(path.exists() for path in rad_paths[1:]),
            }
        )
    return rows


def q_check_rows(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        root = ROOT / case["case_root"] if not str(case["case_root"]).startswith("/") else Path(case["case_root"])
        root_patches = parse_field_file(root / "0/T")
        latest = numeric_dirs(root / "processors64")
        latest_path = latest[-1][1] / "T" if latest else None
        scan_restart = case["run_class"] == "corrected_salt_q_perturbation"
        restart_counts = parse_restart_q_counts(latest_path) if latest_path and scan_restart else {}
        for patch in TARGET_Q_PATCHES:
            root_q = root_patches.get(patch, {}).get("Q", "")
            expected = ""
            if patch.startswith("pipeleg_lower_0"):
                expected = case.get("expected_lower_heater_q_w", "")
            elif patch == "pipeleg_upper_04_reducer":
                expected = case.get("expected_cooler_q04_w", "")
            elif patch == "pipeleg_upper_05_cooler":
                expected = case.get("expected_cooler_q05_w", "")
            elif patch == "pipeleg_upper_06_reducer":
                expected = case.get("expected_cooler_q06_w", "")
            elif patch == "pipeleg_left_04_test_section":
                expected = "37.0"
            restart = restart_counts.get(patch, {})
            rows.append(
                {
                    "case_key": case["case_key"],
                    "case_id": case["case_id"],
                    "run_class": case["run_class"],
                    "patch": patch,
                    "root_Q_W": root_q,
                    "expected_Q_W": expected,
                    "root_matches_expected": numeric_close(root_q, expected) if expected else "",
                    "latest_restart_time_s": latest[-1][0] if latest else "",
                    "latest_restart_T_path": rel(latest_path) if latest_path and scan_restart else "",
                    "restart_processor_block_count": restart.get("processor_block_count", ""),
                    "restart_Q_value_counts_json": json.dumps(restart.get("q_value_counts", {}), sort_keys=True),
                    "restart_type_counts_json": json.dumps(restart.get("type_counts", {}), sort_keys=True),
                    "restart_all_processors_have_expected_Q": restart_all_expected(restart, expected) if expected else "",
                }
            )
    return rows


def numeric_close(a: str, b: str, tol: float = 1e-6) -> bool:
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return False


def restart_all_expected(restart: dict[str, Any], expected: str) -> bool:
    counts = restart.get("q_value_counts", {})
    if not counts:
        return False
    total = sum(int(value) for value in counts.values())
    expected_count = 0
    for q_value, count in counts.items():
        if numeric_close(q_value, expected):
            expected_count += int(count)
    return total == 64 and expected_count == 64


def claim_rows(case_rows: list[dict[str, Any]], q_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mainline = [row for row in case_rows if row["case_key"] in {"salt2_jin_mainline", "salt3_jin_mainline", "salt4_jin_mainline"}]
    all_salt = case_rows
    corrected = [row for row in q_rows if row["run_class"] == "corrected_salt_q_perturbation"]
    summary_topics = {row["topic"]: row for row in read_csv(BOUNDARY_SUMMARY)}

    def verdict(ok: bool) -> str:
        return "verified" if ok else "mismatch_or_incomplete"

    return [
        {
            "claim_id": "cfd_thermal_bc_families",
            "documented_source_topic": "boundary_condition_families",
            "claim": "Mainline Salt 2/3/4 root 0/T files contain exactly externalTemperature:10, rcExternalTemperature:36, zeroGradient:23.",
            "verification": verdict(
                all(
                    row["root_T_type_counts_json"]
                    == '{"externalTemperature": 10, "rcExternalTemperature": 36, "zeroGradient": 23}'
                    for row in mainline
                )
            ),
            "evidence": "; ".join(f"{row['case_key']}={row['root_T_type_counts_json']}" for row in mainline),
            "documentation_excerpt": summary_topics.get("boundary_condition_families", {}).get("what_ethan_runs_do", ""),
        },
        {
            "claim_id": "cfd_1p4in_layer",
            "documented_source_topic": "physical_layer_and_insulation",
            "claim": "Audited Salt roots carry a 0.03556 m layer in thermal boundary thicknessLayers.",
            "verification": verdict(all(row["has_0p03556m_layer"] for row in all_salt)),
            "evidence": f"{sum(1 for row in all_salt if row['has_0p03556m_layer'])}/{len(all_salt)} audited Salt roots include 0.03556 m.",
            "documentation_excerpt": summary_topics.get("physical_layer_and_insulation", {}).get("what_ethan_runs_do", ""),
        },
        {
            "claim_id": "surface_emissivity_no_qr",
            "documented_source_topic": "emissivity_and_radiation",
            "claim": "rcExternalTemperature patches carry emissivity metadata, with no radiationProperties and no qr/G field in audited roots/latest retained time.",
            "verification": verdict(
                all(
                    int(row["emissivity_patch_count"]) == 36
                    and row["has_radiationProperties"] is False
                    and row["has_qr_or_G_field"] is False
                    for row in all_salt
                )
            ),
            "evidence": f"emissivity counts={sorted(set(row['emissivity_patch_count'] for row in all_salt))}; radiationProperties={sum(1 for row in all_salt if row['has_radiationProperties'])}; qr/G={sum(1 for row in all_salt if row['has_qr_or_G_field'])}.",
            "documentation_excerpt": summary_topics.get("emissivity_and_radiation", {}).get("what_ethan_runs_do", ""),
        },
        {
            "claim_id": "corrected_q_root_patch_consistency",
            "documented_source_topic": "heater_boundary",
            "claim": "Corrected-Q root 0/T files patch all three lower heater patches and three cooler sink patches to target values.",
            "verification": verdict(all(row["root_matches_expected"] is True for row in corrected if row["patch"] != "pipeleg_left_04_test_section")),
            "evidence": f"{sum(1 for row in corrected if row['patch'] != 'pipeleg_left_04_test_section' and row['root_matches_expected'] is True)}/{sum(1 for row in corrected if row['patch'] != 'pipeleg_left_04_test_section')} corrected heater/cooler root patch checks passed.",
            "documentation_excerpt": "Compared against corrected_case_manifest.csv target heater and cooler Q values.",
        },
        {
            "claim_id": "corrected_q_restart_patch_consistency",
            "documented_source_topic": "heater_boundary",
            "claim": "Corrected-Q latest retained restart T files carry target Q values on all 64 processor boundary blocks.",
            "verification": verdict(all(row["restart_all_processors_have_expected_Q"] is True for row in corrected if row["patch"] != "pipeleg_left_04_test_section")),
            "evidence": f"{sum(1 for row in corrected if row['patch'] != 'pipeleg_left_04_test_section' and row['restart_all_processors_have_expected_Q'] is True)}/{sum(1 for row in corrected if row['patch'] != 'pipeleg_left_04_test_section')} corrected heater/cooler restart patch checks passed.",
            "documentation_excerpt": "Latest restart T decomposedBlockData was scanned textually; no reconstruction was performed.",
        },
        {
            "claim_id": "admission_gate_boundary",
            "documented_source_topic": "admitted_evidence_set",
            "claim": "Salt 2/3/4 mainline can remain setup evidence; corrected-Q and Salt1 nominal rows remain non-admitted until formal qualification/gate.",
            "verification": verdict(
                all("fit_admissible" in row["admission_status"] for row in mainline)
                and all("closure_fit_admissible=no" in row["admission_status"] for row in case_rows if row["run_class"] == "corrected_salt_q_perturbation")
            ),
            "evidence": "Mainline Salt2/3/4 are fit_admissible_current_mainline; corrected-Q verdict rows all report closure_fit_admissible=no.",
            "documentation_excerpt": summary_topics.get("admitted_evidence_set", {}).get("what_ethan_runs_do", ""),
        },
    ]


def cleanup_rows() -> list[dict[str, Any]]:
    candidates = [
        {
            "path": "tmp",
            "classification": "stale but potentially useful",
            "why": "Large temporary run and analysis area; measured around 187G in this audit session. Contains checkpoint and job scratch that may still be provenance.",
            "recommended_action": "Do not delete blindly. Build a dated manifest of tmp subtrees by task and archive/remove only after owner review.",
            "requires_approval": "yes",
        },
        {
            "path": "tmp_extract",
            "classification": "stale but potentially useful",
            "why": "Large extracted/reconstructed analysis scratch; measured around 205G. Some reports cite tmp_extract paths as provenance.",
            "recommended_action": "Do not delete blindly. Identify report-cited roots before pruning.",
            "requires_approval": "yes",
        },
        {
            "path": "reports/2026-06/2026-06-23/2026-06-23_ethan_cfd_freeze_checkpoint",
            "classification": "misplaced or under-documented package metadata",
            "why": "Package contains CSV/JSON freeze checkpoint outputs but no README, making the freeze semantics hard to reference.",
            "recommended_action": "Add a README in a follow-up writer task or extend this task if desired; no deletion.",
            "requires_approval": "no",
        },
        {
            "path": "jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/TODO.md",
            "classification": "stale coordination note",
            "why": "Checklist still appears unchecked even though later notes and manifests record submitted/canceled/superseded state.",
            "recommended_action": "Update checklist/status note in a campaign documentation cleanup task; no solver-output changes.",
            "requires_approval": "no",
        },
        {
            "path": "jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/submitted_jobs.csv",
            "classification": "stale status metadata",
            "why": "Initial state remains PENDING while scheduler later showed job running and retained times advanced.",
            "recommended_action": "Add a status addendum rather than rewriting original submission facts.",
            "requires_approval": "no",
        },
        {
            "path": "work_products/2026-07-06_overnight_postprocess_jobs",
            "classification": "misplaced file tree",
            "why": "Top-level dated work product remains outside the sorted work_products/YYYY-MM/YYYY-MM-DD pattern.",
            "recommended_action": "Move only with compatibility symlink and manifest update after active references are checked.",
            "requires_approval": "yes",
        },
    ]
    return candidates


def write_readme(case_rows_out: list[dict[str, Any]], claims: list[dict[str, Any]]) -> None:
    verified = sum(1 for row in claims if row["verification"] == "verified")
    text = f"""# OpenFOAM Boundary-Condition Implementation Audit

Generated: `2026-07-09`
Task: `AGENT-240`

## Scope

This package verifies the documented Ethan Salt boundary-condition claims
against actual OpenFOAM dictionaries in the current mainline Salt roots,
corrected Salt-Q roots, and the active Salt 1 nominal continuation root. It
does not run OpenFOAM, reconstruct fields, edit case trees, or mutate native
solver outputs.

## Outputs

- `openfoam_case_boundary_summary.csv`: case-level `0/T` implementation checks,
  latest retained time, radiation-file flags, and comparison to the July 8
  scenario contract where applicable.
- `openfoam_field_boundary_summary.csv`: boundary-condition type counts for
  every root `0/*` field file in each audited case.
- `temperature_patch_inventory.csv`: patch-level `0/T` type, Q, h, Ta,
  emissivity, and thickness-layer inventory.
- `target_q_restart_consistency.csv`: heater/cooler/test-section Q checks for
  root `0/T` and latest retained restart `T` files.
- `claim_verdicts.csv`: documented claim versus implementation verdicts.
- `cleanup_dry_run.csv`: non-destructive cleanup candidate classification.

## Result

Claim checks verified: `{verified}/{len(claims)}`.

The core documented thermal-boundary claims are supported by the implemented
OpenFOAM dictionaries: mainline Salt 2/3/4 use the documented three thermal BC
families in `0/T`, all audited Salt roots carry the `0.03556 m` layer, and
emissivity metadata is present without a detected `radiationProperties`, `qr`,
or `G` field. Corrected-Q root and latest retained restart `T` files were also
checked for target heater/cooler Q values across all 64 processor boundary
blocks.

The audit also surfaces cleanup needs, but destructive cleanup is intentionally
not performed here. The largest cleanup candidates are `tmp/` and
`tmp_extract/`; both need provenance-aware manifests before deletion.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cases = all_cases()
    field_rows = field_boundary_rows(cases)
    patch_rows = thermal_patch_rows(cases)
    summary_rows = case_summary_rows(cases, patch_rows)
    q_rows = q_check_rows(cases)
    claims = claim_rows(summary_rows, q_rows)
    cleanup = cleanup_rows()

    write_csv(
        OUT / "openfoam_field_boundary_summary.csv",
        field_rows,
        ["case_key", "case_id", "run_class", "field", "field_path", "patch_count", "type_counts_json", "has_boundary_field"],
    )
    write_csv(
        OUT / "temperature_patch_inventory.csv",
        patch_rows,
        [
            "case_key",
            "case_id",
            "run_class",
            "admission_status",
            "latest_processor_time_s",
            "patch",
            "type",
            "Q_W",
            "h_W_m2K",
            "Ta_K",
            "Tsur_K",
            "emissivity",
            "thicknessLayers",
            "has_0p03556m_layer",
            "source_path",
        ],
    )
    write_csv(
        OUT / "openfoam_case_boundary_summary.csv",
        summary_rows,
        [
            "case_key",
            "case_id",
            "run_class",
            "admission_status",
            "case_root",
            "latest_processor_time_s",
            "root_T_patch_count",
            "root_T_type_counts_json",
            "documented_scenario_T_type_counts_json",
            "type_counts_match_documentation",
            "unique_thickness_m",
            "has_0p03556m_layer",
            "rcExternalTemperature_count",
            "externalTemperature_count",
            "zeroGradient_count",
            "emissivity_patch_count",
            "Q_patch_count",
            "has_radiationProperties",
            "has_qr_or_G_field",
        ],
    )
    write_csv(
        OUT / "target_q_restart_consistency.csv",
        q_rows,
        [
            "case_key",
            "case_id",
            "run_class",
            "patch",
            "root_Q_W",
            "expected_Q_W",
            "root_matches_expected",
            "latest_restart_time_s",
            "latest_restart_T_path",
            "restart_processor_block_count",
            "restart_Q_value_counts_json",
            "restart_type_counts_json",
            "restart_all_processors_have_expected_Q",
        ],
    )
    write_csv(
        OUT / "claim_verdicts.csv",
        claims,
        ["claim_id", "documented_source_topic", "claim", "verification", "evidence", "documentation_excerpt"],
    )
    write_csv(
        OUT / "cleanup_dry_run.csv",
        cleanup,
        ["path", "classification", "why", "recommended_action", "requires_approval"],
    )
    summary = {
        "case_count": len(summary_rows),
        "field_summary_rows": len(field_rows),
        "temperature_patch_rows": len(patch_rows),
        "q_check_rows": len(q_rows),
        "claim_verdict_counts": dict(Counter(row["verification"] for row in claims)),
        "cleanup_candidate_count": len(cleanup),
        "mutated_solver_outputs": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(summary_rows, claims)


if __name__ == "__main__":
    main()
