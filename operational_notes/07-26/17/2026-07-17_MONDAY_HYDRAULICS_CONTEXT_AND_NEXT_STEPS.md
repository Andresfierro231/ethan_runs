---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_named_pressure_extraction_readiness/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_contract/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_extractor/README.md
  - operational_notes/maps/pressure-and-momentum-budget.md
tags: [handoff, monday-start, hydraulics, pressure-ledger, f6, two-tap]
related:
  - .agent/status/2026-07-17_AGENT-535.md
  - imports/2026-07-17_monday_hydraulics_context_and_next_steps.json
  - operational_notes/07-26/17/2026-07-17_WEEKEND_NEXT_MODEL_HANDOFF_PLAN.md
task: AGENT-535
date: 2026-07-17
role: Hydraulics/Writer
type: operational_note
status: complete
---
# Monday Hydraulics Context And Next Steps

This is a supplemental handoff for a fresh agent starting Monday,
2026-07-20. It focuses on the hydraulic/F6/two-tap extractor line that landed
on Friday, 2026-07-17. The broader weekend/model handoff lives in
`operational_notes/07-26/17/2026-07-17_WEEKEND_NEXT_MODEL_HANDOFF_PLAN.md`.

AGENT-534 owns the main Monday fresh-agent handoff path. Do not edit that path
from this note's task scope unless AGENT-534 has completed or a new row claims
it explicitly.

## Open First

Open these files in order:

1. `.agent/BOARD.md`
2. `.agent/STATE.md` and `.agent/BLOCKERS.md` if present and current
3. `operational_notes/07-26/17/2026-07-17_WEEKEND_NEXT_MODEL_HANDOFF_PLAN.md`
4. `operational_notes/maps/pressure-and-momentum-budget.md`
5. `work_products/2026-07/2026-07-17/2026-07-17_named_pressure_extraction_readiness/README.md`
6. `work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_contract/README.md`
7. `work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_extractor/README.md`
8. `work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_extractor/next_raw_postprocessing_queue.csv`
9. `work_products/2026-07/2026-07-17/2026-07-17_f6_nonrecirculating_pressure_anchor_plan/README.md`
10. `work_products/2026-07/2026-07-17/2026-07-17_f6_nonrecirculating_pressure_anchor_plan/next_action_plan.csv`

## Current Hydraulic State

Production hydraulic closure remains `F3_shah_apparent`. Do not replace it with
F6, H1, component K, branch-apparent K, or reset-development terms from the
Friday artifacts.

The current hydraulic evidence is useful but diagnostic:

- AGENT-523 reviewed 33 named pressure rows and found 0 fit-ready rows.
- AGENT-523 split those rows into 3 component/cluster repair targets, 6
  branch/straight repair targets, and 24 diagnostic/section-effective rows.
- AGENT-525 selected the nearest component/cluster repair lane: the three
  `corner_lower_right` Salt2/Salt3/Salt4 rows.
- AGENT-525 found centerline tap lengths for those rows, but the current
  centerline straight-reference subtraction makes all local K values negative.
- AGENT-530 emitted the requested future extractor schema for those three rows
  from existing evidence only.
- AGENT-530 kept all rows diagnostic: 0 ordinary admissions, 3 missing endpoint
  pressure rows, 3 negative current `K_local` rows, and 15 failed gate rows.
- The non-recirculating F6 plan keeps PM5 as recirculation diagnostics: 12 PM5
  rows, 0 current ordinary F6 anchors.

The strongest pressure-map statement is still: per-segment Delta-P is a more
robust closure metric than mdot, but current pressure coefficients are not
admitted.

## What Was Implemented Friday

### AGENT-523: Named Pressure Extraction Readiness

Package:
`work_products/2026-07/2026-07-17/2026-07-17_named_pressure_extraction_readiness/`

Important files:

- `named_pressure_readiness.csv`
- `next_pressure_extraction_queue.csv`
- `pressure_readiness_summary.csv`
- `summary.json`

Key result:

- 33 named pressure rows reviewed.
- 0 fit-ready rows.
- 5 next extraction lanes:
  `raw_two_tap_connector_and_component_repair`,
  `pressure_and_velocity_basis_finalization`,
  `recirculation_mask_and_section_effective_policy`,
  `same_qoi_mesh_time_uncertainty_attachment`,
  `reset_development_basis_to_Fluid_API_contract`.

### AGENT-525: Two-Tap Component Repair Contract

Package:
`work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_contract/`

Important files:

- `component_repair_targets.csv`
- `repair_field_contract.csv`
- `future_extractor_schema.csv`
- `acceptance_gate_matrix.csv`
- `summary.json`

Key result:

- 3 target rows: `corner_lower_right` for Salt2/Salt3/Salt4.
- 7 required field rows.
- 17 required future extractor columns.
- 5 acceptance gates.
- 0 ordinary admissions.

### AGENT-530: Two-Tap Component Repair Extractor

Package:
`work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_extractor/`

Important files:

- `two_tap_component_repair_output.csv`
- `extractor_gate_results.csv`
- `next_raw_postprocessing_queue.csv`
- `extractor_summary.csv`
- `summary.json`

Key result:

- 3 schema rows emitted.
- Supported fields were filled from preserved/staged evidence.
- Unsupported fields were intentionally left blank:
  `p_upstream_pa`, `p_downstream_pa`, `RAF`, `RMF`, `SVF`, and
  `mesh_time_uncertainty`.
- All rows remain
  `diagnostic_blocked_missing_raw_endpoint_pressure_basis_recirculation_UQ`.

## Why The Rows Are Still Blocked

Do not infer missing values. The current evidence does not support ordinary K
because:

- local endpoint pressure surfaces are missing for the target feature;
- pressure and velocity bases remain proxy or partially preserved quantities;
- the current straight-reference subtraction over-subtracts and drives K
  negative;
- component isolation from reset/development and branch-apparent loss is not
  proven;
- same-window RAF/RMF/SVF are missing for the feature taps;
- same-QOI mesh/time uncertainty is missing.

Negative `K_local` is not a value to clip. It is evidence that the current
straight-reference/component-isolation basis is not physically admissible.

## Monday Next Steps

### Step 1: Check Active Rows Before Editing

Before doing anything, read `.agent/BOARD.md`. As of Friday evening, active or
recent collision-sensitive rows include AGENT-519 scheduler monitor, AGENT-534
main Monday handoff, and model/figure rows around AGENT-526 through AGENT-529.

Do not edit active-agent paths. If the row is complete but still under Active,
inspect its status/import/README and either avoid it or claim a cleanup row.

### Step 2: Claim A Raw Postprocessing Contract Row

Recommended task name:
`TODO-TWO-TAP-COMPONENT-RAW-ENDPOINTS` or next available `AGENT-5xx`.

Allowed edit paths should include:

- `.agent/BOARD.md` own row only
- `.agent/status/<date>_TODO-TWO-TAP-COMPONENT-RAW-ENDPOINTS.md`
- `.agent/journal/<date>/two-tap-component-raw-endpoints.md`
- `imports/<date>_two_tap_component_raw_endpoints.json`
- `tools/analyze/build_two_tap_component_raw_endpoint_plan.py`
- `tools/analyze/test_two_tap_component_raw_endpoint_plan.py`
- `work_products/<date>_two_tap_component_raw_endpoint_plan/**`

Start with a plan/contract package, not a solver launch.

### Step 3: Turn AGENT-530 Queue Into A Sampling Plan

Use:
`work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_extractor/next_raw_postprocessing_queue.csv`

The plan should emit:

- `target_feature_taps.csv`
- `pressure_surface_sampling_contract.csv`
- `basis_field_contract.csv`
- `recirculation_metric_contract.csv`
- `same_qoi_uncertainty_contract.csv`
- `launch_readiness_gate.csv`
- `source_manifest.csv`
- `summary.json`

Minimum target:

- Salt2/Salt3/Salt4
- feature `corner_lower_right`
- same time windows used by the current staged raw-pressure evidence:
  Salt2 `7915`, Salt3 `7618`, Salt4 `10000`

The output contract must include:

- upstream/downstream tap labels;
- `p_upstream_pa` and `p_downstream_pa`;
- pressure basis: static/total/p_rgh plus hydrostatic and kinetic correction
  policy;
- velocity/dynamic-pressure basis and local density basis;
- straight-reference label and subtraction method;
- RAF/RMF/SVF at the same window;
- mesh/time uncertainty status for the same pressure-loss QoI.

### Step 4: Only Then Consider Staged-Copy Postprocessing

After the plan passes tests, a separate task may stage copies and run sampling
on a compute node or through Slurm. Do not mutate native OpenFOAM outputs.

The staged run must not write into imported/native case directories. It should
write under a task-owned `tmp/` or `work_products/` path and record exact source
case paths in a manifest.

Required acceptance before coefficient use:

- finite endpoint pressures with tap labels;
- no pressure-term double counting;
- physically comparable straight reference;
- K is not clipped;
- RAF < 0.01 and RMF < 0.01 for ordinary rows;
- same-QOI mesh/time uncertainty attached or explicit diagnostic-only status.

### Step 5: Rebuild The Extractor From Raw Outputs

Once raw endpoint evidence exists, create a new extractor package rather than
overwriting AGENT-530. It should consume the new raw package and emit a new
version of:

- `two_tap_component_repair_output.csv`
- `extractor_gate_results.csv`
- `component_admission_review.csv`
- `next_action_or_admission_decision.json`

Expected outcome is still likely diagnostic. Admission is allowed only if all
predeclared gates pass.

### Step 6: Keep F6 Separate From Component-K Work

The F6 non-recirculating pressure-anchor plan says:

- PM5 is diagnostic recirculation evidence.
- Pending PM10/high-heat rows are only ordinary-anchor candidates after
  terminal harvest and low-reverse same-window pressure gates.
- Do not fit F6 until legitimate ordinary anchors exist.

If high-heat or PM10 jobs are terminal Monday, claim a separate terminal
harvest/admission row. Do not mix that with the component-K extractor row.

## Guardrails

Do not:

- mutate native CFD/OpenFOAM outputs;
- mutate registry/admission state;
- submit, cancel, requeue, or dependency-edit scheduler jobs from a docs-only or
  contract task;
- run OpenFOAM or long Fluid work on login nodes;
- use Salt3, +/-5Q, `val_salt2`, or future CFD rows for fitting/model selection
  outside their declared split role;
- use realized CFD `wallHeatFlux`, CFD mdot, or validation temperatures as
  runtime inputs;
- clip negative K to zero;
- export a universal K or hidden global friction multiplier;
- treat PM5 recirculation diagnostics as ordinary F6 anchors;
- treat mdot improvement alone as model admission.

## Quick Claim Template For Monday

Use this as a starting point for the next board row:

`TODO-TWO-TAP-COMPONENT-RAW-ENDPOINTS | Coordinator / Hydraulics / cfd-pp / Implementer / Tester / Writer | <owner> | .agent/BOARD.md own row only, status, journal, import manifest, tools/analyze/build_two_tap_component_raw_endpoint_plan.py, tools/analyze/test_two_tap_component_raw_endpoint_plan.py, work_products/<date>_two_tap_component_raw_endpoint_plan/**. READ-ONLY: active scopes, AGENT-523/525/530 packages except cited inputs, native CFD/OpenFOAM outputs, registry/admission state, scheduler state, generated docs indexes, Fluid source tree, external cfd-modeling-tools. No native-output mutation, no registry mutation, no scheduler action, no solver/postprocessing launch, no generated-index refresh, no Fluid edit, no fitting/tuning/model selection, no scientific admission change. | Build a raw endpoint pressure and same-window flow-diagnostic sampling contract for corner_lower_right Salt2/Salt3/Salt4 component-K repair. STATUS: ACTIVE <date>.`

## Success Criteria For Monday

A good Monday morning pass should produce one of these:

- a tested raw-endpoint sampling contract and no launch;
- a tested staged-copy postprocessing launcher, if and only if the contract is
  complete and a separate scheduler/postprocessing row claims it;
- a new extractor package that consumes landed raw endpoint evidence and still
  honestly reports diagnostic status;
- a clear blocker note explaining exactly which raw fields cannot be produced
  from available case data.

Do not end Monday with an unreviewed coefficient, a hidden fit, or a mutated
native case tree.
