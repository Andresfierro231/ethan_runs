#!/usr/bin/env python3
"""Build a read-only CFD scenario-contract and observation-table audit."""
from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

MAINLINE_CASES = [
    {
        "case_key": "salt1_jin_june18_mainline",
        "case_id": "salt_1",
        "source_id": "viscosity_screening_salt_test_1_jin_coarse_mesh",
        "run_class": "mainline_jin_continuation",
        "fit_use_status": "held_salt1_qualification_required",
        "root": "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt1_jin/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
    },
    {
        "case_key": "salt1_jin_june25_basecont",
        "case_id": "salt_1",
        "source_id": "viscosity_screening_salt_test_1_jin_coarse_mesh",
        "run_class": "normal_relaunch_base_continuation",
        "fit_use_status": "held_salt1_qualification_required_latest_candidate",
        "root": "jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runs/salt1_jin_basecont/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
    },
    {
        "case_key": "salt2_jin_mainline",
        "case_id": "salt_2",
        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "run_class": "mainline_jin_continuation",
        "fit_use_status": "fit_admissible_current_mainline",
        "root": "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation",
    },
    {
        "case_key": "salt3_jin_mainline",
        "case_id": "salt_3",
        "source_id": "viscosity_screening_salt_test_3_jin_coarse_mesh",
        "run_class": "mainline_jin_continuation",
        "fit_use_status": "fit_admissible_current_mainline",
        "root": "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt3_jin/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh_continuation",
    },
    {
        "case_key": "salt4_jin_mainline",
        "case_id": "salt_4",
        "source_id": "viscosity_screening_salt_test_4_jin_coarse_mesh",
        "run_class": "mainline_jin_continuation",
        "fit_use_status": "fit_admissible_current_mainline",
        "root": "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt4_jin/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
    },
]

CORRECTED_ROOT = ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs"

SOURCE_CONTRACT = ROOT / "work_products/2026-06-29_ethan_reduction_contract_audit/source_contract_map.csv"
LIVE_MONITOR = ROOT / "work_products/2026-07-07_corrected_salt_live_monitor/live_salt_sanity_monitor.csv"
PRESSURE_LEDGER = ROOT / "work_products/2026-07-07_pressure_term_ledger/pressure_term_ledger.csv"
HEAT_LEDGER = ROOT / "work_products/2026-07-07_heat_source_sink_ledger/heat_source_sink_ledger.csv"
TIME_WINDOW_OBS = ROOT / "work_products/2026-07-07_time_window_quasi_steady_uq/quasi_steady_observations.csv"

OUT = ROOT / "work_products/2026-07-08_cfd_scenario_contract"


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
            writer.writerow({key: row.get(key, "") for key in fields})


def numeric_dirs(path: Path) -> list[float]:
    if not path.exists():
        return []
    out: list[float] = []
    for child in path.iterdir():
        if not child.is_dir():
            continue
        try:
            out.append(float(child.name))
        except ValueError:
            continue
    return sorted(out)


def block_texts(text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    pattern = re.compile(r"(?m)^\s{4}\"?([A-Za-z0-9_]+)\"?\s*\n\s{4}\{")
    for match in pattern.finditer(text):
        name = match.group(1)
        start = match.end()
        depth = 1
        pos = start
        while pos < len(text) and depth:
            if text[pos] == "{":
                depth += 1
            elif text[pos] == "}":
                depth -= 1
            pos += 1
        blocks.append((name, text[start : pos - 1]))
    return blocks


def parse_layers(value: str) -> list[float]:
    return [float(item) for item in re.findall(r"[-+]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", value)]


def parse_boundary_t(case_root: Path) -> dict[str, Any]:
    t_file = case_root / "0/T"
    if not t_file.exists():
        return {
            "t_boundary_exists": False,
            "bc_type_counts": {},
            "unique_thickness_m": [],
            "has_1p4in_layer": False,
            "rc_external_count": 0,
            "emissivity_patch_count": 0,
            "q_patch_count": 0,
        }
    text = t_file.read_text(encoding="utf-8", errors="ignore")
    type_counts: Counter[str] = Counter()
    unique_layers: set[float] = set()
    emissivity_count = 0
    q_count = 0
    for _name, block in block_texts(text):
        typ = re.search(r"(?m)^\s*type\s+([^;]+);", block)
        if typ:
            type_counts[typ.group(1).strip()] += 1
        if re.search(r"(?m)^\s*emissivity\s+", block):
            emissivity_count += 1
        if re.search(r"(?m)^\s*Q\s+", block):
            q_count += 1
        layers = re.search(r"(?m)^\s*thicknessLayers\s*\(([^;]+)\);", block)
        if layers:
            for value in parse_layers(layers.group(1)):
                unique_layers.add(round(value, 12))
    has_1p4 = any(abs(value - 0.03556) < 5e-5 for value in unique_layers)
    return {
        "t_boundary_exists": True,
        "bc_type_counts": dict(type_counts),
        "unique_thickness_m": sorted(unique_layers),
        "has_1p4in_layer": has_1p4,
        "rc_external_count": type_counts.get("rcExternalTemperature", 0),
        "emissivity_patch_count": emissivity_count,
        "q_patch_count": q_count,
    }


def radiation_files(case_root: Path) -> dict[str, bool]:
    latest = numeric_dirs(case_root / "processors64")
    latest_name = f"{latest[-1]:g}" if latest else ""
    candidates = [
        case_root / "constant/radiationProperties",
        case_root / "0/qr",
        case_root / "0/G",
    ]
    if latest_name:
        candidates.extend([case_root / "processors64" / latest_name / "qr", case_root / "processors64" / latest_name / "G"])
    return {
        "has_radiation_properties": (case_root / "constant/radiationProperties").exists(),
        "has_qr_or_G_field": any(path.exists() for path in candidates[1:]),
    }


def case_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in MAINLINE_CASES:
        rows.append(dict(item))
    live = {row["case_key"]: row for row in read_csv(LIVE_MONITOR)}
    if CORRECTED_ROOT.exists():
        for run_dir in sorted(CORRECTED_ROOT.iterdir()):
            if not run_dir.is_dir():
                continue
            staged = sorted((run_dir / "case_stage").glob("*_continuation"))
            if not staged:
                continue
            live_row = live.get(run_dir.name, {})
            source = re.sub(r"^(salt[1-4])_jin_.*$", r"\1", run_dir.name)
            rows.append(
                {
                    "case_key": run_dir.name,
                    "case_id": source.replace("salt", "salt_"),
                    "source_id": run_dir.name,
                    "run_class": "corrected_salt_q_perturbation",
                    "fit_use_status": "held_until_formal_gate",
                    "root": rel(staged[0]),
                    "job_id": live_row.get("job_id", ""),
                    "job_state": live_row.get("job_state", ""),
                    "needs_special_gate_scrutiny": live_row.get("needs_special_gate_scrutiny", ""),
                    "recommendation": live_row.get("recommendation", ""),
                }
            )
    for row in rows:
        root = ROOT / row["root"]
        times = numeric_dirs(root / "processors64")
        boundary = parse_boundary_t(root)
        rad = radiation_files(root)
        row.update(
            {
                "case_root": rel(root),
                "latest_processor_time_s": times[-1] if times else "",
                "retained_numeric_time_count": len(times),
                "t_boundary_exists": boundary["t_boundary_exists"],
                "bc_type_counts_json": json.dumps(boundary["bc_type_counts"], sort_keys=True),
                "unique_thickness_m": "|".join(f"{value:g}" for value in boundary["unique_thickness_m"]),
                "has_1p4in_insulation_layer": boundary["has_1p4in_layer"],
                "insulation_label": "contains_0.03556m_1.4in_layer" if boundary["has_1p4in_layer"] else "no_1.4in_layer_found",
                "rc_external_patch_count": boundary["rc_external_count"],
                "emissivity_patch_count": boundary["emissivity_patch_count"],
                "q_patch_count": boundary["q_patch_count"],
                "has_radiation_properties": rad["has_radiation_properties"],
                "has_qr_or_G_field": rad["has_qr_or_G_field"],
                "radiation_label": (
                    "surface_emissivity_bc_present_no_volume_radiation_field"
                    if boundary["emissivity_patch_count"] and not rad["has_qr_or_G_field"] and not rad["has_radiation_properties"]
                    else "radiation_field_or_model_present"
                    if rad["has_qr_or_G_field"] or rad["has_radiation_properties"]
                    else "no_radiation_indicators_found"
                ),
            }
        )
    return rows


def source_window_rows(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_source = {row["source_id"]: row for row in read_csv(SOURCE_CONTRACT)}
    out: list[dict[str, Any]] = []
    for case in cases:
        prior = by_source.get(case["source_id"], {})
        current_latest = case.get("latest_processor_time_s", "")
        prior_end = prior.get("requested_time_end_s", "")
        latest_status = "no_prior_contract"
        if prior_end and current_latest != "":
            try:
                latest_status = "prior_extraction_older_than_case_latest" if float(prior_end) < float(current_latest) else "prior_extraction_reaches_case_latest"
            except ValueError:
                latest_status = "prior_contract_non_numeric"
        out.append(
            {
                "case_key": case["case_key"],
                "source_id": case["source_id"],
                "run_class": case["run_class"],
                "case_latest_processor_time_s": current_latest,
                "prior_contract_requested_start_s": prior.get("requested_time_start_s", ""),
                "prior_contract_requested_end_s": prior_end,
                "prior_contract_latest_retained_time_s": prior.get("checkpoint_latest_retained_time_s", ""),
                "prior_contract_status": prior.get("retained_window_status", ""),
                "latest_window_status": latest_status,
                "prior_package_root": prior.get("package_root", ""),
                "case_root": case["case_root"],
            }
        )
    return out


def admitted(source_id: str) -> bool:
    return source_id in {
        "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "viscosity_screening_salt_test_3_jin_coarse_mesh",
        "viscosity_screening_salt_test_4_jin_coarse_mesh",
    }


def observation_rows(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    case_by_source = {row["source_id"]: row for row in cases}
    rows: list[dict[str, Any]] = []
    for row in read_csv(PRESSURE_LEDGER):
        source_id = row["source_id"]
        for qoi, units in [
            ("distributed_friction_pa", "Pa"),
            ("development_loss_pa", "Pa"),
            ("minor_loss_pa", "Pa"),
            ("f_debuoyed", "dimensionless"),
        ]:
            rows.append(
                {
                    "observation_id": f"{source_id}:{row['span']}:{qoi}",
                    "source_id": source_id,
                    "case_id": source_id.replace("viscosity_screening_salt_test_", "salt_").split("_jin")[0],
                    "run_class": "mainline_jin_continuation",
                    "observable_type": "pressure_span_term",
                    "span": row["span"],
                    "qoi_name": qoi,
                    "value": row.get(qoi, ""),
                    "units": units,
                    "time_window_start_s": "",
                    "time_window_end_s": "",
                    "source_path": rel(PRESSURE_LEDGER),
                    "fit_eligible": admitted(source_id) and qoi in {"distributed_friction_pa", "f_debuoyed"} and row.get("recirculation_flag") != "True",
                    "validation_eligible": admitted(source_id),
                    "quality_flags": "recirculation" if row.get("recirculation_flag") == "True" else "",
                    "gate_verdict": "admitted_mainline" if admitted(source_id) else "held",
                    "needs_special_gate_scrutiny": False,
                    "notes": "pressure ledger lacks explicit extraction window; join to source-window audit before final fitting",
                }
            )
    for row in read_csv(HEAT_LEDGER):
        source_id = row["source_id"]
        rows.append(
            {
                "observation_id": f"{source_id}:{row['span']}:{row['patch_group']}:wallHeatFlux_integral_W",
                "source_id": source_id,
                "case_id": source_id.replace("viscosity_screening_salt_test_", "salt_").split("_jin")[0],
                "run_class": "mainline_jin_continuation",
                "observable_type": "patch_heat_flux",
                "span": row["span"],
                "qoi_name": "wallHeatFlux_integral_W",
                "value": row.get("wallHeatFlux_integral_W", ""),
                "units": "W",
                "time_window_start_s": "",
                "time_window_end_s": "",
                "source_path": rel(HEAT_LEDGER),
                "fit_eligible": False,
                "validation_eligible": admitted(source_id),
                "quality_flags": "enthalpy_missing;radiation_label_needs_contract_join",
                "gate_verdict": "admitted_mainline" if admitted(source_id) else "held",
                "needs_special_gate_scrutiny": False,
                "notes": row.get("note", ""),
            }
        )
    for row in read_csv(TIME_WINDOW_OBS):
        source_id = row["source_id"]
        primary = row.get("is_primary_window") == "True"
        rows.append(
            {
                "observation_id": f"{source_id}:{row['qoi_name']}:{row['window_id']}",
                "source_id": source_id,
                "case_id": row.get("case_id", ""),
                "run_class": row.get("run_class", ""),
                "observable_type": "time_window_qoi",
                "span": "",
                "qoi_name": row["qoi_name"],
                "value": row.get("mean", ""),
                "units": row.get("qoi_units", ""),
                "time_window_start_s": row.get("window_start_s", ""),
                "time_window_end_s": row.get("window_end_s", ""),
                "source_path": row.get("source_path", rel(TIME_WINDOW_OBS)),
                "fit_eligible": primary and admitted(source_id) and row.get("window_state") in {"stationary", "quasi_stationary"},
                "validation_eligible": primary and (admitted(source_id) or source_id.endswith("_coarse_mesh")),
                "quality_flags": row.get("fit_use_status", ""),
                "gate_verdict": "admitted_mainline" if admitted(source_id) else "held_or_provisional",
                "needs_special_gate_scrutiny": row.get("needs_special_gate_scrutiny", ""),
                "notes": "time-window UQ row; Salt 1 fit eligibility overridden by scenario contract",
            }
        )
    return rows


def write_readme(cases: list[dict[str, Any]], windows: list[dict[str, Any]], observations: list[dict[str, Any]]) -> None:
    mainline_1p4 = [r for r in cases if r["run_class"].startswith("mainline") and r["has_1p4in_insulation_layer"]]
    stale = [r for r in windows if r["latest_window_status"] == "prior_extraction_older_than_case_latest"]
    text = f"""# CFD Scenario Contract And Observation Table Audit

Generated: `{datetime.now().isoformat(timespec='seconds')}`

## Scope

Read-only audit for the scientific redo requested on 2026-07-08. This package
separates case setup, available latest solver time, prior extracted windows, and
seed closure observations. It does not run OpenFOAM and does not mutate solver
case trees.

## Key Findings

- Mainline CFD Salt cases with readable `0/T` contain a `0.03556 m` layer, i.e.
  `1.4 in`, in their wall boundary-layer stack. The `0.25 in` / `0.30 in`
  values in the friction mdot comparison are 1D temperature-matching sweep
  settings, not the CFD case insulation label.
- `rcExternalTemperature` patches carry `emissivity 0.95`. No
  `constant/radiationProperties`, `qr`, or `G` field was found in the audited
  case roots, so the safest label is
  `surface_emissivity_bc_present_no_volume_radiation_field`, not simply
  `radiation absent`.
- Salt 1 nominal has a later June 25 base continuation candidate ending at about
  `4026.15625 s`, while several prior evidence products still use the June 18
  Salt 1 window ending at `3756.33125 s`.
- Salt 2/3/4 mainline case trees have later available retained times than the
  June 29 source-contract extraction rows. Any publication or fitting table must
  state whether it uses the current case latest or a frozen older package.
- Corrected Salt Q rows remain non-admitted until formal gate output lands.

## Outputs

- `scenario_contract.csv`: case setup, latest retained solver time, insulation
  label, and radiation label.
- `latest_window_audit.csv`: compares available latest solver time against the
  prior source-contract extraction window.
- `closure_observations_seed.csv`: canonical seed table. One row is one
  observable, with units, source path, eligibility flags, and quality flags.
- `summary.json`: machine-readable counts and recommendations.

## Counts

- Scenario rows: `{len(cases)}`
- Mainline rows with detected 1.4 in layer: `{len(mainline_1p4)}`
- Prior extraction rows older than available case latest: `{len(stale)}`
- Seed observation rows: `{len(observations)}`

## Immediate Recommendations

1. Treat the actual CFD scenario as `1.4 in wall/insulation layer present` with
   surface-emissivity boundary metadata, pending a deeper review of the custom
   `rcExternalTemperature` implementation.
2. Do not label the CFD as `0.25/0.30 in`; reserve those values for the 1D
   diagnostic matched-temperature scenario.
3. Refresh Salt 1 qualification from the June 25 base continuation before using
   Salt 1 as nominal evidence.
4. Before final closure fitting, rebuild pressure/thermal observations from a
   single declared latest-window contract rather than mixing older frozen
   extraction packages with newer retained solver output.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cases = case_rows()
    windows = source_window_rows(cases)
    observations = observation_rows(cases)
    case_fields = [
        "case_key",
        "case_id",
        "source_id",
        "run_class",
        "fit_use_status",
        "job_id",
        "job_state",
        "needs_special_gate_scrutiny",
        "recommendation",
        "case_root",
        "latest_processor_time_s",
        "retained_numeric_time_count",
        "t_boundary_exists",
        "bc_type_counts_json",
        "unique_thickness_m",
        "has_1p4in_insulation_layer",
        "insulation_label",
        "rc_external_patch_count",
        "emissivity_patch_count",
        "q_patch_count",
        "has_radiation_properties",
        "has_qr_or_G_field",
        "radiation_label",
    ]
    window_fields = [
        "case_key",
        "source_id",
        "run_class",
        "case_latest_processor_time_s",
        "prior_contract_requested_start_s",
        "prior_contract_requested_end_s",
        "prior_contract_latest_retained_time_s",
        "prior_contract_status",
        "latest_window_status",
        "prior_package_root",
        "case_root",
    ]
    obs_fields = [
        "observation_id",
        "source_id",
        "case_id",
        "run_class",
        "observable_type",
        "span",
        "qoi_name",
        "value",
        "units",
        "time_window_start_s",
        "time_window_end_s",
        "source_path",
        "fit_eligible",
        "validation_eligible",
        "quality_flags",
        "gate_verdict",
        "needs_special_gate_scrutiny",
        "notes",
    ]
    write_csv(OUT / "scenario_contract.csv", cases, case_fields)
    write_csv(OUT / "latest_window_audit.csv", windows, window_fields)
    write_csv(OUT / "closure_observations_seed.csv", observations, obs_fields)
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scenario_rows": len(cases),
        "observation_rows": len(observations),
        "mainline_1p4_detected": sum(1 for row in cases if row["run_class"].startswith("mainline") and row["has_1p4in_insulation_layer"]),
        "prior_extraction_older_than_case_latest": sum(1 for row in windows if row["latest_window_status"] == "prior_extraction_older_than_case_latest"),
        "recommendation": "freeze a single latest-window contract before final closure fitting",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_readme(cases, windows, observations)
    print(f"Wrote {rel(OUT)}")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
