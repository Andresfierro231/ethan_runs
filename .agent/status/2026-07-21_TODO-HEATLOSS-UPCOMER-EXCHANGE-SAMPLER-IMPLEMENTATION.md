---
provenance:
  - tools/extract/sample_upcomer_exchange_cell.py
  - tools/extract/test_sample_upcomer_exchange_cell.py
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_sampler_implementation/IMPLEMENTATION_NOTE.md
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_sampler_implementation/exchange_sampler_rows.csv
tags: [heat-loss, upcomer, exchange-cell, sampler-implementation, fail-closed, status]
related:
  - .agent/journal/2026-07-21/heatloss-upcomer-exchange-sampler-implementation.md
  - imports/2026-07-21_heatloss_upcomer_exchange_sampler_implementation.json
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_source_field_audit/README.md
task: TODO-HEATLOSS-UPCOMER-EXCHANGE-SAMPLER-IMPLEMENTATION
date: 2026-07-21
role: Implementer/Tester/Writer/Thermal-modeling/Hydraulics/cfd-pp
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-HEATLOSS-UPCOMER-EXCHANGE-SAMPLER-IMPLEMENTATION

## Objective

Extend `tools/extract/sample_upcomer_exchange_cell.py` so a future execution
row can emit explicit extraction rows from supplied VTK inputs, or fail closed
when required inputs are missing. Keep the work synthetic/dry: no production
sampler launch, OpenFOAM execution, scheduler action, fit, score, or closure
admission.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_sampler_implementation/`.

The sampler now has:

- a stable extraction-row field list;
- CSV/JSON row writers;
- CLI controls for supplied cell, interface, and wall VTK files;
- normals for throughflow and exchange-interface orientation;
- optional pressure and energy residual inputs;
- fail-closed unavailable rows when required VTK inputs are absent;
- guard columns `fit_allowed_now=false` and `score_allowed_now=false`;
- explicit residual policy `do_not_hide_heat_residual_in_internal_Nu`.

The generated package includes one dry Salt2 `7915` row with
`extraction_status=not_available_with_reason:missing_required_vtk_inputs` and
`missing_inputs=cell_vtk;interface_vtk`. This is intentional: production
extraction remains blocked until a separate row supplies trusted VTK, volume,
mask, and source/sink ledger inputs.

## Changes Made

- Updated `tools/extract/sample_upcomer_exchange_cell.py`.
- Updated `tools/extract/test_sample_upcomer_exchange_cell.py`.
- Generated the implementation package and fail-closed dry extraction row.
- Added an implementation-specific note and summary for the current task.
- Added this status file, journal entry, and import manifest.
- Updated `.agent/BOARD.md` own row.

## Validation

- `python3.11 -m py_compile tools/extract/sample_upcomer_exchange_cell.py tools/extract/test_sample_upcomer_exchange_cell.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_sample_upcomer_exchange_cell`:
  passed, `8` tests.
- `python3.11 tools/extract/sample_upcomer_exchange_cell.py --output-dir work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_sampler_implementation --emit-extraction-row --case-id salt_2 --time-window-s 7915`:
  passed and emitted the fail-closed `exchange_sampler_rows.csv/json`.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_sampler_implementation`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_sampler_implementation --strict`:
  passed, `candidate_rows=0`, `findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_sampler_implementation`:
  passed.

## Unresolved Blockers

- No production CFD extraction has been run.
- The source-field audit still blocks production extraction on missing or
  unadmitted `mu`, `cellVolume`, `recircMask`, exchange-interface VTK,
  wall/core surface VTK, and source/sink ledger inputs.
- Same-QOI UQ and Phase 4B rescore remain separate blocked work packages.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Solver/postprocessing/production sampler execution launched: no.
- Fluid source edited: no.
- External repository edited: no.
- Fitting, tuning, model selection, or closure admission changed: no.
- Blocker register changed: no.
- Generated documentation indexes refreshed: no.
- Phase 4B rescore run: no.
- Phase 5/S6 trigger changed: no.
- Heat residual absorbed into internal Nu: no.
