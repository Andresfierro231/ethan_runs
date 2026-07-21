---
provenance:
  - .agent/BLOCKERS.md
  - .agent/BOARD.md
  - operational_notes/07-26/14/2026-07-14_PROJECT_MISSION_AND_SCIENTIFIC_QUESTIONS.md
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-14_thesis_presentation_update.md
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_terminal_admission_gate/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_f6_hydraulic_screen/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_fluid_localized_h1_and_boundary_api/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_model_task_matrix/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_onset_blocker_resolution/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_table_update_cadence_contract/README.md
tags: [thesis-dossier, weekly-presentation, story-sync, admission-gate, blocker-audit, forward-v1]
related:
  - reports/thesis_dossier/README.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/mesh-gci-and-uncertainty.md
task: AGENT-329
date: 2026-07-14
role: Thesis/Presentation/Documentation
type: report
status: complete
supersedes:
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-14_thesis_presentation_update.md
superseded_by:
---
# Thesis / Presentation Story Sync - 2026-07-14

Purpose: update the human-facing story after the July 14 gate packages landed.
This note consumes the landed AGENT-327 boundary task matrix, does not promote
in-flight AGENT-328/330 results, and does not reopen stale blockers.

## What Changed Since The Prior Note

- Thermal mesh/admission is no longer pending: the refreshed mesh gate has `25`
  QOI rows, `0` publication-ready GCI rows, and `0` fit-admissible thermal rows.
- Internal-Nu policy is now explicit for forward-v1: `16` thermal admission rows
  give `0` fit rows, `11` validation-only rows, and `5` blocked rows.
- Final forward-v1 scorecard is decided for the current evidence set:
  `blocked_no_go_final_forward_v1_not_admitted`.
- Corrected Salt-Q job `3293924` was still non-terminal at the latest gate;
  all four selected rows remain `blocked_pending_terminal_gate`.
- Hydraulic evidence improved but did not close the blocker: H1 localized
  named-loss/reset proxy reduces `F1_heater_only` mean mdot error from
  `0.0054775` to `0.0021442 kg/s`, while F6 remains a candidate screen.
- Fluid gained a localized fixed-K hook, but reset/redevelopment semantics,
  calibrated Salt2/3/4 rerun evidence, and first-class boundary dictionaries
  remain unfinished.
- Boundary modeling now has a setup-only task order: run
  `BCM-HEATER-FRACTION-V1` first, then `BCM-COOLER-HX-UA-V1`. This is task
  prioritization, not a new admitted boundary closure.
- Upcomer onset remains open: current admitted evidence has only `3` recirculating
  points from Re `71.1` to `134.9`, below the documented onset midpoints.

## Trustworthy Wording

| Class | Say | Do not say |
| --- | --- | --- |
| Predictive | Forward-v0 execution works, and final forward-v1 has a current scored no-go. | The predictive model is admitted. |
| Calibrated | No final calibrated hydraulic, internal-Nu, HX, or wall-layer closure is admitted from these packages. | H1 or F6 is the selected final closure. |
| Diagnostic | Imposed cooler duty, H1 proxy, F6 screen, repaired thermal smoke, and validation-only thermal rows identify error lanes. | Diagnostic replay is predictive validation. |
| Blocked | Mesh/GCI, thermal parity/internal Nu, setup-only boundary/HX/wall models, corrected-Q terminal harvest, upcomer onset, Fluid API gaps, and F6 validation remain blockers. | Reconstructed-T corruption, no mesh families, OF13 reconstruction, or absent CFD radiation are current blockers. |

## Math / Theory / Assumptions To Carry Forward

- Predictive model contract: setup inputs only go into the run; CFD mdot,
  realized CFD wallHeatFlux, and validation/holdout temperatures are target
  data, not runtime inputs.
- Thermal closure contract: positive wallHeatFlux/segment duty heats the fluid;
  internal Nu/HTC/UA cannot absorb heater realization, cooler/HX duty, passive
  wall loss, radiation, storage, junction, or recirculation residuals.
- Radiation contract: current CFD `rcExternalTemperature` wallHeatFlux already
  includes radiation; do not add a separate radiation term when replaying
  realized wallHeatFlux.
- Boundary-model contract: heater realized fraction, cooler/HX removal, passive
  wall/external convection, and radiation semantics are separate lanes; realized
  CFD heater/test-section wallHeatFlux is diagnostic-only for setup-only forward
  runs.
- Split discipline: keep `salt_2=train`, `salt_3=validation`, and
  `salt_4=holdout` unless a later dated gate supersedes the split.
- Upcomer theory boundary: observed recirculation points support a blocked
  onset-data statement, not a calibrated regime-switch threshold.

## Remaining Blockers For The Slide

Use the current blocker set, not the stale list:

- `closure-qoi-mesh-gci`: zero publication-ready GCI rows.
- `thermal-cfd-1d-parity`: no fit-admissible internal-Nu rows.
- `predictive-heater-cooler-wall-submodels`: setup-only heater/HX/wall/radiation
  submodels are not admitted.
- `upcomer-onset-data-sparsity`: onset remains extrapolated from low-Re
  recirculation evidence.
- `fluid-external-boundary-api-gap`: localized fixed-K exists, but first-class
  external boundary/HX/wall dictionaries are not final.
- `f6-friction-re-correction`: F6 is a candidate screen without held-out or
  mesh/GCI-backed validation.

## Next Meeting Story

Show progress as disciplined narrowing:

1. The project has moved from "can we run and extract enough evidence?" to
   "which admitted gates can support claims?"
2. Thermal evidence is cleaner operationally, but the admission result is a
   no-fit decision, which protects the thesis from overclaiming Nu/UA.
3. Hydraulics has a promising localized-loss direction, but current H1/F6
   evidence is still diagnostic or screen-level until calibrated/held-out gates
   land.
4. Boundary/HX/wall/radiation modeling is now well separated by theory, but the
   setup-only predictive implementation remains the next model-building task;
   the first proposed task is `BCM-HEATER-FRACTION-V1`.
5. Corrected-Q remains live/non-terminal; it should appear as an awaited gate,
   not as admitted sensitivity evidence.

## Watchlist / Update Cadence

- Update this story only when an admission, blocker, scorecard, or claim status
  changes.
- AGENT-328 localized fixed-K forward score and AGENT-330 upcomer
  recirculation/internal-Nu admissibility are in flight; consume them only after
  their status/work products land.
- Use the AGENT-325 table-update cadence contract for daily and gate-triggered
  refreshes of blocker, admission, scorecard, and thesis-facing tables.
