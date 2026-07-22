---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split/admission_split_table.csv
  - work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_terminal_admission_gate/corrected_q_terminal_gate_rows.csv
tags: [cfd-pp, admission, boundary-conditions, validation-split, corrected-q]
related:
  - operational_notes/maps/cfd-runs-and-admission.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - reports/thesis_dossier/master_thesis_bullet_outline.md
task: AGENT-331
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# CFD Case Admission Inventory

This package turns current CFD run/admission evidence into case-level and
boundary-role tables for downstream training, validation, and holdout use.

## Result

- Admitted now under the current split: `salt_2` as training, `salt_3` as
  validation, and `salt_4` as holdout.
- Diagnostic/context only: Salt1 nominal and Salt1 corrected-Q terminal harvest
  rows; these still need an explicit Salt1 admission policy before closure use.
- Blocked/pending: all corrected Salt-Q rows. Job `3293924` selected four rows
  for continuation, but the terminal gate package still reports zero admitted
  corrected-Q rows.
- Excluded: Kirst rows are historical, and the original Q/insulation sweep is
  false-steady/quarantined.

## Boundary Semantics

Mainline Salt2/3/4 boundary labels come from the July 13 patch-role audit.
`rcExternalTemperature` rows include emissivity/Tsur radiation, and radiation is
folded into total OpenFOAM `wallHeatFlux`; there is no separate exported `qr`
term. Corrected-Q selected live rows have clean runtime preflight evidence for
heater/cooler values, but still need terminal patch/heat-flux reduction before
admission.

## Outputs

- `cfd_case_admission_inventory.csv`
- `boundary_condition_role_table.csv`
- `training_validation_holdout_candidate_table.csv`
- `source_manifest.csv`
- `summary.json`

## Counts

- Case rows: 20
- Boundary rows: 38
- Training rows now: salt_2
- Validation rows now: salt_3
- Holdout rows now: salt_4

No native CFD solver outputs were modified.
