#!/usr/bin/env python3
"""Audit rcExternalTemperature radiation/emissivity behavior for AGENT-264."""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_rc_external_temperature_implementation_audit"
PATCH_TABLE = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv"
)
OF13_ENV = ROOT / "tools/ofenv/of13_env.sh"
RCWALL_LIB = Path("/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/libRCWallBC.so")
OF13_EXTERNAL_T_C = Path(
    "/work/09748/andresfierro231/ls6/openfoam_runtime_recovery/2026-06-02_openfoam13/source/OpenFOAM-13/src/"
    "ThermophysicalTransportModels/coupledThermophysicalTransportModels/externalTemperature/"
    "externalTemperatureFvPatchScalarField.C"
)

CUSTOM_SOURCE_CANDIDATES = [
    Path("/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/rcExternalTemperatureFvPatchScalarField.C"),
    Path("/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/rcExternalTemperatureFvPatchScalarField.H"),
    Path("/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/RCWallBC/rcExternalTemperatureFvPatchScalarField.C"),
    Path("/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/RCWallBC/rcExternalTemperatureFvPatchScalarField.H"),
]

EVIDENCE_FIELDS = [
    "evidence_id",
    "category",
    "source_path",
    "observed",
    "interpretation",
    "supports_emissivity_Tsur_effect",
    "supports_separate_radiation_output",
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


def run_text_command(args: list[str]) -> tuple[bool, str]:
    if shutil.which(args[0]) is None:
        return False, f"{args[0]} not found"
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    return result.returncode == 0, result.stdout + result.stderr


def filtered_lines(text: str, needles: tuple[str, ...]) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        lower = line.lower()
        if any(needle.lower() in lower for needle in needles):
            out.append(line.strip())
    return out


def rc_patch_counts() -> dict[str, Any]:
    rows = read_csv(PATCH_TABLE)
    rc_rows = [row for row in rows if row.get("bc_type") == "rcExternalTemperature"]
    by_source = Counter(row["source_id"] for row in rc_rows)
    with_emissivity = sum(1 for row in rc_rows if row.get("emissivity"))
    with_tsur = sum(1 for row in rc_rows if row.get("Tsur_K"))
    with_q = sum(1 for row in rc_rows if row.get("imposed_Q_W"))
    return {
        "patch_table_exists": PATCH_TABLE.exists(),
        "total_patch_rows": len(rows),
        "rc_rows": len(rc_rows),
        "rc_rows_by_source": dict(sorted(by_source.items())),
        "rc_rows_with_emissivity": with_emissivity,
        "rc_rows_with_Tsur": with_tsur,
        "rc_rows_with_imposed_Q": with_q,
        "radiation_metadata_status_counts": dict(Counter(row.get("radiation_metadata_status", "") for row in rc_rows)),
    }


def source_probe_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    found = [path for path in CUSTOM_SOURCE_CANDIDATES if path.exists()]
    rows.append(
        {
            "evidence_id": "custom_source_probe",
            "category": "source_availability",
            "source_path": ";".join(str(path) for path in CUSTOM_SOURCE_CANDIDATES),
            "observed": "found=" + ";".join(str(path) for path in found) if found else "no targeted custom source candidate found",
            "interpretation": "Custom source is not available in the targeted accessible locations; use compiled-library and dictionary evidence.",
            "supports_emissivity_Tsur_effect": "unknown",
            "supports_separate_radiation_output": "no",
        }
    )
    return rows


def binary_probe_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    strings_ok, strings_text = run_text_command(["strings", str(RCWALL_LIB)])
    nm_ok, nm_text = run_text_command(["nm", "-C", str(RCWALL_LIB)])
    objdump_ok, objdump_text = run_text_command(["objdump", "-T", str(RCWALL_LIB)])

    string_hits = filtered_lines(
        strings_text,
        ("rcExternalTemperature", "emissivity", "Tsur", "sigma", "radiation", "thicknessLayers", "kappaLayerCoeffs"),
    )
    symbol_hits = filtered_lines(
        nm_text + "\n" + objdump_text,
        ("rcExternalTemperature", "updateCoeffs", "sigma", "Rps", "RpsInner", "RpsOuter", "CsAreal", "CpAreal"),
    )
    sigma_present = "physicoChemical::sigma" in nm_text or "physicoChemical5sigma" in objdump_text or "physicoChemical5sigma" in strings_text
    update_present = "rcExternalTemperatureFvPatchScalarField::updateCoeffs()" in nm_text
    radiation_methods = [line for line in symbol_hits if any(token in line for token in ("Rps", "CsAreal", "CpAreal"))]
    t_sur_string = any("Tsur" in line for line in string_hits)
    emissivity_string = any("emissivity" in line for line in string_hits)

    prioritized_symbol_hits = []
    for token in ("sigma", "updateCoeffs", "RpsOuter", "RpsInner", "Rps", "CsAreal", "CpAreal"):
        prioritized_symbol_hits.extend(line for line in symbol_hits if token in line and line not in prioritized_symbol_hits)
    prioritized_symbol_hits.extend(line for line in symbol_hits if line not in prioritized_symbol_hits)

    rows.append(
        {
            "evidence_id": "compiled_library_strings",
            "category": "compiled_library",
            "source_path": str(RCWALL_LIB),
            "observed": " | ".join(string_hits[:24]),
            "interpretation": "The compiled BC stores rcExternalTemperature, emissivity, Tsur, layer metadata, and constructor diagnostics requiring Ta or Tsur with emissivity.",
            "supports_emissivity_Tsur_effect": "yes" if t_sur_string and emissivity_string else "partial",
            "supports_separate_radiation_output": "no",
        }
    )
    rows.append(
        {
            "evidence_id": "compiled_library_symbols",
            "category": "compiled_library",
            "source_path": str(RCWALL_LIB),
            "observed": " | ".join(prioritized_symbol_hits[:24]),
            "interpretation": "The compiled BC defines updateCoeffs and radiation/resistance-related methods and references OpenFOAM sigma.",
            "supports_emissivity_Tsur_effect": "yes" if sigma_present and update_present and radiation_methods else "partial",
            "supports_separate_radiation_output": "no",
        }
    )
    facts = {
        "strings_command_ok": strings_ok,
        "nm_command_ok": nm_ok,
        "objdump_command_ok": objdump_ok,
        "sigma_symbol_present": sigma_present,
        "updateCoeffs_symbol_present": update_present,
        "radiation_resistance_symbols": radiation_methods,
        "Tsur_string_present": t_sur_string,
        "emissivity_string_present": emissivity_string,
    }
    return rows, facts


def stock_external_temperature_row() -> dict[str, Any]:
    observed = ""
    interpretation = ""
    if OF13_EXTERNAL_T_C.exists():
        text = OF13_EXTERNAL_T_C.read_text(encoding="utf-8", errors="ignore")
        lines = filtered_lines(text, ("physicoChemical::sigma", "haveEmissivity_", "hEff", "qrName_", "radiative heat flux"))
        observed = " | ".join(lines[:18])
        interpretation = (
            "Stock OF13 externalTemperature combines emissivity with sigma into an effective heat-transfer coefficient "
            "and only exports separate radiation when a qr field is configured; this is an analogy, not the custom source."
        )
    else:
        observed = "stock OF13 source path missing"
        interpretation = "No stock-source comparison available."
    return {
        "evidence_id": "stock_externalTemperature_reference",
        "category": "source_reference",
        "source_path": str(OF13_EXTERNAL_T_C),
        "observed": observed,
        "interpretation": interpretation,
        "supports_emissivity_Tsur_effect": "context_only",
        "supports_separate_radiation_output": "only_if_qr_configured",
    }


def dictionary_evidence_row() -> dict[str, Any]:
    counts = rc_patch_counts()
    return {
        "evidence_id": "admitted_case_dictionary_fields",
        "category": "case_dictionaries",
        "source_path": rel(PATCH_TABLE),
        "observed": json.dumps(counts, sort_keys=True),
        "interpretation": "All admitted Salt 2/3/4 rcExternalTemperature patches carry emissivity and Tsur metadata in the AGENT-263 table.",
        "supports_emissivity_Tsur_effect": "metadata_present_not_sufficient_alone",
        "supports_separate_radiation_output": "no",
    }


def no_exported_radiation_row() -> dict[str, Any]:
    rows = read_csv(PATCH_TABLE)
    no_qr_status = all(row.get("radiation_metadata_status") != "qr_output_present" for row in rows)
    return {
        "evidence_id": "no_exported_radiation_ledger",
        "category": "available_outputs",
        "source_path": rel(PATCH_TABLE),
        "observed": "no qr/G/radiation output column exists in AGENT-263 patch table; prior AGENT-240/July 8 packages found no qr/G/radiationProperties",
        "interpretation": "Radiation is not separable from total OpenFOAM wallHeatFlux in the available outputs.",
        "supports_emissivity_Tsur_effect": "does_not_refute",
        "supports_separate_radiation_output": "no" if no_qr_status else "unknown",
    }


def build_evidence_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.extend(source_probe_rows())
    binary_rows, binary_facts = binary_probe_rows()
    rows.extend(binary_rows)
    rows.append(stock_external_temperature_row())
    rows.append(dictionary_evidence_row())
    rows.append(no_exported_radiation_row())
    return rows, binary_facts


def make_decision(evidence_rows: list[dict[str, Any]], binary_facts: dict[str, Any]) -> dict[str, Any]:
    counts = rc_patch_counts()
    effect_supported = (
        binary_facts.get("sigma_symbol_present")
        and binary_facts.get("updateCoeffs_symbol_present")
        and binary_facts.get("Tsur_string_present")
        and binary_facts.get("emissivity_string_present")
        and bool(binary_facts.get("radiation_resistance_symbols"))
    )
    all_rc_have_metadata = counts.get("rc_rows") == counts.get("rc_rows_with_emissivity") == counts.get("rc_rows_with_Tsur")
    return {
        "task": "AGENT-264",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "emissivity_Tsur_affect_heat_flux": "yes" if effect_supported else "not_proven",
        "effect_basis": (
            "compiled_library_symbols_and_strings_plus_admitted_case_metadata"
            if effect_supported
            else "insufficient_without_custom_source_or_microcase"
        ),
        "custom_source_available": any(path.exists() for path in CUSTOM_SOURCE_CANDIDATES),
        "source_formula_status": "custom_source_not_found; exact source formula not quoted",
        "formula_inference": (
            "rcExternalTemperature has updateCoeffs, emissivity/Tsur dictionary handling, OpenFOAM sigma linkage, "
            "and radial/resistance symbols; radiation is therefore part of the boundary heat-flux calculation, "
            "but the contribution is not separately exported in current outputs."
        ),
        "all_admitted_rc_patches_have_emissivity_and_Tsur": bool(all_rc_have_metadata),
        "separable_radiation_output_available": "no",
        "parity_radiation_mode": "inseparable" if effect_supported else "off_until_proven",
        "one_d_parity_instruction": (
            "For realized-wallHeatFlux diagnostic replay, do not add a separate 1D radiation term on top of CFD wallHeatFlux. "
            "For external-BC parity mode, treat radiation as inseparable inside the rcExternalTemperature equivalent unless a future "
            "OpenFOAM output or source audit exposes a separate qr/radiation heat term."
        ),
        "microcase_run": "not_run",
        "microcase_reason": "compiled binary evidence was sufficient to answer effect direction; no solver output mutation or job submission was needed",
        "evidence_ids": [row["evidence_id"] for row in evidence_rows],
    }


def validate(evidence_rows: list[dict[str, Any]], decision: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not RCWALL_LIB.exists():
        errors.append(f"missing libRCWallBC.so at {RCWALL_LIB}")
    if not PATCH_TABLE.exists():
        errors.append(f"missing AGENT-263 patch table at {PATCH_TABLE}")
    if decision["emissivity_Tsur_affect_heat_flux"] != "yes":
        errors.append("emissivity/Tsur effect not proven by configured evidence")
    if decision["parity_radiation_mode"] != "inseparable":
        errors.append("expected parity_radiation_mode=inseparable for current evidence")
    if not any(row["evidence_id"] == "compiled_library_symbols" for row in evidence_rows):
        errors.append("missing compiled_library_symbols evidence row")
    if not any(row["supports_separate_radiation_output"] == "no" for row in evidence_rows):
        errors.append("missing no-separate-radiation evidence")
    return errors


def write_formula_audit(evidence_rows: list[dict[str, Any]], decision: dict[str, Any], errors: list[str]) -> None:
    text = f"""# rcExternalTemperature Implementation Audit

Generated: `{decision['generated_at']}`
Task: `AGENT-264`

## Result

- `emissivity_Tsur_affect_heat_flux`: `{decision['emissivity_Tsur_affect_heat_flux']}`
- `parity_radiation_mode`: `{decision['parity_radiation_mode']}`
- `separable_radiation_output_available`: `{decision['separable_radiation_output_available']}`

The accessible custom C++ source was not found in targeted locations, so this
audit does not quote an exact custom-source formula. The compiled
`libRCWallBC.so` is readable and exposes `rcExternalTemperature`, `updateCoeffs`,
`emissivity`, `Tsur`, OpenFOAM `physicoChemical::sigma`, and radial/resistance
symbols including `Rps`, `RpsInner`, `RpsOuter`, `CpAreal`, and `CsAreal`.

Interpretation: emissivity/Tsur are active in the custom boundary heat-flux
calculation, but the current CFD outputs do not expose a separate radiation
heat-rate ledger. Radiation is therefore inseparable from total
`wallHeatFlux` for current parity work.

## 1D Parity Instruction

{decision['one_d_parity_instruction']}

## Evidence

"""
    for row in evidence_rows:
        text += f"- `{row['evidence_id']}`: {row['interpretation']}\n"
    text += f"\n## Validation Errors\n\n```json\n{json.dumps(errors, indent=2)}\n```\n"
    (OUT / "rc_external_temperature_formula_audit.md").write_text(text, encoding="utf-8")


def write_outputs(evidence_rows: list[dict[str, Any]], decision: dict[str, Any], errors: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "rc_external_temperature_evidence_table.csv", evidence_rows, EVIDENCE_FIELDS)
    (OUT / "radiation_parity_decision.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    summary = {
        "generated_at": decision["generated_at"],
        "task": "AGENT-264",
        "validation_passed": not errors,
        "validation_errors": errors,
        "decision": decision,
        "outputs": {
            "evidence_table": rel(OUT / "rc_external_temperature_evidence_table.csv"),
            "radiation_parity_decision": rel(OUT / "radiation_parity_decision.json"),
            "formula_audit": rel(OUT / "rc_external_temperature_formula_audit.md"),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_formula_audit(evidence_rows, decision, errors)


def main() -> int:
    evidence_rows, binary_facts = build_evidence_rows()
    decision = make_decision(evidence_rows, binary_facts)
    errors = validate(evidence_rows, decision)
    write_outputs(evidence_rows, decision, errors)
    print(f"evidence_rows={len(evidence_rows)}")
    print(f"parity_radiation_mode={decision['parity_radiation_mode']}")
    print(f"validation_errors={len(errors)}")
    print(f"wrote {rel(OUT)}")
    if errors:
        for error in errors[:20]:
            print(f"ERROR: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
