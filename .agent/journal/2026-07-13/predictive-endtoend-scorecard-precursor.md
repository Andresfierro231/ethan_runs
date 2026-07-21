---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_endtoend_scorecard_precursor/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split/admission_split_table.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/hx_validation_guardrail_scorecard.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_gate/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_correction_candidates/decision_summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_forward_v0_solve_case_compute_run/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/summary.json
tags: [forward-model, predictive-1d, scorecard, journal]
related:
  - .agent/status/2026-07-13_AGENT-303.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_endtoend_scorecard_precursor/README.md
task: AGENT-303
date: 2026-07-13
role: Implementer/Writer
type: journal
status: complete
---
# Predictive End-to-End Scorecard Precursor

Date: 2026-07-13  
Task: AGENT-303  
Role: Implementer / Writer

## Startup

Read the required coordination files:

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `.agent/README.md`
- `.agent/status/README.md`
- `.agent/journal/README.md`
- `.agent/DOC_FRONTMATTER_SCHEMA.md`
- `operational_notes/maps/forward-predictive-model.md`
- `.agent/STATE.md`
- `.agent/BLOCKERS.md`

Confirmed the assigned write scope for AGENT-303 and did not edit
`.agent/BOARD.md`.

## Files Inspected

Core read-only packages:

- `work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split/`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_hx_fit/`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_gate/`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/`
- `work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/`

Also checked for AGENT-300/301/302 outputs twice because the shared worktree was
changing concurrently. At first AGENT-300 looked like an empty placeholder and
AGENT-302 was absent. Before finalizing, completed AGENT-300 and AGENT-302
artifacts appeared, and AGENT-301 recorded Slurm job `3293960` as submitted and
running. The precursor was updated to include those newer artifacts.

## Observations

The current forward-v1 state is a precursor, not a final scorecard:

- strict input contract passes with zero violations;
- split policy is locked and restrictive;
- fast-scan forward-v0 and HX1 split-aware rows can be tabulated;
- all Salt rows still fail the hydraulic mdot guardrail;
- full `solve_case` rows are submitted/running under Slurm job `3293960` but not
  harvested;
- sensor scoring is partially allowed after solve for 15 provisional diagnostic
  targets, with `TP2` and `TW10` blocked;
- hydraulic correction candidates are ranked, with `H1_localized_named_loss_and_reset_bundle`
  first and mean required resistance multiplier `2.115`, but no forward rerun;
- thermal mesh admission has zero fit-admissible rows.

## Files Changed

- `work_products/2026-07/2026-07-13/2026-07-13_predictive_endtoend_scorecard_precursor/README.md`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_endtoend_scorecard_precursor/readiness_lanes.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_endtoend_scorecard_precursor/split_scorecard_precursor.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_endtoend_scorecard_precursor/residual_attribution_precursor.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_endtoend_scorecard_precursor/blockers.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_endtoend_scorecard_precursor/source_manifest.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_endtoend_scorecard_precursor/summary.json`
- `.agent/status/2026-07-13_AGENT-303.md`
- `.agent/journal/2026-07-13/predictive-endtoend-scorecard-precursor.md`
- `imports/2026-07-13_predictive_endtoend_scorecard_precursor.json`

## Commands Run

- `pwd`
- `sed -n ...` on required coordination and package README files
- `find ...` and `rg -n ...` to locate read-only source artifacts and pending
  AGENT-300/301/302 evidence
- `python3.11 -c ...` to inspect source `summary.json` files
- `head -20 ...` on relevant CSVs
- `mkdir -p work_products/2026-07/2026-07-13/2026-07-13_predictive_endtoend_scorecard_precursor`
- `python3.11 -m json.tool ...` for summary and manifest validation
- CSV parse/count check over package outputs
- `python3 tools/docs/build_repo_index.py --check`

## Results

The package separates:

- what can be scored now: strict contract, split assignment, fast-scan proxy
  rows, HX1 guardrailed rows, hydraulic blocker metrics, external BC readiness,
  passive-wall diagnostic attribution, thermal mesh blocker state, ranked
  hydraulic correction candidates, and partial provisional sensor policy;
- what remains blocked or pending: full solve_case harvest, TP2/TW10 and exact
  sensor-coordinate claims, hydraulic correction forward rerun, thermal
  UA/HTC/Nu admission, and external Fluid API implementation.

## Incomplete Lines

Do not close AGENT-303 as final forward-v1 readiness. The next work should:

- use the AGENT-300 H1 candidate only after a bounded hydraulic forward rerun;
- harvest AGENT-301 Slurm job `3293960` before replacing proxy scores;
- apply AGENT-302 sensor policy by excluding `TP2` and `TW10` until their blockers
  clear;
- preserve Salt2/Salt3/Salt4 split boundaries before any new fitting;
- keep thermal mesh and passive-wall residuals out of fitted closure parameters
  until their gates admit them.
