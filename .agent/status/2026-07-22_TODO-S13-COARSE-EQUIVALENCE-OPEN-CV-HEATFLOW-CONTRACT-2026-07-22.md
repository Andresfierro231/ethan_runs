---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract/coarse_basis_resolution.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract/open_cv_use_policy.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract/source_side_heatflow_focus.csv
tags: [status, s13, recirculation, open-cv, coarse-equivalence, source-side-heat-flow]
related:
  - .agent/journal/2026-07-22/s13-coarse-equivalence-open-cv-heatflow-contract.md
  - imports/2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_mesh_gci_disposition/README.md
task: TODO-S13-COARSE-EQUIVALENCE-OPEN-CV-HEATFLOW-CONTRACT-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# TODO-S13-COARSE-EQUIVALENCE-OPEN-CV-HEATFLOW-CONTRACT-2026-07-22

## Objective

Resolve whether existing current-coarse S13 rows can serve as same-label coarse
evidence, write an auditable coarse-equivalence contract, and state the policy
for open recirculation CVs, averaged values, and source-side heat-flow matching.

## Outcome

Complete. Decision:
`coarse_reference_candidate_only_equivalence_contract_defined_no_gci_no_admission`.

Current-coarse reconstructed rows exist for all three cases and four S13 QOIs
(`12` candidate rows), but they are not admitted as same-label coarse evidence.
They remain reference candidates because geometry-mask provenance,
time-window equivalence, field/source/property basis, and residual-complete CV
criteria have not been audited as a joined coarse/medium/fine triplet.

Open recirculation CVs are allowed for diagnostics if every cut surface,
normal convention, flux term, storage term, source/wall term, and residual is
explicit. A closed or residual-complete CV is required before exchange-cell
coefficient fitting or admission.

Averaged values are allowed for intensive reduced states such as `T_recirc` only
when the weighting basis is explicit. Fluxes, integrals, and residuals must be
integrated from signed terms first; average-field substitutes remain diagnostic
only.

Heat-flow matching should focus on the source-side heat-flow equivalence and
same-basis energy residual. `Q_wall_W` is mesh-close, but source-side heat flow
is a distinct QOI and remains much larger than direct wall heat in the current
diagnostic: `Q_wall_W / Q_source_side_net_static_bc_W` is about `0.137-0.139`.

## Changes Made

- Added reusable builder:
  `tools/analyze/build_s13_coarse_equivalence_open_cv_heatflow_contract.py`.
- Added tests:
  `tools/analyze/test_s13_coarse_equivalence_open_cv_heatflow_contract.py`.
- Generated package:
  `work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract/`.
- Generated:
  `coarse_basis_resolution.csv`,
  `auditable_coarse_equivalence_contract.csv`,
  `open_cv_use_policy.csv`,
  `averaged_value_policy.csv`,
  `source_side_heatflow_focus.csv`,
  `production_admission_gate.csv`,
  `source_manifest.csv`,
  `summary.json`, and `README.md`.
- Updated own board row, this status, matching journal, and import manifest.

## Validation

- `python3.11 -m pytest tools/analyze/test_s13_coarse_equivalence_open_cv_heatflow_contract.py`:
  passed, `6` tests.
- `python3.11 -m py_compile tools/analyze/build_s13_coarse_equivalence_open_cv_heatflow_contract.py tools/analyze/test_s13_coarse_equivalence_open_cv_heatflow_contract.py`:
  passed.
- `python3.11 tools/analyze/build_s13_coarse_equivalence_open_cv_heatflow_contract.py`:
  passed and regenerated the package outputs.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: `false`.
- Registry/admission state mutated: `false`.
- Scheduler action: `false`.
- Solver/postProcess/sampler/harvest/UQ launched: `false`.
- Generated docs index refreshed: `false` because another active row owns that path.
- Formal GCI unlocked/admitted: `false`.
- Production harvest/admission: `false`.
- Source/property or Qwall release: `false`.
- Coefficient fitting/admission: `false`.
- Validation/holdout/external-test scoring: `false`.
- S11/S12/S13/S15/S6 trigger: `false`.

## Next Useful Action

The practical unlock is a coarse-equivalent joined triplet audit or a coarse
rerun through the repaired exact-label sampler on the same contract as
medium/fine. For heat-flow matching, the next package should build the
same-basis energy residual using direct `Q_wall_W`, source-side heat flow,
enthalpy exchange terms, and released cp/property provenance without fitting a
coefficient.
