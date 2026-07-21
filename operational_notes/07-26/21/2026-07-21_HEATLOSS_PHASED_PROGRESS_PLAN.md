---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/heat_loss_path_contract.csv
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/forward-predictive-model.md
tags: [thermal-modeling, heat-loss, phased-plan, forward-predictive-model, fluid-walls]
related:
  - .agent/BOARD.md
  - .agent/status/2026-07-21_TODO-HEATLOSS-PHASED-PROGRESS-PLAN-2026-07-21.md
  - .agent/journal/2026-07-21/heatloss-phased-progress-plan.md
task: TODO-HEATLOSS-PHASED-PROGRESS-PLAN-2026-07-21
date: 2026-07-21
role: Coordinator/Writer
type: operational_note
status: complete
supersedes: []
superseded_by:
---
# Heat-Loss Phased Progress Plan

## Why This Avenue Exists

The July 21 heat-loss contract fixed the accounting language: heater/source,
internal `Nu`, wall conduction, contact/layer resistance, insulation/quartz,
external convection, radiation, jacket/cooler removal, storage, and residual
are separate lanes. The next risk is implementation drift: future work could
score another wall/test-section candidate without first making external
boundary dictionaries, radiation semantics, split heat evidence, source/property
labels, and runtime audits line up.

This plan turns the contract into a phased queue. It is meant to keep progress
fast by reusing existing TODO rows, but rigorous by forcing release gates between
phases.

## Open First

1. `work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/README.md`
2. `work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/heat_loss_path_contract.csv`
3. `reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md`
4. `operational_notes/maps/thermal-boundary-and-radiation.md`
5. `operational_notes/maps/thermal-closures-and-internal-nu.md`
6. `operational_notes/maps/forward-predictive-model.md`
7. `.agent/BOARD.md` rows named `TODO-HEATLOSS-PHASE-*`

## Trusted Packages

| Topic | Package |
| --- | --- |
| Heat-path contract | `work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/` |
| External boundary setup | `reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/` |
| Patchwise heat roles | `work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger/` |
| Physical-interface residuals | `work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/` |
| Thermal parity residual owners | `work_products/2026-07/2026-07-16/2026-07-16_thermal_parity_resolution_gate/` |
| Predictive boundary admission | `work_products/2026-07/2026-07-16/2026-07-16_predictive_boundary_submodel_admission/` |
| Segment thermal slots | `work_products/2026-07/2026-07-17/2026-07-17_predict_segment_thermal_models/` |
| Wall/test-section failures | `work_products/2026-07/2026-07-17/2026-07-17_wall_thermal_circuit_study/` |
| Upcomer exchange design | `work_products/2026-07/2026-07-21/2026-07-21_litrev_throughflow_recirc_exchange_cell/` |
| Source/property enforcement | `work_products/2026-07/2026-07-18/2026-07-18_source_property_label_enforcement/` |

## Active Board Rows

This coordination pass added:

- `TODO-HEATLOSS-PHASE-0-BASELINE-RELEASE-GATE`
- `TODO-HEATLOSS-PHASE-1-EXTERNAL-BC-RADIATION-INTEGRATION`
- `TODO-HEATLOSS-PHASE-2-SPLIT-HEAT-LOSS-EVIDENCE`
- `TODO-HEATLOSS-PHASE-3-WALL-TEST-SECTION-MODEL-SCORE`
- `TODO-HEATLOSS-PHASE-4-UPCOMER-EXCHANGE-AND-INTERNAL-NU-GATE`
- `TODO-HEATLOSS-PHASE-5-FROZEN-SCORECARD-AND-THESIS-HANDOFF`

Existing rows remain part of the execution path and should be claimed directly
when they are the sharper unit of work: `TODO-FLUID-EXTERNAL-BC-DICT`,
`TODO-1D-RADIATION-CAPABILITY`, `TODO-LITREV-SPLIT-JUNCTION-STORAGE-RADIATION-EXTRACTION`,
`TODO-PREDICT-WALL-THERMAL-CIRCUIT`,
`TODO-PREDICT-TEST-SECTION-HEAT-LOSS`,
`TODO-LITREV-MATCHED-PLANE-RECIRC-FIELD-HARVEST`,
`TODO-LITREV-GATED-SINGLE-STREAM-DEVELOPING-BRANCH`, and
`TODO-PRED-ENDTOEND-SCORE`.

## Phase Sequence

| Phase | Goal | Why it comes here | Acceptance signal |
| --- | --- | --- | --- |
| 0 | Freeze the baseline release gate. | Prevents later rows from scoring against stale or mismatched contracts. | Every heat path has current package, executable status, score/admission status, forbidden runtime fields, source/property status, and next dependency row. |
| 1 | Make external BC and radiation semantics executable. | Predictive heat loss needs setup dictionaries before wall/test-section candidates can be honest. | Runtime audit separates replay and predictive modes; radiation has analytic tests or an implementation handoff; no double counting with CFD `wallHeatFlux`. |
| 2 | Improve split heat-loss evidence. | Model candidates need better targets and residual ownership, especially junction/stub, storage proxy, and `qr` absence/presence. | Split heat-loss readiness table names each missing field and records absent `qr`/storage fields without inference. |
| 3 | Score narrow wall/test-section candidates. | Only after phases 1-2 can candidates use setup inputs and valid heat-path targets. | Candidate scorecard reports heat, mdot, TP, TW, all-probe, TW5/TW6, source/property labels, and runtime audit versus M3/prior candidates. |
| 4 | Decide upcomer exchange vs internal `Nu`. | Recirculation can masquerade as thermal residual; separate it before reopening any `Nu` fitting. | Exchange-cell readiness and ordinary single-stream reopening table; default remains `0` internal-Nu fit rows unless all gates pass. |
| 5 | Freeze final scorecard and thesis handoff. | Final claims require a runtime-legal candidate or a documented negative result. | Train/support/holdout/external scorecard with residual attribution by heat path and no held-out/external tuning. |

## Current Blockers

- `TODO-FLUID-EXTERNAL-BC-DICT`: first-class setup dictionaries still need an
  implementation/integration pass.
- `TODO-1D-RADIATION-CAPABILITY`: predictive radiation remains separate from CFD
  replay semantics.
- `predictive-wall-test-section-submodels`: wall/test-section candidates are not
  admitted.
- Upcomer recirculation/onset sparsity: ordinary single-stream upcomer `Nu`,
  `f_D`, and `K` remain invalid for current rows.
- Same-QOI uncertainty and source/property labels still gate admission language.

## Output Contract For Every Phase

Every phase package should include:

- `README.md` with observed facts, inferred interpretation, blockers, and next
  action.
- At least one machine-readable CSV contract or score table.
- `source_manifest.csv` or equivalent exact source-path table.
- Runtime-input audit naming allowed and forbidden inputs.
- Split-role labels for train/support/holdout/external rows when scoring.
- Explicit statement that realized CFD `wallHeatFlux`, CFD `mdot`, imposed CFD
  cooler duty, realized test-section heat, and validation temperatures are not
  predictive runtime inputs.

## Do-Not-Do Guardrails

- Do not hide heat residual in internal `Nu`.
- Do not add a separate radiation term on top of realized CFD `wallHeatFlux`.
- Do not infer `qr` or storage heat from an energy residual.
- Do not score wall/test-section candidates before external BC/radiation
  semantics and split heat evidence are release-gated.
- Do not use held-out or external-test rows for fitting or model selection.
- Do not launch solver or postprocessing work from a planning row.
- Do not change registry/admission state or blocker-register state from a
  writing/coordination row.
