---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_heater_lower_leg_source_sign_gci_admission/README.md
  - work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/README.md
tags: [journal, AGENT-468, internal-nu, heater, closure-qoi, mesh-gci]
related:
  - .agent/status/2026-07-16_AGENT-468.md
  - imports/2026-07-16_heater_lower_leg_source_sign_gci_admission.json
task: AGENT-468
date: 2026-07-16
role: Coordinator/Thermal-modeling/Mesh-GCI/Implementer/Tester/Writer
type: journal
status: complete
---
# Heater Lower-Leg Source/Sign/GCI Admission

## Files Inspected

- `work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/branch_local_thermal_admission.csv`
- `work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/internal_nu_fit_admissible_rows.csv`
- `work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/final_use_closure_qoi_gci.csv`
- `work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/targeted_extraction_admission_queue.csv`
- `work_products/2026-07/2026-07-16/2026-07-16_downcomer_internal_nu_unlock_and_blocker_roadmap/future_studies_and_blockers.csv`
- `.agent/blockers.yml`

## Files Changed

- `tools/analyze/build_heater_lower_leg_source_sign_gci_admission.py`
- `tools/analyze/test_heater_lower_leg_source_sign_gci_admission.py`
- `work_products/2026-07/2026-07-16/2026-07-16_heater_lower_leg_source_sign_gci_admission/*`
- `.agent/blockers.yml`
- `.agent/status/2026-07-16_AGENT-468.md`
- `.agent/journal/2026-07-16/heater-lower-leg-source-sign-gci-admission.md`
- `imports/2026-07-16_heater_lower_leg_source_sign_gci_admission.json`

## Observations

The heater lower leg is still blocked as an ordinary Internal-Nu fit lane. The
branch summary has `7` candidate rows and `2` Nu-equivalent rows, but no row
passes source-fit, sign/heat-balance, recirculation, or mesh/GCI gates. The
single row-level Salt2 heater Nu candidate has residual-owner evidence but
fails source, sign/heat-balance, recirculation, and mesh/GCI gates; the
branch-level heater row also fails residual-owner.

The final-use heater GCI set has `6` rows and no publication-ready rows. HTC and
UA_prime are blocked by sign review; Nu is missing a reconciled coarse/medium/fine
triplet; lower-leg hydraulic rows are non-publication due to non-monotone or
divergent current triplets.

## Commands Run

- `python3.11 -m py_compile tools/analyze/build_heater_lower_leg_source_sign_gci_admission.py tools/analyze/test_heater_lower_leg_source_sign_gci_admission.py`
- `python3.11 tools/analyze/test_heater_lower_leg_source_sign_gci_admission.py`
- `python3.11 tools/analyze/build_heater_lower_leg_source_sign_gci_admission.py`

## Result

`closure-qoi-mesh-gci` remains open but is narrower. The next heater actions are
now explicit: source/enthalpy/sign heat-balance admission, same-QOI Nu-or-HTC/UA
GCI reconciliation, heater branch recirculation evidence, and lower-leg
hydraulic final-use exclusion or re-extraction.
