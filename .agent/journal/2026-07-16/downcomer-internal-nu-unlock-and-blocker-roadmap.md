---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_downcomer_internal_nu_unlock_and_blocker_roadmap/README.md
  - work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/README.md
tags: [journal, AGENT-466, internal-nu, downcomer, litrev-gates, blocker-roadmap]
related:
  - .agent/status/2026-07-16_AGENT-466.md
  - imports/2026-07-16_downcomer_internal_nu_unlock_and_blocker_roadmap.json
task: AGENT-466
date: 2026-07-16
role: Coordinator/Thermal-modeling/Internal-Nu/Mesh-GCI/Implementer/Tester/Writer
type: journal
status: complete
---
# Downcomer Internal-Nu Unlock And Blocker Roadmap

## Files Inspected

- `work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/branch_local_thermal_admission.csv`
- `work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/internal_nu_fit_admissible_rows.csv`
- `work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/final_use_closure_qoi_gci.csv`
- `work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/README.md`
- `work_products/2026-07/2026-07-16/2026-07-16_f6_upcomer_blocker_status_scorecard/README.md`
- `operational_notes/maps/literature-synthesis-and-gates.md`

## Files Changed

- `tools/analyze/build_downcomer_internal_nu_unlock_and_blocker_roadmap.py`
- `tools/analyze/test_downcomer_internal_nu_unlock_and_blocker_roadmap.py`
- `work_products/2026-07/2026-07-16/2026-07-16_downcomer_internal_nu_unlock_and_blocker_roadmap/*`
- `.agent/blockers.yml`
- `.agent/status/2026-07-16_AGENT-466.md`
- `.agent/journal/2026-07-16/downcomer-internal-nu-unlock-and-blocker-roadmap.md`
- `imports/2026-07-16_downcomer_internal_nu_unlock_and_blocker_roadmap.json`
- `operational_notes/maps/thermal-closures-and-internal-nu.md`
- `operational_notes/maps/mesh-gci-and-uncertainty.md`
- `operational_notes/maps/forward-predictive-model.md`

## Observations

The downcomer is still the cleanest first ordinary non-upcomer Internal-Nu lane,
but current evidence does not admit it. The single downcomer Nu candidate has
residual-owner evidence only partially passing (`4/5`) and has `0/5`
sign/heat-balance, recirculation, and mesh/GCI pass rows.

The LitRev methodology changes the action from "fit Nu next" to "admit the
branch next." The next downcomer artifact must prove row-level sign/enthalpy,
low-recirculation or non-recirculating validity, and same-QOI publication-ready
GCI before any ordinary Nu correlation is fitted.

The roadmap records later studies for heater source/sign, cooler/HX boundary
separation, upcomer hybrid/onset, same-QOI GCI, coupled M3+TS, F6, wall thermal
circuit, segment pressure/thermal models, boundary-layer development, and thesis
upcomer-recirculation prose.

## Commands Run

- `python3.11 -m unittest tools.analyze.test_downcomer_internal_nu_unlock_and_blocker_roadmap`
- `python3.11 tools/analyze/build_downcomer_internal_nu_unlock_and_blocker_roadmap.py`

## Result

`closure-qoi-mesh-gci` remains open but is narrower: the downcomer-first attempt
is resolved to a specific blocking tuple rather than a vague Internal-Nu
blocker. Current next actions should target downcomer policy/low-recirculation
admission or coupled M3+TS scoring, not global Nu tuning.
