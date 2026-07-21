#!/usr/bin/env python3
"""Build the hardened upcomer-onset CFD/postprocessing request package.

This is a design and postprocessing contract only. It must not launch CFD,
mutate native solver outputs, change registries, or promote scientific
admission state.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-17"
TASK = "TODO-UPCOMER-ONSET-ANCHOR-REQUEST-HARDENING"

OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_anchor_request_hardening"
STATUS = ROOT / f".agent/status/{DATE}_{TASK}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-17/upcomer-onset-anchor-request-hardening.md"
IMPORT = ROOT / "imports/2026-07-17_upcomer_onset_anchor_request_hardening.json"

PRIOR_ANCHOR_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_cfd_anchor_matrix"
DATA_GAP_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_data_sparsity_progress"
RECIRC_DESIGN_DIR = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design"

PRIOR_ANCHOR_MATRIX = PRIOR_ANCHOR_DIR / "upcomer_onset_anchor_matrix.csv"
PRIOR_REQUIRED_OUTPUTS = PRIOR_ANCHOR_DIR / "required_output_contract.csv"
EVIDENCE_GAP_QUEUE = DATA_GAP_DIR / "evidence_gap_queue.csv"
ANCHOR_INVENTORY = DATA_GAP_DIR / "anchor_inventory.csv"
SAME_WINDOW_GAPS = DATA_GAP_DIR / "same_window_field_gap_table.csv"
RECIRC_REQUIRED_OUTPUTS = RECIRC_DESIGN_DIR / "required_output_contract.csv"
RECIRC_PROPOSED_MATRIX = RECIRC_DESIGN_DIR / "proposed_cfd_run_matrix.csv"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def require_sources() -> None:
    required = [
        PRIOR_ANCHOR_MATRIX,
        PRIOR_REQUIRED_OUTPUTS,
        EVIDENCE_GAP_QUEUE,
        ANCHOR_INVENTORY,
        SAME_WINDOW_GAPS,
        RECIRC_REQUIRED_OUTPUTS,
        RECIRC_PROPOSED_MATRIX,
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing upcomer-onset request sources: " + "; ".join(missing))


def _thermal_drive_for(row: dict[str, str]) -> tuple[str, str]:
    q = row.get("target_heater_power_W", "")
    insulation = row.get("insulation_mode", "")
    if row["study_group"] == "sentinel_cell_off":
        return ("suppressed_passive_wall_drive", "wall_bulk_deltaT expected low-to-moderate; verify from same-window wall/bulk fields")
    if row["study_group"] == "sentinel_cell_max":
        return ("amplified_passive_wall_drive", "wall_bulk_deltaT expected high; verify that reverse metrics respond")
    if insulation == "loins":
        return ("high_passive_wall_drive", f"q={q} W with low insulation is the high thermal-drive side of this Re band")
    if insulation == "hiins":
        return ("low_passive_wall_drive", f"q={q} W with high insulation is the low thermal-drive side of this Re band")
    return ("baseline_passive_wall_drive", f"q={q} W with baseline insulation is the center thermal-drive request")


def _re_band_for(row: dict[str, str]) -> tuple[str, str, str, str]:
    case_key = row["case_key"]
    q = row.get("target_heater_power_W", "")
    insulation = row.get("insulation_mode", "")
    if row["study_group"] == "sentinel_cell_off":
        return ("high", "175", "250", "non_recirculating_anchor")
    if row["study_group"] == "sentinel_cell_max":
        return ("low", "50", "90", "recirculating_anchor")
    if "q0250" in case_key:
        return ("low_to_near_onset", "75", "115", "transition_or_recirculating_side")
    if "q0500" in case_key:
        return ("near_onset", "95", "150", "transition_anchor")
    if "q1000" in case_key and insulation == "hiins":
        return ("upper_near_onset", "150", "220", "non_recirculating_or_transition_anchor")
    if "q1000" in case_key:
        return ("upper_near_onset", "130", "200", "transition_anchor")
    return ("feasibility", "TBD", "TBD", "feasibility_not_admission")


def _acceptance_for(role: str) -> str:
    if role == "non_recirculating_anchor":
        return "same-window RAF<=0.02, RMF<=0.02, backflow_fraction<=0.02, and Ri_median<0.30 with uncertainty upper bound still below gate"
    if role == "recirculating_anchor":
        return "same-window backflow_fraction>=0.20 or RAF/RMF materially above 0.10; documents recirculating side only"
    if "transition" in role:
        return "same-window reverse metric in 0.02-0.10 band or paired rows bracketing <=0.02 and >=0.10 with overlapping Re/thermal-drive provenance"
    return "not an admission row unless a later task defines a solver-consistent forced-flow comparison"


def build_target_matrix() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for prior in read_csv(PRIOR_ANCHOR_MATRIX):
        if prior["case_key"] == "forced_flow_decoupled_re_feasibility":
            continue
        re_class, re_min, re_max, role = _re_band_for(prior)
        thermal_class, thermal_note = _thermal_drive_for(prior)
        rows.append(
            {
                "request_id": f"upcomer_onset:{prior['case_key']}",
                "case_key": prior["case_key"],
                "priority": prior["priority"],
                "study_group": prior["study_group"],
                "salt_anchor": prior["salt_anchor"],
                "target_heater_power_W": prior["target_heater_power_W"],
                "q_ratio_vs_salt3_nominal": prior["q_ratio_vs_salt3_nominal"],
                "insulation_mode": prior["insulation_mode"],
                "target_Re_upcomer_class": re_class,
                "target_Re_upcomer_design_min": re_min,
                "target_Re_upcomer_design_max": re_max,
                "target_thermal_drive_class": thermal_class,
                "thermal_drive_coordinate": "same-window wall_bulk_deltaT, Gr, Ra, Ri, and passive wall heat ledger",
                "target_regime": prior["target_regime"],
                "acceptance_role": role,
                "acceptance_gate": _acceptance_for(role),
                "one_d_model_mapping": "upcomer pipe element between PM5 and PM10 stations; keep junction/stub heat as separate loss branches until admitted",
                "actual_Re_requirement": "postprocess actual Re from same-window rho, mu(T_bulk), U_bulk, and hydraulic diameter; do not treat design band as evidence",
                "thermal_drive_note": thermal_note,
                "launch_allowed_in_this_row": "false",
                "source_paths": ";".join([rel(PRIOR_ANCHOR_MATRIX), rel(RECIRC_PROPOSED_MATRIX), rel(EVIDENCE_GAP_QUEUE)]),
            }
        )
    rows.append(
        {
            "request_id": "upcomer_onset:forced_flow_decoupled_re_feasibility",
            "case_key": "forced_flow_decoupled_re_feasibility",
            "priority": 3,
            "study_group": "optional_forced_flow_feasibility",
            "salt_anchor": "representative_salt_case",
            "target_heater_power_W": "TBD",
            "q_ratio_vs_salt3_nominal": "TBD",
            "insulation_mode": "TBD",
            "target_Re_upcomer_class": "controlled_Re_feasibility",
            "target_Re_upcomer_design_min": "150",
            "target_Re_upcomer_design_max": "250",
            "target_thermal_drive_class": "decoupled_if_boundary_conditions_are_valid",
            "thermal_drive_coordinate": "same-window wall_bulk_deltaT, Gr, Ra, Ri, and heat ledger",
            "target_regime": "decouple_Re_from_buoyancy_if_solver_supports",
            "acceptance_role": "feasibility_not_admission",
            "acceptance_gate": _acceptance_for("feasibility_not_admission"),
            "one_d_model_mapping": "diagnostic only unless natural-circulation boundary comparability is documented",
            "actual_Re_requirement": "postprocess actual Re from same-window fields; document why imposed flow is comparable before any use",
            "thermal_drive_note": "Use only if natural-circulation cases cannot bracket onset and solver setup can preserve the comparison question.",
            "launch_allowed_in_this_row": "false",
            "source_paths": ";".join([rel(PRIOR_ANCHOR_MATRIX), rel(EVIDENCE_GAP_QUEUE)]),
        }
    )
    return rows


def build_same_window_request() -> list[dict[str, object]]:
    common_window = "same retained terminal/quasi-steady time window used for RAF/RMF/SVF, Re/Ri, pressure, and heat ledger"
    rows = [
        ("bulk_temperature", "PM5 and PM10 upcomer planes plus inlet/mid/outlet support planes", "T_bulk_area_weighted", "K", "bulk state for Re/Pr/Ri and 1D node temperatures"),
        ("wall_temperature", "wall-band cells at the same axial stations as the bulk planes", "T_wall_band_area_weighted", "K", "wall/bulk thermal-drive coordinate"),
        ("wall_bulk_deltaT", "matched wall band minus matched bulk plane at PM5/PM10 and support stations", "T_wall_band - T_bulk", "K", "upcomer-onset thermal drive and junction/stub loss audit"),
        ("velocity_vector", "PM5 and PM10 planes", "U, U dot n, axial and transverse components", "m/s", "RAF/RMF/SVF, U_bulk, Re, and backflow classification"),
        ("mass_flux", "PM5 and PM10 planes", "rho U dot n signed and absolute integrals", "kg/s", "RMF and mass-conservation gate"),
        ("pressure_static", "PM5, PM10, and adjacent corner/junction taps", "p and p_rgh area-weighted means", "Pa", "pressure drop through upcomer and separation from corner losses"),
        ("pressure_total_proxy", "PM5 and PM10 planes", "p + 0.5 rho |U|^2 if density support exists", "Pa", "distinguish static drop from kinetic conversion"),
        ("wall_heat_flux", "upcomer wall, adjacent junction patches, and dead-leg/stub patches", "wallHeatFlux local and patch-integrated", "W/m2 and W", "heat audit; prevents hiding junction/stub losses inside one 1D upcomer coefficient"),
        ("fluid_properties", "same samples used for T_bulk", "rho, mu, k, cp, beta, nu, alpha", "SI", "Re/Pr/Gr/Ra/Ri/Gz reproducibility"),
        ("heat_balance", "heater, cooler/sink, upcomer wall, junctions, stubs, and remainder patches", "integrated heat flow by patch", "W", "thermal residual and section heat-loss audit"),
    ]
    output = []
    for field_id, location, field, units, needed in rows:
        output.append(
            {
                "field_id": field_id,
                "case_scope": "all requested upcomer-onset anchor cases",
                "location": location,
                "same_window_requirement": common_window,
                "field_or_metric": field,
                "units": units,
                "needed_for": needed,
                "one_d_model_mapping": "PM5/PM10 map to 1D upcomer pipe nodes; corner/junction/stub patch heat maps to explicit local loss terms, not bulk upcomer Nu",
                "minimum_acceptance": "field present, station definition recorded, window ID matches onset metrics, uncertainty row exists",
                "source_paths": ";".join([rel(PRIOR_REQUIRED_OUTPUTS), rel(SAME_WINDOW_GAPS), rel(RECIRC_REQUIRED_OUTPUTS)]),
            }
        )
    return output


def build_pm_request() -> list[dict[str, object]]:
    metrics = [
        ("reverse_area_fraction", "RAF", "area fraction with U dot n < 0", "onset classifier"),
        ("reverse_mass_fraction", "RMF", "reverse signed mass flux divided by total absolute mass flux", "material backflow classifier"),
        ("secondary_velocity_fraction", "SVF", "mean transverse speed divided by mean axial speed", "cell strength proxy"),
        ("backflow_fraction", "backflow_fraction", "legacy cell-count/area fraction when available", "bridge to existing upcomer-onset evidence"),
        ("Re", "Re_upcomer", "rho*U_bulk*D_h/mu(T_bulk)", "streamwise coordinate for 1D model"),
        ("Pr", "Pr", "mu*cp/k", "property coordinate"),
        ("Ri", "Ri", "Gr/Re^2 using documented L", "onset coordinate"),
        ("Gr", "Gr", "g*beta*wall_bulk_deltaT*L^3/nu^2", "thermal-drive coordinate"),
        ("Ra", "Ra", "Gr*Pr", "thermal-drive coordinate"),
        ("Gz", "Gz", "Re*Pr*D_h/x_from_reset", "development coordinate"),
        ("pressure", "delta_p_PM5_PM10", "same-window p and p_rgh difference plus uncertainty", "pressure map and corner-drop separation"),
        ("wall_bulk_deltaT", "wall_bulk_deltaT_PM5_PM10", "matched wall-band minus bulk T at PM5 and PM10", "junction/upcomer heat-loss audit"),
        ("heat_flux", "wallHeatFlux_PM5_PM10_section", "patch-integrated wall heat in the PM5-PM10 section", "same-window heat audit"),
    ]
    rows = []
    for plane_set in ("PM5", "PM10", "PM5_to_PM10_pair"):
        for metric_id, metric, definition, required_for in metrics:
            if plane_set != "PM5_to_PM10_pair" and metric_id in {"pressure", "heat_flux"}:
                continue
            rows.append(
                {
                    "request_id": f"{plane_set}:{metric}",
                    "plane_set": plane_set,
                    "case_scope": "all requested upcomer-onset anchor cases",
                    "quantity": metric_id,
                    "metric": metric,
                    "definition": definition,
                    "required_for": required_for,
                    "admission_gate": "same retained time window, same plane geometry, same wall-band definition, uncertainty reported",
                    "minimum_acceptance": "required for main evidence; missing value keeps row diagnostic only",
                    "postprocessor_hint": "emit both per-plane samples and paired PM5-PM10 ledger rows keyed by case_key/window_id/mesh_id",
                    "source_paths": ";".join([rel(PRIOR_REQUIRED_OUTPUTS), rel(ANCHOR_INVENTORY), rel(SAME_WINDOW_GAPS)]),
                }
            )
    return rows


def build_uncertainty_requirements() -> list[dict[str, object]]:
    return [
        {
            "requirement_id": "mesh_family_for_anchor_admission",
            "scope": "non-recirculating sentinel and at least one transition bracket pair",
            "metric": "RAF, RMF, backflow_fraction, Re, Ri, wall_bulk_deltaT, delta_p_PM5_PM10, section heat loss",
            "minimum_design": "baseline plus one refined mesh for candidate screening; three-level coarse/medium/fine or documented GCI-equivalent for admission",
            "admission_threshold": "classification must not flip across admitted meshes; GCI or refinement uncertainty reported beside every onset metric",
            "why": "upcomer-onset-data-sparsity cannot be closed by a single mesh row near a classification boundary",
            "blocks_if_missing": "main evidence/training admission; row remains diagnostic",
        },
        {
            "requirement_id": "time_window_stability",
            "scope": "every requested anchor case",
            "metric": "window means and slopes for mdot, RAF/RMF/SVF, Re/Ri, heat residual, T_wall, T_bulk, pressure",
            "minimum_design": "at least three retained terminal time-window samples or a documented quasi-steady time-window with bootstrap/block uncertainty",
            "admission_threshold": "Re and heat residual variation <=5%; RAF/RMF/backflow/Ri/wall_bulk_deltaT variation <=10% or uncertainty explicitly crosses transition band",
            "why": "near-onset labels are sensitive to slow drift and thermal storage",
            "blocks_if_missing": "main evidence/training admission; no coefficient fitting",
        },
        {
            "requirement_id": "nonrecirculating_anchor_gate",
            "scope": "candidate non-recirculating anchor",
            "metric": "RAF, RMF, backflow_fraction, Ri_median",
            "minimum_design": "target Re_upcomer 175-250 with suppressed passive wall drive",
            "admission_threshold": "upper uncertainty bound RAF<=0.02, RMF<=0.02, backflow_fraction<=0.02, and Ri_median<0.30",
            "why": "we currently have zero non-recirculating upcomer-onset anchors",
            "blocks_if_missing": "upcomer-onset-data-sparsity remains open",
        },
        {
            "requirement_id": "transition_bracket_gate",
            "scope": "near-onset matrix rows",
            "metric": "RAF, RMF, backflow_fraction at matched Re/thermal-drive coordinates",
            "minimum_design": "paired rows spanning 0.02-0.10 reverse metric band or one row inside the band",
            "admission_threshold": "bracket must preserve same PM5/PM10 definitions, property model, window policy, and uncertainty accounting",
            "why": "needed to locate onset rather than only diagnose strong recirculation",
            "blocks_if_missing": "cannot train or validate onset threshold",
        },
        {
            "requirement_id": "pressure_and_heat_uncertainty",
            "scope": "PM5-PM10 and adjacent junction/stub patches",
            "metric": "delta_p, p_rgh, wallHeatFlux, patch heat totals, thermal residual",
            "minimum_design": "same-window uncertainty rows and conservation residual for each mesh/window",
            "admission_threshold": "pressure and section heat-loss uncertainty <=10% for admitted rows; heat residual <=5% of imposed heater/sink magnitude",
            "why": "corner pressure drop and junction heat loss are separate mechanisms and must not be buried inside upcomer friction/Nu",
            "blocks_if_missing": "pressure map and heat-loss audit remain diagnostic",
        },
    ]


def build_launch_gates() -> list[dict[str, object]]:
    return [
        {
            "gate_id": "no_duplicate_jobs",
            "required_action_before_launch": "query live and recent scheduler state for equivalent case_key, parent, Q, insulation, mesh, and restart time",
            "pass_condition": "no active duplicate and no completed equivalent artifact already postprocessed",
            "this_package_status": "request_only_no_scheduler_action",
        },
        {
            "gate_id": "separate_execution_board_row",
            "required_action_before_launch": "claim a new board row with allowed staging/scheduler paths and exact case list",
            "pass_condition": "board row permits staging and scheduler mutation",
            "this_package_status": "launch_forbidden",
        },
        {
            "gate_id": "source_case_readiness",
            "required_action_before_launch": "verify parent continuation fields, heat ledger, property model, boundary mutations, and restart provenance",
            "pass_condition": "source manifest names exact native case path and copied staging path",
            "this_package_status": "not_checked_here",
        },
        {
            "gate_id": "postprocessing_contract_first",
            "required_action_before_launch": "install or stage PM5/PM10, wall-band, pressure, heat, and uncertainty extractors before expensive runtime",
            "pass_condition": "dry-run extractor schema matches this package's CSV contracts",
            "this_package_status": "contract_defined_here",
        },
        {
            "gate_id": "cost_and_mesh_plan",
            "required_action_before_launch": "separate pilot/discovery runs from admission mesh/time rows",
            "pass_condition": "candidate discovery may be coarse; admitted anchors must carry mesh/time uncertainty",
            "this_package_status": "requirements_defined_here",
        },
    ]


def build_guardrails() -> list[dict[str, object]]:
    return [
        {
            "guardrail_id": "no_recirc_nu_fd_k_fit",
            "forbidden_use": "ordinary upcomer Nu, f_D, or corner K fitting from rows with RAF/RMF/backflow above non-recirculating gates",
            "required_alternative": "use diagnostic recirculation-modeled closure or wait for admitted non-recirculating/transition anchors",
        },
        {
            "guardrail_id": "no_window_mixing",
            "forbidden_use": "combine wall temperature, bulk temperature, pressure, and reverse metrics from different time windows",
            "required_alternative": "key every extracted value by case_key, mesh_id, window_id, plane_set, and station definition",
        },
        {
            "guardrail_id": "no_hidden_junction_loss",
            "forbidden_use": "hide junction/stub heat loss in a single upcomer heat-transfer multiplier",
            "required_alternative": "report upcomer wall, junction, corner, and stub heat branches separately for 1D mapping",
        },
        {
            "guardrail_id": "no_design_target_as_evidence",
            "forbidden_use": "treat design target Re or thermal-drive bands as measured CFD evidence",
            "required_alternative": "compute actual same-window Re/Pr/Ri/Gr/Ra/Gz from extracted fields",
        },
        {
            "guardrail_id": "no_scientific_admission_change",
            "forbidden_use": "promote rows to training/main evidence from this request package alone",
            "required_alternative": "run a future admission package after postprocessed outputs and uncertainty rows exist",
        },
    ]


def build_blocker_attack_map() -> list[dict[str, object]]:
    return [
        {
            "blocker_id": "upcomer-onset-data-sparsity",
            "missing_evidence": "non-recirculating upcomer anchor",
            "request_output": "target_re_thermal_drive_matrix.csv",
            "minimum_acceptance": "candidate with RAF/RMF/backflow <=0.02 and Ri_median<0.30 after uncertainty",
            "status_after_this_package": "request_defined_not_unblocked",
        },
        {
            "blocker_id": "upcomer-onset-data-sparsity",
            "missing_evidence": "near-onset transition bracket",
            "request_output": "target_re_thermal_drive_matrix.csv;pm5_pm10_extraction_request.csv",
            "minimum_acceptance": "rows inside or bracketing 0.02-0.10 reverse metric band",
            "status_after_this_package": "request_defined_not_unblocked",
        },
        {
            "blocker_id": "upcomer-onset-data-sparsity",
            "missing_evidence": "same-window wall/bulk and heat fields",
            "request_output": "same_window_field_request.csv",
            "minimum_acceptance": "T_wall/T_bulk/wallHeatFlux/patch heat totals share the same retained window as RAF/RMF/Re/Ri",
            "status_after_this_package": "request_defined_not_unblocked",
        },
        {
            "blocker_id": "upcomer-onset-data-sparsity",
            "missing_evidence": "mesh/time uncertainty for onset metrics",
            "request_output": "mesh_time_uncertainty_requirements.csv",
            "minimum_acceptance": "classification-stable mesh family and time-window uncertainty beside every onset metric",
            "status_after_this_package": "request_defined_not_unblocked",
        },
        {
            "blocker_id": "corner-pressure-and-junction-heat-diagnostic",
            "missing_evidence": "separate pressure drop and heat-loss ledgers for upcomer, corners, junctions, and stubs",
            "request_output": "same_window_field_request.csv;pm5_pm10_extraction_request.csv",
            "minimum_acceptance": "PM5-PM10 pressure map plus patch heat ledgers with conservation residual",
            "status_after_this_package": "request_defined_not_unblocked",
        },
    ]


def source_manifest_rows() -> list[dict[str, object]]:
    sources = [
        ("prior_anchor_matrix", PRIOR_ANCHOR_MATRIX, "completed design-only upcomer onset anchor matrix"),
        ("prior_required_outputs", PRIOR_REQUIRED_OUTPUTS, "prior required-output contract and admission roles"),
        ("evidence_gap_queue", EVIDENCE_GAP_QUEUE, "open blocker requirements for upcomer-onset-data-sparsity"),
        ("anchor_inventory", ANCHOR_INVENTORY, "observed recirculating rows and current Re/Ri/reverse metrics"),
        ("same_window_gaps", SAME_WINDOW_GAPS, "missing same-window field audit"),
        ("recirc_required_outputs", RECIRC_REQUIRED_OUTPUTS, "recirculation anchor field contract"),
        ("recirc_proposed_matrix", RECIRC_PROPOSED_MATRIX, "original anchor case design provenance"),
    ]
    return [{"source_id": key, "path": rel(path), "exists": str(path.exists()).lower(), "use": use} for key, path, use in sources]


def write_docs(summary: dict[str, object]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    readme = OUT / "README.md"
    readme.write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(PRIOR_ANCHOR_MATRIX)}",
                f"  - {rel(EVIDENCE_GAP_QUEUE)}",
                f"  - {rel(ANCHOR_INVENTORY)}",
                f"  - {rel(SAME_WINDOW_GAPS)}",
                "tags: [upcomer, onset, cfd-anchor, postprocessing-request, provenance]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(JOURNAL)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Coordinator/Implementer/Tester/Writer",
                "type: work_product",
                "status: complete",
                "---",
                "# Upcomer Onset CFD Anchor Request Hardening",
                "",
                "## Decision",
                "",
                "This package converts the completed upcomer-onset design into an exact CFD/postprocessing request. It does not launch CFD, mutate native solver outputs, or change admission state.",
                "",
                "## Required Outputs",
                "",
                "- `target_re_thermal_drive_matrix.csv`: target Re and thermal-drive matrix for near-onset, non-recirculating, transition, and recirculating-side anchors.",
                "- `same_window_field_request.csv`: wall/bulk, pressure, heat, and property fields that must be extracted from the same retained window.",
                "- `pm5_pm10_extraction_request.csv`: PM5/PM10 reverse-flow, pressure, heat, and nondimensional extraction contract.",
                "- `mesh_time_uncertainty_requirements.csv`: mesh/time gates required before rows can become main evidence or training data.",
                "- `launch_gate_checklist.csv`: pre-launch gates for a future scheduler/staging task; this package itself is non-launching.",
                "- `misuse_guardrails.csv`: forbidden interpretations that would contaminate upcomer-onset or 1D closure work.",
                "- `blocker_attack_map.csv`: how the request attacks `upcomer-onset-data-sparsity` without claiming it is resolved.",
                "",
                "## Counts",
                "",
                f"- Target matrix rows: `{summary['target_matrix_rows']}`.",
                f"- Same-window field rows: `{summary['same_window_field_rows']}`.",
                f"- PM5/PM10 request rows: `{summary['pm5_pm10_request_rows']}`.",
                f"- Mesh/time uncertainty rows: `{summary['mesh_time_requirement_rows']}`.",
                f"- Scheduler action: `{summary['scheduler_action']}`.",
                "",
                "## 1D Mapping",
                "",
                "PM5 and PM10 define the upcomer pipe-element endpoints for the 1D model. Junction, corner, and stub heat/pressure terms must remain separate local branches until admitted evidence proves they can be collapsed without biasing onset.",
            ]
        )
        + "\n"
    )

    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(OUT / 'summary.json')}",
                f"  - {rel(OUT / 'target_re_thermal_drive_matrix.csv')}",
                f"  - {rel(OUT / 'same_window_field_request.csv')}",
                f"  - {rel(OUT / 'mesh_time_uncertainty_requirements.csv')}",
                "tags: [status, upcomer, onset, cfd-anchor]",
                "related:",
                f"  - {rel(JOURNAL)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Coordinator/Implementer/Tester/Writer",
                "type: status",
                "status: complete",
                "---",
                f"# {TASK} Status",
                "",
                "## Changes Made",
                "",
                "- Built a reusable non-launching request builder for the upcomer-onset CFD anchor design.",
                "- Published exact target Re/thermal-drive, same-window wall/bulk, PM5/PM10 extraction, and mesh/time uncertainty contracts.",
                "- Added blocker and misuse guardrail tables so future work can distinguish request definition from admitted evidence.",
                "",
                "## Validation",
                "",
                "- `python3.11 -m unittest tools.analyze.test_upcomer_onset_anchor_request_hardening`",
                "- `python3.11 tools/analyze/build_upcomer_onset_anchor_request_hardening.py`",
                "- `python3.11 -m json.tool work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_anchor_request_hardening/summary.json`",
                "",
                "## Guardrails",
                "",
                "- No CFD was launched and no scheduler state was modified.",
                "- No native solver output, registry state, or scientific admission state was changed.",
                "- Target Re/thermal-drive bands are design requests only; actual values must come from same-window postprocessing.",
            ]
        )
        + "\n"
    )

    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(OUT / 'README.md')}",
                f"  - {rel(PRIOR_ANCHOR_MATRIX)}",
                f"  - {rel(EVIDENCE_GAP_QUEUE)}",
                f"  - {rel(ANCHOR_INVENTORY)}",
                "tags: [journal, upcomer, onset, cfd-anchor, postprocessing-request]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Coordinator/Implementer/Tester/Writer",
                "type: journal",
                "status: complete",
                "---",
                "# Upcomer Onset Anchor Request Hardening Journal",
                "",
                f"Task: `{TASK}`",
                "",
                "The request hardening pass keeps the existing CFD anchor design non-launching while making the downstream postprocessing requirements explicit. The key blocker is unchanged: current upcomer evidence is diagnostic because it lacks a non-recirculating/transition anchor, same-window wall/bulk heat fields, and mesh/time uncertainty.",
                "",
                "The package therefore asks for a target Re/thermal-drive matrix rather than a fitted model. PM5 and PM10 are treated as 1D upcomer endpoints. Junction, corner, and stub heat/pressure entries are requested separately so future 1D work can decide whether they are explicit local losses or admissible collapsed terms.",
                "",
                "No jobs were submitted. Future execution needs a separate board row with scheduler/staging authority, duplicate-job checks, source-case manifests, and extractor dry runs before compute spend.",
            ]
        )
        + "\n"
    )


def changed_files() -> list[str]:
    files = [
        "tools/analyze/build_upcomer_onset_anchor_request_hardening.py",
        "tools/analyze/test_upcomer_onset_anchor_request_hardening.py",
        rel(OUT / "target_re_thermal_drive_matrix.csv"),
        rel(OUT / "same_window_field_request.csv"),
        rel(OUT / "pm5_pm10_extraction_request.csv"),
        rel(OUT / "mesh_time_uncertainty_requirements.csv"),
        rel(OUT / "launch_gate_checklist.csv"),
        rel(OUT / "misuse_guardrails.csv"),
        rel(OUT / "blocker_attack_map.csv"),
        rel(OUT / "source_manifest.csv"),
        rel(OUT / "cfd_postprocessing_request.json"),
        rel(OUT / "summary.json"),
        rel(OUT / "README.md"),
        rel(STATUS),
        rel(JOURNAL),
        rel(IMPORT),
        ".agent/BOARD.md",
    ]
    return files


def write_import_manifest(summary: dict[str, object]) -> None:
    IMPORT.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "task": TASK,
        "date": DATE,
        "summary": "Hardened exact upcomer-onset CFD/postprocessing request for near-onset and non-recirculating anchors.",
        "changed_files": changed_files(),
        "read_only_context": [
            rel(PRIOR_ANCHOR_MATRIX),
            rel(PRIOR_REQUIRED_OUTPUTS),
            rel(EVIDENCE_GAP_QUEUE),
            rel(ANCHOR_INVENTORY),
            rel(SAME_WINDOW_GAPS),
            rel(RECIRC_REQUIRED_OUTPUTS),
            rel(RECIRC_PROPOSED_MATRIX),
        ],
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "scientific_admission_change": "none",
        "output_dir": rel(OUT),
        "summary_json": summary,
    }
    write_json(IMPORT, manifest)


def main() -> dict[str, object]:
    require_sources()
    target_matrix = build_target_matrix()
    same_window = build_same_window_request()
    pm_request = build_pm_request()
    uncertainty = build_uncertainty_requirements()
    launch_gates = build_launch_gates()
    guardrails = build_guardrails()
    blocker_map = build_blocker_attack_map()
    source_manifest = source_manifest_rows()

    write_csv(
        OUT / "target_re_thermal_drive_matrix.csv",
        target_matrix,
        [
            "request_id",
            "case_key",
            "priority",
            "study_group",
            "salt_anchor",
            "target_heater_power_W",
            "q_ratio_vs_salt3_nominal",
            "insulation_mode",
            "target_Re_upcomer_class",
            "target_Re_upcomer_design_min",
            "target_Re_upcomer_design_max",
            "target_thermal_drive_class",
            "thermal_drive_coordinate",
            "target_regime",
            "acceptance_role",
            "acceptance_gate",
            "one_d_model_mapping",
            "actual_Re_requirement",
            "thermal_drive_note",
            "launch_allowed_in_this_row",
            "source_paths",
        ],
    )
    write_csv(
        OUT / "same_window_field_request.csv",
        same_window,
        [
            "field_id",
            "case_scope",
            "location",
            "same_window_requirement",
            "field_or_metric",
            "units",
            "needed_for",
            "one_d_model_mapping",
            "minimum_acceptance",
            "source_paths",
        ],
    )
    write_csv(
        OUT / "pm5_pm10_extraction_request.csv",
        pm_request,
        [
            "request_id",
            "plane_set",
            "case_scope",
            "quantity",
            "metric",
            "definition",
            "required_for",
            "admission_gate",
            "minimum_acceptance",
            "postprocessor_hint",
            "source_paths",
        ],
    )
    write_csv(
        OUT / "mesh_time_uncertainty_requirements.csv",
        uncertainty,
        ["requirement_id", "scope", "metric", "minimum_design", "admission_threshold", "why", "blocks_if_missing"],
    )
    write_csv(
        OUT / "launch_gate_checklist.csv",
        launch_gates,
        ["gate_id", "required_action_before_launch", "pass_condition", "this_package_status"],
    )
    write_csv(
        OUT / "misuse_guardrails.csv",
        guardrails,
        ["guardrail_id", "forbidden_use", "required_alternative"],
    )
    write_csv(
        OUT / "blocker_attack_map.csv",
        blocker_map,
        ["blocker_id", "missing_evidence", "request_output", "minimum_acceptance", "status_after_this_package"],
    )
    write_csv(OUT / "source_manifest.csv", source_manifest, ["source_id", "path", "exists", "use"])

    postprocessing_request = {
        "task": TASK,
        "date": DATE,
        "request_type": "non_launching_cfd_postprocessing_contract",
        "case_matrix_csv": "target_re_thermal_drive_matrix.csv",
        "same_window_fields_csv": "same_window_field_request.csv",
        "pm5_pm10_extraction_csv": "pm5_pm10_extraction_request.csv",
        "mesh_time_uncertainty_csv": "mesh_time_uncertainty_requirements.csv",
        "global_window_rule": "all thermal, pressure, velocity, reverse-flow, and heat-ledger quantities must share case_key/mesh_id/window_id/station definitions",
        "admission_status": "request_only_not_evidence",
        "scheduler_action": False,
    }
    write_json(OUT / "cfd_postprocessing_request.json", postprocessing_request)

    summary = {
        "task": TASK,
        "output_dir": rel(OUT),
        "target_matrix_rows": len(target_matrix),
        "same_window_field_rows": len(same_window),
        "pm5_pm10_request_rows": len(pm_request),
        "mesh_time_requirement_rows": len(uncertainty),
        "launch_gate_rows": len(launch_gates),
        "guardrail_rows": len(guardrails),
        "blocker_attack_rows": len(blocker_map),
        "scheduler_action": False,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scientific_admission_change": "none",
        "unblocks_upcomer_onset_data_sparsity": False,
        "reason_not_unblocked": "request contract only; CFD execution, postprocessing, and admission remain future work",
    }
    write_json(OUT / "summary.json", summary)
    write_docs(summary)
    write_import_manifest(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
