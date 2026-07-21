---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_reusable_harvest_scaffold/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_reusable_harvest_scaffold/case_volume_input_map.csv
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_reusable_harvest_scaffold/required_vtk_input_contract.csv
tags: [upcomer, exchange-cell, reusable-scripts, harvest-scaffold, no-scheduler]
related:
  - .agent/journal/2026-07-21/upcomer-exchange-sampler-reusable-harvest-scaffold.md
  - imports/2026-07-21_upcomer_exchange_sampler_reusable_harvest_scaffold.json
task: TODO-UPCOMER-EXCHANGE-SAMPLER-REUSABLE-HARVEST-SCAFFOLD-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-UPCOMER-EXCHANGE-SAMPLER-REUSABLE-HARVEST-SCAFFOLD-2026-07-21

## Objective

Create reusable, fail-closed scripts and manifests that let a later task run the
dry upcomer exchange-cell sampler once same-window cell/interface/wall/source
inputs exist.

## Outcome

Complete. The package wires `3` Salt2/Salt3/Salt4 ready cell-volume CSVs into a
case map, publishes `12` VTK/source contract rows, carries forward `12` geometry
and source blocker rows, and emits `4` reusable scripts:

- `scripts/validate_exchange_case_inputs.py`
- `scripts/harvest_one_exchange_case.sh`
- `scripts/harvest_exchange_case_matrix.sh`
- `scripts/check_exchange_outputs.py`

The manifest template intentionally fails validation until real same-window VTK
paths and explicit throughflow/interface normal vectors are supplied.

## Changes Made

- `tools/extract/build_upcomer_exchange_sampler_reusable_harvest_scaffold.py`
- `tools/extract/test_build_upcomer_exchange_sampler_reusable_harvest_scaffold.py`
- `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_reusable_harvest_scaffold/**`
- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-UPCOMER-EXCHANGE-SAMPLER-REUSABLE-HARVEST-SCAFFOLD-2026-07-21.md`
- `.agent/journal/2026-07-21/upcomer-exchange-sampler-reusable-harvest-scaffold.md`
- `imports/2026-07-21_upcomer_exchange_sampler_reusable_harvest_scaffold.json`

## Validation

- `python3.11 -m py_compile tools/extract/build_upcomer_exchange_sampler_reusable_harvest_scaffold.py tools/extract/test_build_upcomer_exchange_sampler_reusable_harvest_scaffold.py tools/extract/sample_upcomer_exchange_cell.py`: passed.
- `python3.11 -m unittest tools.extract.test_build_upcomer_exchange_sampler_reusable_harvest_scaffold tools.extract.test_sample_upcomer_exchange_cell`: passed, `13` tests.
- `python3.11 tools/extract/build_upcomer_exchange_sampler_reusable_harvest_scaffold.py`: passed; summary reports `3` ready volume CSVs, `12` VTK contract rows, `12` blocker rows, and no sampler/scheduler action.
- `bash -n` on generated `harvest_one_exchange_case.sh` and `harvest_exchange_case_matrix.sh`: passed.
- `python3.11 -m py_compile` on generated `validate_exchange_case_inputs.py` and `check_exchange_outputs.py`: passed.
- `python3.11 .../validate_exchange_case_inputs.py .../case_vtk_input_manifest.template.csv`: failed closed with exit `66` and missing `cell_vtk` messages for Salt2/Salt3/Salt4, as intended.
- `python3.11 tools/agent/runtime_input_lint.py ...`: passed.
- `python3.11 tools/agent/source_property_gate.py ... --strict`: passed with `candidate_rows=0` and `findings=0`.
- `python3.11 tools/agent/split_policy_lint.py ...`: passed.

## Unresolved Blockers

- Same-window `cell_vtk` with U/T/rho and cell ID or stable volume order.
- Named `exchange_interface_vtk` with U/rho/area and normal sign convention.
- `wall_vtk` for wall-core Delta T and optional heat-flux diagnostic.
- Same-window source/sink ledger with `Q_source_W`, `Q_sink_W`, `cp_J_kg_K`, sign convention, and source paths.
- Sampler harvest, scheduler submission, Phase 4B rescore, Phase 5/S6, fitting, scoring, and exchange-cell admission remain separate tasks.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Solver/OpenFOAM postprocessing/sampler launched: no.
- Fluid source edited: no.
- External repository edited: no.
- Fitting, tuning, model selection, score release, or closure admission changed: no.
- Blocker register changed: no.
- Generated documentation indexes refreshed: no.
- Phase 4B rescore, Phase 5, or S6 trigger changed: no.
