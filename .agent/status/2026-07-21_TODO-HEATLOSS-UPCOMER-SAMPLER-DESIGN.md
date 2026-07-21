---
provenance:
  - tools/analyze/build_heatloss_upcomer_sampler_design.py
  - tools/analyze/test_heatloss_upcomer_sampler_design.py
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_sampler_design/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_sampler_design/summary.json
tags: [thermal-modeling, heat-loss, upcomer, sampler-design, status]
related:
  - .agent/journal/2026-07-21/heatloss-upcomer-sampler-design.md
  - imports/2026-07-21_heatloss_upcomer_sampler_design.json
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction/README.md
task: TODO-HEATLOSS-UPCOMER-SAMPLER-DESIGN
date: 2026-07-21
role: Implementer/Tester/Writer/Thermal-modeling/Hydraulics
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-HEATLOSS-UPCOMER-SAMPLER-DESIGN

## Objective

Build the Phase 1 sampler-design package: define exact output schema,
algorithm contract, dry-run emission matrix, validation cases, and execution
handoff for `V_recirc`, `mdot_exchange`, `tau_recirc`, paired thermal states,
wall-core Delta T, pressure residual, energy residual, and same-QOI UQ hooks.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_sampler_design/`.

- Output schema rows: `17`.
- Algorithm stage rows: `9`.
- Dry-run emission rows: `51`.
- Future implementation rows: `5`.
- Execution preflight case rows: `3`.
- Validation case rows: `5`.
- `tools/extract` edits: `false`.
- Solver/postprocessing/sampler launched: `false`.
- Fit or score allowed now: `false`.
- Residual absorbed into internal Nu: `false`.

The package is decision-complete for the next implementation row while
remaining design-only. It identifies current support for reverse-flow metrics
and the missing implementation pieces for recirculation volume, exchange flux,
residence time, paired thermal state, pressure residual, residual lanes, and
same-QOI UQ.

## Changes Made

- `tools/analyze/build_heatloss_upcomer_sampler_design.py`
- `tools/analyze/test_heatloss_upcomer_sampler_design.py`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_sampler_design/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_sampler_design/sampler_output_schema.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_sampler_design/algorithm_contract.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_sampler_design/dry_run_emission_matrix.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_sampler_design/future_implementation_change_list.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_sampler_design/execution_preflight_cases.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_sampler_design/validation_cases.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_sampler_design/source_manifest.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_sampler_design/summary.json`
- `.agent/status/2026-07-21_TODO-HEATLOSS-UPCOMER-SAMPLER-DESIGN.md`
- `.agent/journal/2026-07-21/heatloss-upcomer-sampler-design.md`
- `imports/2026-07-21_heatloss_upcomer_sampler_design.json`
- `.agent/BOARD.md` own row update

## Validation

- `python3.11 -m py_compile tools/analyze/build_heatloss_upcomer_sampler_design.py tools/analyze/test_heatloss_upcomer_sampler_design.py`:
  passed.
- `python3.11 tools/analyze/build_heatloss_upcomer_sampler_design.py`:
  passed; generated `17` schema rows, `9` algorithm rows, `51` dry-run rows,
  and `3` execution preflight cases.
- `python3.11 -m unittest tools.analyze.test_heatloss_upcomer_sampler_design`:
  passed, `7` tests.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_sampler_design`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_sampler_design --strict`:
  passed, `candidate_rows=0`, `findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_sampler_design`:
  passed.

## Unresolved Blockers

- The actual extractor still needs a separately claimed implementation row
  before `tools/extract/sample_upcomer_convection_cell.py` is edited.
- Compute-node execution must be claimed separately and run only with `sbatch`
  or `srun`.
- Same-QOI UQ must be attached after extracted QOI rows exist.
- Phase 4B rescore remains blocked until sampler execution and UQ pairing pass
  guard checks.

## Guardrails

- Native solver outputs: not mutated.
- Registry/admission state: not mutated.
- Scheduler state: not touched.
- Solver/postprocessing/sampler: not launched.
- `tools/extract`: not edited.
- Fluid source and external repositories: not edited.
- Fitting/tuning/model selection: not performed.
- Closure admission and scorecard trigger: not changed.
- Blocker register and generated docs index: not edited.
- Heat residual: kept separate from internal Nu.
