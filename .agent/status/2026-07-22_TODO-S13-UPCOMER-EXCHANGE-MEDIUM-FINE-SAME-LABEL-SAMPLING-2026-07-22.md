---
provenance:
  - tools/analyze/build_s13_upcomer_exchange_medium_fine_same_label_sampling.py
  - tools/analyze/test_s13_upcomer_exchange_medium_fine_same_label_sampling.py
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_same_label_sampling/summary.json
task: TODO-S13-UPCOMER-EXCHANGE-MEDIUM-FINE-SAME-LABEL-SAMPLING-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: status
status: complete
tags: [status, s13, upcomer-exchange, medium-fine, mesh-gci, same-label]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_same_label_sampling
---

# TODO-S13-UPCOMER-EXCHANGE-MEDIUM-FINE-SAME-LABEL-SAMPLING-2026-07-22

## Objective

Answer whether existing Salt2/Salt3/Salt4 medium/fine source runs can be used
to advance S13 same-label mesh/GCI, and distinguish source-run availability
from already-published exact S13 medium/fine rows.

## Outcome

Decision: `medium_fine_runs_exist_exact_s13_rows_absent_sampling_contract_ready`.

The medium and fine source runs are present for Salt2/Salt3/Salt4. All six have
readable `processors*` directories, terminal primitive fields needed by the
four S13 labels, and postProcessing families that can support provenance and
sanity checks. The exact medium/fine S13 rows are still absent because those
fields have not been sampled over the S13 trusted wall, exchange-interface,
recirculation-CV, and wall/core/bulk masks with the exact label/formula/sign
contract.

Strict current-coarse contract times are not present on medium/fine. Terminal
candidate windows are available:

- Salt2 medium/fine: `516;517;518` and `397;398;399`.
- Salt3 medium/fine: `1338;1339;1340` and `531;532;533`.
- Salt4 medium/fine: `1157;1158;1159` and `415;416;417`.

Mesh/GCI remains closed until a compute-node sampling row either proves a
terminal-window mesh-time equivalence gate or publishes a fail-closed mesh/GCI
result.

## Changes Made

- Added `tools/analyze/build_s13_upcomer_exchange_medium_fine_same_label_sampling.py`.
- Added `tools/analyze/test_s13_upcomer_exchange_medium_fine_same_label_sampling.py`.
- Wrote `medium_fine_source_run_inventory.csv`.
- Wrote `existing_postprocessing_reuse_matrix.csv`.
- Wrote `s13_exact_label_sampling_need_matrix.csv`.
- Wrote `sampling_command_contract.csv`.
- Wrote `mesh_gci_readiness_after_medium_fine_inventory.csv`.
- Wrote package `README.md`, `summary.json`, and `source_manifest.csv`.
- Updated `.agent/BOARD.md` own row.

## Validation

- `python3.11 -m py_compile tools/analyze/build_s13_upcomer_exchange_medium_fine_same_label_sampling.py tools/analyze/test_s13_upcomer_exchange_medium_fine_same_label_sampling.py`: passed.
- `python3.11 -m unittest tools.analyze.test_s13_upcomer_exchange_medium_fine_same_label_sampling`: passed, `4` tests in `0.995 s`.
- `python3.11 tools/analyze/build_s13_upcomer_exchange_medium_fine_same_label_sampling.py`: passed; generated the medium/fine inventory and sampling contract.

## Guardrails

- Native solver outputs mutated: false.
- Registry/admission mutated: false.
- Scheduler/sampler/solver/postprocessing launched: false.
- Mesh/GCI computed: false.
- Production harvest or coefficient admission: false.
- Source/property or Qwall release: false.
- S11/S12/S13/S15/S6 trigger: false.
- Existing endpoint/probe/profile results relabeled as exact S13 rows: false.
