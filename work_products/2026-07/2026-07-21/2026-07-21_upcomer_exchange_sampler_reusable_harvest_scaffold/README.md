---
task: TODO-UPCOMER-EXCHANGE-SAMPLER-REUSABLE-HARVEST-SCAFFOLD-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
tags: [upcomer, recirculation, exchange-cell, reusable-scripts, no-scheduler]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_design
---
# Upcomer Exchange Sampler Reusable Harvest Scaffold

This package turns the dry exchange-cell sampler into reusable, fail-closed
harvest plumbing. It wires the ready Salt2/Salt3/Salt4 cell-volume CSVs into a
manifest template and provides scripts that future rows can use once the
same-window cell, interface, wall, and source inputs exist.

## Current State

- case volume rows: `3`
- ready volume CSVs: `3`
- VTK/source contract rows: `12`
- blocker rows: `12`
- sampler harvest launched now: `false`
- scheduler action: `false`

The template intentionally contains `MISSING_*` placeholders and blank normal
vectors. `scripts/validate_exchange_case_inputs.py` rejects that template until
a later row supplies real same-window VTK paths and explicit normal vectors.

## Reusable Scripts

- `scripts/validate_exchange_case_inputs.py`: validates paths and normal-vector
  columns before any run.
- `scripts/harvest_one_exchange_case.sh`: invokes
  `tools/extract/sample_upcomer_exchange_cell.py` for one populated case.
- `scripts/harvest_exchange_case_matrix.sh`: validates and runs a populated
  case matrix.
- `scripts/check_exchange_outputs.py`: verifies one sampler row per output
  directory after harvest.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repository, blocker register, or generated docs index was
mutated. No OpenFOAM postprocessing, sampler harvest, fitting, model selection,
exchange-cell admission, Phase 4B rescore, Phase 5/S6 trigger, or internal-Nu
residual absorption was performed.
