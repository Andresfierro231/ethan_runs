#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design"

TASK = "AGENT-478"
DATE = "2026-07-16"
SALT3_NOMINAL_Q_W = 297.5
SALT3_PARENT = "viscosity_screening_salt_test_3_jin_coarse_mesh_continuation"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def case_key(q_w: float, ins: str) -> str:
    return f"salt3_jin_q{int(q_w):04d}w_{ins}_onset_anchor"


def run_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    def add(
        q_w: float,
        ins_mode: str,
        h_mult: float,
        group: str,
        target: str,
        priority: int,
        rationale: str,
    ) -> None:
        rows.append(
            {
                "case_key": case_key(q_w, ins_mode),
                "study_group": group,
                "salt_anchor": "salt3_jin",
                "parent_source_id": SALT3_PARENT,
                "target_heater_power_W": f"{q_w:.12g}",
                "target_heater_patch_Q_W": f"{q_w / 3.0:.12g}",
                "q_ratio_vs_salt3_nominal": f"{q_w / SALT3_NOMINAL_Q_W:.12g}",
                "insulation_mode": ins_mode,
                "passive_insulated_h_multiplier": f"{h_mult:.12g}",
                "active_patch_mutation_required": "0/T root and processors64 restart T",
                "cooler_policy": "scale fixed cooler/sink Q from parent heat ledger, then re-audit net heat after insulation mutation",
                "target_regime": target,
                "priority": priority,
                "run_after_gate": "after AGENT-471/475 high-heat Salt4 jobs reach restart preflight and at least early foamRun",
                "scientific_use": "onset anchor; not ordinary upcomer Nu/f_D/K fit unless reverse fractions pass",
                "rationale": rationale,
            }
        )

    add(
        1500.0,
        "hiins",
        0.5,
        "sentinel_cell_off",
        "high_Re_high_insulation_cell_off_target",
        1,
        "Push Re upward without forced flow while reducing passive wall cooling; intended to find a no/material-low-cell endpoint.",
    )
    add(
        150.0,
        "loins",
        2.0,
        "sentinel_cell_max",
        "low_Q_low_insulation_cell_max_target",
        1,
        "Lower throughflow and increase passive wall cooling to maximize wall-core drive and recirculation strength.",
    )

    for q_w in [250.0, 500.0, 1000.0]:
        for ins_mode, h_mult in [("hiins", 0.5), ("baseline", 1.0), ("loins", 2.0)]:
            target = "q_by_insulation_onset_matrix"
            priority = 2
            rationale = (
                "Small factorial matrix around the expected onset envelope; separates heater/Re effect "
                "from passive-wall insulation effect."
            )
            add(q_w, ins_mode, h_mult, "small_q_x_insulation_matrix", target, priority, rationale)

    return rows


def active_context_rows() -> list[dict[str, object]]:
    return [
        {
            "job_id": "3299610",
            "case_or_pack": "salt4_q3x_no_recirc_probe",
            "heater_inputs_W": "1012.8",
            "insulation_mode": "baseline",
            "current_use": "live high-Q nominal-insulation context; do not duplicate",
            "handoff_source": ".agent/status/2026-07-16_AGENT-471.md",
        },
        {
            "job_id": "3299620",
            "case_or_pack": "salt4_q0500w/salt4_q1000w/salt4_q1500w",
            "heater_inputs_W": "500;1000;1500",
            "insulation_mode": "baseline",
            "current_use": "live high-Q nominal-insulation bracket; use results before deciding whether Salt3 matrix levels need adjustment",
            "handoff_source": ".agent/status/2026-07-16_AGENT-475.md",
        },
    ]


def extraction_contract_rows() -> list[dict[str, object]]:
    rows = [
        ("U", "native field", "sample on upcomer inlet/mid/outlet planes and segment centerlines", "velocity vector, throughflow, reverse mask, secondary velocity"),
        ("T", "native field", "same planes plus core/wall-band samples", "bulk/core temperature and wall-core Delta T"),
        ("wallHeatFlux", "wall field/function object", "patch-integrated and local wall-band extraction", "source/sink ledger and wall heat-balance gate"),
        ("Re", "derived", "rho*U_bulk*D_h/mu(T_bulk)", "throughflow regime coordinate"),
        ("Pr", "derived", "mu(T_bulk)*Cp(T_bulk)/k(T_bulk)", "thermal property coordinate"),
        ("Ri", "derived", "Gr/Re^2 using documented characteristic length", "mixed-convection/onset coordinate"),
        ("Gr", "derived", "g*beta*DeltaT*L^3/nu^2", "buoyancy coordinate"),
        ("Ra", "derived", "Gr*Pr", "buoyancy-thermal coordinate"),
        ("Gz", "derived", "Re*Pr*D_h/x_from_reset", "thermal development coordinate"),
        ("wall_core_deltaT", "derived", "T_wall_band - T_core on each matched plane", "cell-driving thermal contrast"),
        ("reverse_area_fraction", "derived from U dot n", "area fraction with local reverse axial velocity", "cell/onset classifier"),
        ("reverse_mass_fraction", "derived from rho U dot n", "reverse mass flux / total absolute mass flux", "material backflow classifier"),
        ("secondary_velocity_fraction", "derived from U", "mean transverse speed / mean axial speed on plane", "recirculation-cell strength proxy"),
        ("steady_window_status", "time-window analysis", "last retained windows for mdot, heat residual, T probes, wall T", "admission gate for terminal or quasi-steady use"),
        ("mesh_time_uncertainty", "mesh/time plan", "coarse pilot; medium/fine endpoints; window uncertainty rows", "do not fit coefficients without uncertainty bounds"),
    ]
    return [
        {
            "required_output": name,
            "source_type": source,
            "extraction_location_or_method": method,
            "why_required": why,
            "required_for_acceptance": "yes",
        }
        for name, source, method, why in rows
    ]


def uncertainty_rows() -> list[dict[str, object]]:
    return [
        {
            "uncertainty_axis": "time_window",
            "applies_to": "all proposed rows",
            "minimum_action": "retain enough saved times for terminal-window mdot, heat residual, T, wall T, reverse fractions",
            "acceptance_rule": "classify steady/quasi-steady/drifting; no onset label promoted from a drifting-only window",
        },
        {
            "uncertainty_axis": "mesh",
            "applies_to": "sentinel cell-off and cell-max plus one transition matrix row",
            "minimum_action": "repeat selected endpoints on medium mesh after coarse pilot identifies useful regime",
            "acceptance_rule": "publish onset class with mesh caveat until same-QOI medium/fine or GCI exists",
        },
        {
            "uncertainty_axis": "insulation_mutation",
            "applies_to": "all hiins/loins rows",
            "minimum_action": "audit h/thickness/layer values in root 0/T and collated restart T before foamRun",
            "acceptance_rule": "reject as false-insulation if live restart field remains baseline",
        },
        {
            "uncertainty_axis": "heat_balance",
            "applies_to": "all rows",
            "minimum_action": "derive cooler fixed-Q from parent heat ledger and re-check net heat after passive insulation mutation",
            "acceptance_rule": "record signed source/sink residual; do not compare onset rows as balanced if residual is uncontrolled",
        },
    ]


def write_readme(rows: list[dict[str, object]]) -> None:
    readme = OUT / "README.md"
    readme.write_text(
        f"""---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/decision_note.md
  - work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/f6_onset_scorecard.csv
  - operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md
  - operational_notes/maps/cfd-runs-and-admission.md
  - .agent/status/2026-07-16_AGENT-471.md
  - .agent/status/2026-07-16_AGENT-475.md
tags: [recirculation, cfd-run-design, upcomer-onset, insulation, uncertainty]
related:
  - .agent/status/2026-07-16_AGENT-478.md
  - .agent/journal/2026-07-16/recirculation-cfd-anchor-study-design.md
task: {TASK}
date: {DATE}
role: CFD-study-design/Writer/Implementer/Tester
type: work_product
status: complete
---
# Recirculation CFD Anchor Study Design

This package proposes the next CFD run matrix for upcomer recirculation/onset
anchors. It does not stage or submit jobs.

## Study Decision

Run no new duplicate high-Q nominal-insulation Salt4 cases until jobs `3299610`
and `3299620` report enough status. The next independent knob should be real
insulation mutation on a Salt3 Jin anchor:

- high-Re / high-insulation cell-off sentinel: `salt3_jin_q1500w_hiins_onset_anchor`
- low-Q / low-insulation cell-max sentinel: `salt3_jin_q0150w_loins_onset_anchor`
- small `Q x insulation` matrix: `3 x 3` rows at `250`, `500`, and `1000 W`
  crossed with `hiins`, `baseline`, and `loins`.

`hiins` means more insulation / lower passive external `h` (`0.5x`); `loins`
means less insulation / higher passive external `h` (`2.0x`). This must be
verified in both root `0/T` and the collated restart field read by `foamRun`.

## Outputs

- `proposed_cfd_run_matrix.csv`
- `small_q_insulation_matrix.csv`
- `required_output_contract.csv`
- `mesh_time_uncertainty_plan.csv`
- `active_high_heat_context.csv`
- `tomorrow_start_here.md`
- `summary.json`

## Counts

- Proposed rows: `{len(rows)}`.
- Sentinel rows: `2`.
- Matrix rows: `9`.

## Scientific Guardrail

These runs can produce onset anchors and recirculation classifier evidence.
They should not be used as ordinary upcomer `Nu`, `f_D`, or component `K` fits
unless reverse-flow and uncertainty gates pass.
""",
        encoding="utf-8",
    )


def write_tomorrow() -> None:
    (OUT / "tomorrow_start_here.md").write_text(
        """# Tomorrow Start Here: Recirculation CFD Anchor Study

1. Open `.agent/BOARD.md` and check active rows before editing.
2. Check live jobs `3299610` and `3299620`; do not duplicate their Salt4
   high-Q nominal-insulation cases.
3. Open this package README and `proposed_cfd_run_matrix.csv`.
4. If staging is approved, start with the two Salt3 sentinel rows:
   `q1500w_hiins` and `q0150w_loins`.
5. Before launch, implement the insulation mutation as an actual OpenFOAM
   boundary/restart-field change, not only a case label:
   root `0/T`, copied `processors64/<restart>/T`, and case metadata must agree.
6. Run restart-level preflight before `foamRun`, following the AGENT-471/475
   Q-patching pattern.
7. Make every submitted case produce or retain enough data for U, T,
   wallHeatFlux, Re/Pr/Ri/Gr/Ra/Gz, wall-core Delta T, reverse area/mass
   fraction, secondary velocity, steady-window status, and mesh/time
   uncertainty.

Do not fit ordinary single-stream upcomer coefficients from material
recirculation rows.
""",
        encoding="utf-8",
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = run_rows()
    write_csv(OUT / "proposed_cfd_run_matrix.csv", rows)
    write_csv(
        OUT / "small_q_insulation_matrix.csv",
        [row for row in rows if row["study_group"] == "small_q_x_insulation_matrix"],
    )
    write_csv(OUT / "active_high_heat_context.csv", active_context_rows())
    write_csv(OUT / "required_output_contract.csv", extraction_contract_rows())
    write_csv(OUT / "mesh_time_uncertainty_plan.csv", uncertainty_rows())
    write_readme(rows)
    write_tomorrow()
    (OUT / "summary.json").write_text(
        json.dumps(
            {
                "task": TASK,
                "proposed_rows": len(rows),
                "sentinel_rows": 2,
                "matrix_rows": 9,
                "salt_anchor": "salt3_jin",
                "no_scheduler_action": True,
                "required_outputs": [row["required_output"] for row in extraction_contract_rows()],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
