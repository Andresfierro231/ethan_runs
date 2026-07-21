---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_heater_source_leave_salt3_out_score/summary.json
  - work_products/2026-07/2026-07-17/2026-07-17_heater_source_leave_salt3_out_score/candidate_admission_review.csv
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_blocker_audit/next_lane_decision.csv
  - work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate/candidate_admission_review.csv
  - work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate/coupled_delta_vs_m3.csv
tags: [forward-model, weekend-plan, upcomer-mixing, wall-fluid-coupling, handoff]
related:
  - operational_notes/maps/forward-predictive-model.md
  - .agent/status/2026-07-17_AGENT-529.md
  - .agent/status/2026-07-17_AGENT-531.md
  - work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate/README.md
task: AGENT-533
date: 2026-07-17
role: Coordinator/Writer
type: operational_note
status: complete
---
# Weekend Next-Model Handoff Plan

## Start Here

Open these files first, in order:

1. `work_products/2026-07/2026-07-17/2026-07-17_heater_source_leave_salt3_out_score/README.md`
2. `work_products/2026-07/2026-07-17/2026-07-17_heater_source_leave_salt3_out_score/candidate_admission_review.csv`
3. `work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_blocker_audit/next_lane_decision.csv`
4. `work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_blocker_audit/invariant_failure_modes.csv`
5. `work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate/README.md`
6. `work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate/coupled_delta_vs_m3.csv`
7. `work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/README.md`

Before editing, claim a new board row. If the board still lists AGENT-526 as
active, inspect its status/import/README first. Its work product exists and is
complete, but the board row may be stale; do not edit overlapping wall/fluid
candidate files until that is resolved.

## Current Evidence

The wall/test-section blocker remains open after three recent attempts:

- AGENT-529 corrected the heater-source split. It completed `67/67` Fluid rows,
  but strict Salt1/Salt2/Salt4 selection is blocked because every Salt4 train
  row has `root_status=rejected`. The diagnostic finite-row lambda `1.0` fails
  Salt3 vs M3 by mdot, TP, TW, and all-probe gates.
- AGENT-531 found no scoreable source-segment mismatch and no admitted wall or
  source candidate. The next useful physics lane is axial mixing/upcomer
  stratification after AGENT-526 resolves.
- AGENT-526's explicit test-section bulk-to-ambient series-resistance fallback
  completed `6` coupled rows but admitted `0`. It improves mdot vs M3 while TP,
  TW, and all-probe RMSE fail on Salt3/Salt4.

Key AGENT-526 deltas against M3:

- Lumped cooler Salt3: mdot delta `-15.8500613 pct`, TP `+11.5769804 K`,
  TW `+42.37730593 K`, all-probe `+35.38684985 K`.
- Lumped cooler Salt4: mdot delta `-13.09023967 pct`, TP `+26.19173439 K`,
  TW `+48.6052515 K`, all-probe `+42.93410155 K`.
- Segmented cooler gives the same conclusion.

The failure pattern is now stable: mdot can be improved, but the model places
the thermal field incorrectly. Do not admit any candidate from mdot improvement
alone.

## Remaining Blockers

1. **Salt4 root rejection in AGENT-529 baseline lane.** Strict Salt1/Salt2/Salt4
   training cannot select a lambda while Salt4 roots are rejected. This is a
   numerical/contract blocker, not a license to use finite rejected roots for
   admission.
2. **PB2 lacks Salt1 external-boundary role rows.** The PB2 lane cannot run under
   the corrected Salt1/Salt2/Salt4 split until Salt1 setup role rows exist.
3. **Blind-row adapters are missing.** Salt2 +/-5Q and `val_salt2` are
   score-only, never fit/model-selection rows. They need executable frozen
   prediction adapters before a final candidate can be admitted.
4. **Heated-incline/upcomer thermal-shape residuals persist.** AGENT-531 shows
   scoreable residuals such as TW5/TW6 persist across passive wall distribution,
   wall-temperature drive, wall-circuit, and heater-source families.
5. **Explicit test-section wall/fluid series resistance alone failed.** AGENT-526
   did not close TP/TW/all-probe gates; a richer wall/fluid candidate may still
   be useful, but do not duplicate AGENT-526's exact one-node series model.
6. **Updated Fluid upcomer-mixing API must be verified.** In the current checkout,
   `ScenarioConfig` exposes `external_boundary_role_rows` and
   `heater_source_mode`, but no obvious named upcomer-mixing hook. If the updated
   Fluid branch exists elsewhere, use it deliberately; otherwise do not fake
   mixing by posthoc sensor correction.

## Recommended Next Model

Prefer the upcomer mixing/stratification lane first. It is the best
non-overlapping next model after AGENT-526 because the explicit test-section
series-resistance fallback already failed and AGENT-531 points to axial mixing
or upcomer stratification as the next physics lane.

### Model UMX1: Energy-Conserving Upcomer Exchange

Goal: represent axial mixing/stratification in the upcomer without consuming CFD
temperatures, CFD mdot, realized wall heat flux, or holdout/blind targets at
runtime.

Model form:

- Split the upcomer/test-section parent path into a primary through-flow stream
  and a recirculation/near-wall exchange reservoir.
- Couple them with an energy-conserving exchange term:
  `Q_mix = C_mix * mdot * cp * (T_reservoir - T_main)`, or the equivalent
  updated Fluid API parameter if the new branch names it differently.
- The reservoir receives setup-only wall/ambient/test-section heat inputs
  already available to Fluid. It must not be calibrated from realized CFD
  wallHeatFlux.
- Fit at most one scalar first: `C_mix` or an equivalent exchange multiplier.
  If the updated Fluid implementation already has a physically dimensioned
  exchange time/length, fit that one scalar instead.

Split discipline:

- Fit/model-select on Salt1/Salt2/Salt4 nominal only.
- Salt3 is nominal holdout.
- Salt2 +/-5Q and `val_salt2` are blind score-only rows once adapters exist.
- Do not use Salt3, +/-5Q, or `val_salt2` to choose model form, lambda, exchange
  multiplier, bounds, root tolerances, sensor exclusions, or fallback policy.

Admission gates:

- Runtime audit passes: no forbidden inputs.
- All train rows used for selection have accepted roots, not only finite rejected
  rows.
- Salt3 mdot, TP RMSE, TW RMSE, and all-probe RMSE are all no worse than M3 and
  no worse than the best prior wall/source candidate.
- Blind rows are either completed and pass their declared score gates, or the
  candidate remains non-admitted with an explicit release gate.
- Probe-localization table shows that scoreable TW5/TW6 and TP/TW upcomer/test
  section residuals move in the right direction without creating a new
  unphysical cooler/test-section compensation.

Implementation plan:

1. Claim a new task row such as `AGENT-5xx_UPCOMER_MIXING_STRATIFICATION`.
2. Audit the updated Fluid version:
   `rg -n "upcomer|mixing|stratification|recirculation|exchange|ScenarioConfig" ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2`.
3. If an upcomer-mixing hook exists, build a repo-local scorer around it. If it
   does not exist, write a no-solver contract package that specifies the required
   Fluid API and stop before launching jobs.
4. Start with a narrow dry package:
   `tools/analyze/build_upcomer_mixing_stratification_candidate.py`
   and `tools/analyze/test_upcomer_mixing_stratification_candidate.py`.
5. Emit at least:
   `case_split_contract.csv`, `candidate_definitions.csv`,
   `scenario_contracts.csv`, `runtime_input_audit.csv`,
   `training_objective_by_parameter.csv`, `nominal_coupled_scorecard.csv`,
   `salt3_holdout_delta_vs_m3.csv`, `probe_error_localization.csv`,
   `blind_perturbation_external_scorecard.csv`, `candidate_admission_review.csv`,
   `blocker_decision.json`, `source_manifest.csv`, `summary.json`, and `README.md`.
6. Run dry tests first. Then submit the coupled run through Slurm or `srun`, not
   on a login node. Keep parallel workers bounded and write checkpoint/reuse
   support before a large grid.

## Secondary Model

Use explicit test-section wall/fluid coupling as the second lane, not the first,
unless AGENT-526 is found incomplete or invalid.

### Model TSWFC2: Distributed Test-Section Wall/Fluid Nodes

Do not duplicate AGENT-526's single bulk-to-ambient series resistance. The next
wall/fluid model should be distributed and energy-conserving:

- Divide the test section and adjacent upcomer parent into axial nodes.
- Solve fluid bulk, inner wall, and outer wall/surface states through declared
  material and setup hA/radiation paths.
- Fit only one global multiplier first, such as a wall-fluid UA multiplier or
  fouling/contact-resistance multiplier.
- Preserve energy balance and emit per-node heat ledgers so failures can be
  traced to wall/fluid exchange, ambient loss, or source placement.

Use the same split and admission gates as UMX1. If TSWFC2 cannot run Salt1 due
missing external-boundary rows, record that as a PB2/Salt1 contract blocker
instead of silently dropping Salt1.

## Weekend Sequence

Friday night / first session:

- Close stale coordination: verify AGENT-526 status/import exists or create a
  small cleanup row to close its board state without touching its outputs.
- Do not launch another full grid before the next model contract exists.
- Audit the updated Fluid branch for real upcomer-mixing/stratification hooks.

Saturday morning:

- Implement only the static UMX1 contract and tests.
- Dry-build the package and inspect `scenario_contracts.csv` and
  `runtime_input_audit.csv`.
- Confirm Salt3 and blind rows are absent from fit/model-selection rows.

Saturday afternoon:

- Run a small compute-node smoke: one or two parameter values over Salt1/Salt2/Salt4
  plus Salt3 if a selected diagnostic parameter is available.
- If any train root is rejected, stop and diagnose root/contract settings before
  expanding the grid.

Saturday evening:

- If smoke passes accepted roots, submit the bounded full grid through Slurm.
- Use checkpoint/reuse support. Do not leave the main agent blocked on a long
  foreground process.

Sunday:

- Harvest scorecards and probe localization.
- If Salt3 still fails TP/TW/all-probe, write a failure-localization package
  instead of retuning.
- If Salt3 passes but blind adapters are missing, mark the candidate
  non-admitted and create the next adapter task.
- If UMX1 is blocked by missing Fluid API, switch to TSWFC2 distributed wall
  nodes only after documenting the missing API contract.

## Do Not Do

- Do not use Salt3, Salt2 +/-5Q, `val_salt2`, or future CFD rows for fitting,
  model selection, root fallback decisions, or sensor-policy tuning.
- Do not consume realized CFD `wallHeatFlux`, CFD mdot, imposed CFD cooler duty,
  or validation temperatures at runtime.
- Do not rerun AGENT-511, AGENT-526, AGENT-529, or AGENT-531 unchanged.
- Do not admit finite rejected roots.
- Do not classify mdot improvement as success if TP/TW/all-probe errors worsen.
- Do not mutate native OpenFOAM/CFD outputs or the registry.
- Do not run long Fluid/OpenFOAM work on login nodes.

## Acceptance Signal For The Next Agent

A weekend implementation pass is successful if it produces one of these clear
outcomes:

- `UMX1` admits no candidate but identifies a precise Fluid API/root/blocker
  with completed evidence and no split leakage.
- `UMX1` completes Salt1/Salt2/Salt4 accepted-root training and Salt3 holdout,
  and remains honestly non-admitted because blind adapters are still missing.
- `UMX1` passes nominal and blind gates and can justifiably update the blocker
  register. This is unlikely; require strict provenance and all score tables
  before making that claim.
