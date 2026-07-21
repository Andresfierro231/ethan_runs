---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_tswfc2_fluid_api_contract/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_tswfc2_fluid_api_contract/next_step_handoff.csv
  - work_products/2026-07/2026-07-18/2026-07-18_tswfc2_fluid_api_contract/node_geometry_reconciliation.csv
  - .agent/status/2026-07-18_TODO-TSWFC2-DISTRIBUTED-WALL-FLUID.md
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/README.md
tags: [handoff, forward-model, wall-fluid-coupling, test-section, tswfc2]
related:
  - .agent/status/2026-07-18_TODO-TSWFC2-NEXT-CONTEXT-HANDOFF.md
  - .agent/journal/2026-07-18/tswfc2-next-context-handoff.md
  - imports/2026-07-18_tswfc2_next_context_handoff.json
  - work_products/2026-07/2026-07-18/2026-07-18_tswfc2_fluid_api_contract/README.md
task: TODO-TSWFC2-NEXT-CONTEXT-HANDOFF
date: 2026-07-18
role: Forward-pred/Thermal-modeling/Writer
type: operational_note
status: complete
---
# TSWFC2 Next Context And Steps

This is the start-here note for the TSWFC2 distributed test-section wall/fluid
thread after the July 18 API implementation. It exists so the next agent can
make progress without chat logs and without accidentally treating the API
implementation as scored model evidence.

## Open First

1. `.agent/BOARD.md`
2. `work_products/2026-07/2026-07-18/2026-07-18_tswfc2_fluid_api_contract/README.md`
3. `work_products/2026-07/2026-07-18/2026-07-18_tswfc2_fluid_api_contract/summary.json`
4. `work_products/2026-07/2026-07-18/2026-07-18_tswfc2_fluid_api_contract/fluid_api_change_log.csv`
5. `work_products/2026-07/2026-07-18/2026-07-18_tswfc2_fluid_api_contract/node_geometry_reconciliation.csv`
6. `work_products/2026-07/2026-07-18/2026-07-18_tswfc2_fluid_api_contract/runtime_guardrail_audit.csv`
7. `work_products/2026-07/2026-07-18/2026-07-18_tswfc2_fluid_api_contract/next_step_handoff.csv`
8. `.agent/status/2026-07-18_TODO-TSWFC2-DISTRIBUTED-WALL-FLUID.md`
9. `.agent/journal/2026-07-18/tswfc2-distributed-wall-fluid-api.md`
10. `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/README.md`

## Current State

The Fluid solver now has a disabled-by-default TSWFC2 API:
`test_section_wall_fluid_mode = distributed_wall_fluid_nodes_v1`.

The implemented scenario fields are:

- `test_section_wall_fluid_mode`
- `test_section_wall_fluid_contact_multiplier`
- `test_section_wall_fluid_node_rows`

The active row mode consumes setup-only node rows with `node_id`, parent segment,
normalized `start_fraction` and `end_fraction`, `drive_selector`, and either
`hA_W_K` or `h_W_m2K` plus `area_m2`. It rejects unsupported modes, invalid
multipliers, fewer than four active rows, unknown parents, invalid fractions,
and missing or negative conductance before solve.

The marcher exports segment ledgers for matched spans: node IDs, node count,
fluid-to-inner-wall heat, wall-conduction heat, external heat, residual, and
estimated inner/outer wall temperatures.

The implementation is not a campaign result. There is no smoke case, scorecard,
fit, model selection, registry mutation, or admission change yet.

## Geometry Reconciliation

Preserve this corrected four-node split:

- `TSWFC2_N01_pre_test_bracket`: `left_lower_vertical`, fraction `0.80` to `1.00`
- `TSWFC2_N02_test_section_lower`: `test_section`, fraction `0.00` to `0.50`
- `TSWFC2_N03_test_section_upper`: `test_section`, fraction `0.50` to `1.00`
- `TSWFC2_N04_post_test_bracket`: `left_upper_vertical`, fraction `0.00` to `0.20`

The earlier dry-contract table put the test-section subnodes under
`left_upper_vertical`; the implementation corrected that because Fluid exposes
`test_section` as its own parent segment.

## Trusted Packages

- TSWFC2 Fluid API contract:
  `work_products/2026-07/2026-07-18/2026-07-18_tswfc2_fluid_api_contract/`
- TSWFC2 dry-contract predecessor:
  `work_products/2026-07/2026-07-18/2026-07-18_tswfc2_dry_contract/`
- Wall/test-section failure context:
  `work_products/2026-07/2026-07-18/2026-07-18_tp_tw_failure_forensics/`
- UMX1 smoke-blocked context:
  `work_products/2026-07/2026-07-18/2026-07-18_umx1_dry_smoke_scorer/`

## Validation Already Done

- `python -m py_compile tamu_loop_model_v2/solver.py tamu_loop_model_v2/config_loader.py tests/test_solver_contracts.py` passed.
- `python -m pytest tests/test_solver_contracts.py -q -k 'tswfc2 or scenario_config_defaults_match_active_solver_contract'` passed: 4 selected tests, 45 deselected.
- Extra broad `python -m pytest tests/test_solver_contracts.py -q` was
  interrupted after 4:26 with 13 tests passed and no failure summary. Do not
  present that interrupted run as a full-suite pass.

## Unresolved Blockers

The next blocker is not API existence. It is scenario/value selection and
execution authority for a small Fluid smoke row.

Still unresolved:

- no explicit scenario YAML row with curated TSWFC2 conductances
- no smoke run showing finite roots and nonzero TSWFC2 ledgers
- no temperature-shape scorecard versus M3/prior wall-source candidates
- no admission review

## Next Task Sequence

### 1. API Review Row

Claim a small reviewer row before changing code. Confirm the Fluid diff for
TSWFC2 only:

- disabled default is a no-op
- active mode requires distributed rows
- node matching uses Fluid parent segments and normalized fractions
- segment table exports the TSWFC2 ledger columns
- tests cover config parse, validation rejection, and marched ledger output

Acceptance: review either approves the API for smoke use or writes a precise
patch request. Do not fold unrelated dirty Fluid changes into the TSWFC2 review.

### 2. Smoke Scenario Preparation Row

Claim a separate Fluid/config row. Add one explicit scenario contract using the
four reconciled nodes and bounded setup conductances. The row must declare the
output root and whether execution is local, Slurm, or prepare-only.

Acceptance: scenario config loads and `scenario_records` exports the node rows.
No measured TP/TW, CFD mdot, realized CFD `wallHeatFlux`, imposed CFD cooler
duty, or holdout residual is allowed as a runtime input.

### 3. Smoke Execution Row

Run one or two predeclared cases only after the smoke scenario exists and a row
claims execution paths. The purpose is API/ledger sanity, not fitting.

Acceptance:

- finite root status
- segment output contains nonzero `tswfc2_node_count` on matched spans
- heat residuals are finite and near zero
- inner/outer wall temperatures are finite
- baseline disabled scenario remains available for comparison

Scheduler work requires an explicit scheduler row and handoff.

### 4. Temperature-Shape Scorecard Row

Only after smoke passes, build a scorecard separating train and holdout rows.
The acceptance signal is temperature shape, not mass flow alone.

Report at minimum:

- mdot absolute error
- TP RMSE
- TW RMSE
- all-probe RMSE
- TW5/TW6/TP5/TP6/TW8 shape probes where policy permits
- accepted-root status
- source/property labels
- runtime-input legality

Salt3 and any blind rows remain score-only and must not choose conductances,
bounds, exclusions, or fallback behavior.

## Output Contract For Future Rows

Every future TSWFC2 package should carry:

- exact Fluid commit/worktree context or source paths
- scenario YAML rows or generated config artifact
- four-node geometry table
- runtime-input audit
- root/finite-output audit
- segment-ledger extraction
- disabled-baseline comparison
- temperature-shape scorecard
- train versus holdout split
- source/property labels
- explicit flags for native-output, registry, scheduler, Fluid output, fitting,
  model-selection, and admission state

## Do Not Do

- Do not use TSWFC2 as an admitted model from the API implementation alone.
- Do not score only mdot and call it a thesis payoff.
- Do not use measured TP/TW, CFD mdot, realized CFD `wallHeatFlux`, imposed CFD
  cooler duty, or holdout/blind residuals as runtime inputs.
- Do not mutate native OpenFOAM outputs.
- Do not edit registry/admission state.
- Do not launch solver/postprocessing work without a new board row.
- Do not combine TSWFC2 with UMX1 until each path has independent smoke evidence
  or one path fails cleanly.
