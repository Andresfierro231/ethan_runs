---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/cfd_postprocessing_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/model_form_candidates.csv
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - work_products/2026-07/2026-07-16/2026-07-16_thermal_parity_resolution_gate/residual_owner_resolution_gate.csv
  - work_products/2026-07/2026-07-17/2026-07-17_predict_segment_thermal_models/thermal_model_slot_admission.csv
tags: [litrev-synthesis, thermal-modeling, heat-loss, fluid-walls, external-boundary, internal-nu]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/README.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
task: TODO-LITREV-THERMAL-HEAT-LOSS-CONTRACT-ALIGNMENT
date: 2026-07-21
role: Thermal-modeling/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# LitRev Thermal Heat-Loss Contract Alignment

## Decision

The LitRev heat-transfer extraction contract aligns with the current predictive
`fluid+walls` model only if heat paths remain separate runtime and scoring
lanes. Internal `Nu` is restricted to salt-side convection and thermal
development. It may not absorb heater/source mismatch, wall/layer conduction,
insulation or quartz losses, external convection, radiation, cooler/jacket
removal, wall storage, recirculation/mixing, or the final heat residual.

This package is a contract-only alignment. It does not admit new coefficients,
does not edit Fluid, and does not mutate CFD outputs.

## LitRev Rows Used

The controlling CFD contract rows from
`cfd_postprocessing_contract.csv` are:

| Row | Quantity | Contract implication |
| --- | --- | --- |
| `CFD-13` | `enthalpy_bulk_temperature` | Bulk temperature must be enthalpy-weighted or the averaging simplification must be recorded before heat-transfer comparisons. |
| `CFD-14` | `wall_heat_transfer` | Wall area, wall heat flux, wall temperature, `h_internal`, and `Nu_internal` are outputs with averaging basis; they become section-effective when stratification or recirculation is large. |
| `CFD-15` | `heat_loss_network_terms` | Heater, jacket/cooler, passive, storage, radiation, wall, and residual terms stay separate; residual cannot be absorbed into internal `Nu`. |

MF-01 supplies the gated single-stream branch path: ordinary branch `Nu`
requires stable signed throughflow and source-envelope fields. MF-04 supplies
the escalation path when local reverse mass/area invalidates one bulk state:
throughflow plus a recirculation/exchange-cell energy ledger.

## Contract Table

The machine-readable version is `heat_loss_path_contract.csv`.

| Heat Path | Runtime Inputs | Forbidden Inputs | Outputs | Current Blocker |
| --- | --- | --- | --- | --- |
| Heater/source to fluid | Setup heater power, declared source distribution, optional admitted training scalar, geometry, property lane. | Realized CFD heater `wallHeatFlux`, validation temperatures, CFD `mdot`, internal-Nu correction. | `Q_heater_to_fluid`, heater efficiency/source split, source residual. | Stronger physical source distribution still needs same-time solid/storage audit. |
| Internal `Nu` | Geometry, Re, Pr, Gz, admitted drive temperature, source-envelope Nu form, solved local fluid state. | Any external heat residual, passive loss, radiation, heater/cooler error, storage, recirculation residual, CFD `wallHeatFlux` at runtime. | `h_internal`, `Nu_internal`, internal convective resistance, development flag. | `0` fit-admissible rows; sign/heat-balance, recirculation, and same-QOI mesh/GCI gates remain open. |
| Wall conduction | Wall material, dimensions, `k_wall`, area/perimeter, solved wall state. | Multipliers that absorb boundary/storage residuals, realized CFD `wallHeatFlux`, validation wall temperatures. | Wall conduction resistance and wall temperature drop. | Segment-local wall ownership and coupled validation incomplete; wall-circuit candidates fail validation/holdout gates. |
| Contact/layer resistance | Declared layer/contact resistance, layer thickness, `k_layer`, area, setup layer metadata. | Back-solving from held-out residuals, folding contact into `Nu`, validation temperatures. | Contact/layer resistance and layer temperature drop. | Contact/local layer ownership is not independently isolated by segment. |
| Insulation/quartz | Insulation/quartz geometry and properties, exposed area, drive selector, external BC setup fields. | Realized test-section `wallHeatFlux`, validation/holdout temperatures, legacy `37 W` source as passive loss, residual fitted into `Nu`. | Insulation/quartz resistance, test-section net heat sign. | Test-section passive-loss candidates remain not admitted under `predictive-wall-test-section-submodels`. |
| External convection | `h_ext`, `Ta`, area, drive selector, segment/patch role, coverage. | Realized CFD `wallHeatFlux` at runtime, validation temperatures, hidden residual multipliers, extra radiation during replay. | External-convection heat loss and resistance. | First-class external BC dictionary bridge remains `TODO-FLUID-EXTERNAL-BC-DICT`; segment wall scoring incomplete. |
| Radiation | Predictive mode: emissivity, `Tsur`, area, solved surface temperature, admitted view-factor assumption. | Adding radiation on top of realized CFD `wallHeatFlux`, claiming radiation absent, fitting radiation into `Nu`, using `qr` when no `qr` exists. | Separate radiation heat rate or linearized `h_rad` in predictive mode; sensitivity labels. | `TODO-1D-RADIATION-CAPABILITY` remains open; CFD has embedded radiation but no exported separate `qr`. |
| Jacket/cooler removal | Setup cooler/HX geometry, coolant/air inlet conditions, admitted UA/effectiveness candidate, property lane. | Imposed CFD cooler duty or realized cooler `wallHeatFlux` as predictive input, internal-Nu correction, validation temperatures. | Cooler/jacket heat removal, UA/effectiveness, cooler residual. | Current setup-only scalar cooler/HX lane is admitted; broader distributed/coupled review remains open. |
| Storage | None in present steady model; future transient lane would need heat capacity, volume, wall-temperature derivative, time metadata. | Tuning steady fit with storage, erasing storage via `Nu`, unlogged time drift. | `Q_storage` or `dE_wall/dt` only in a future transient/ROM lane. | Steady `fluid+walls` scope excludes storage; same-time solid-energy audit not admitted. |
| Residual | No runtime closure input; only residual tolerance and owner labels. | Fitted residual heat path, residual hidden in `Nu`, validation heat target at runtime. | `Q_residual`, residual fraction, owner candidate, blocker, next extraction need. | Segment residuals remain; junctions unbracketed, upcomer recirculating, test-section passive loss not admitted. |

## Alignment With Predictive External Boundary

The external-boundary runtime dictionary should carry setup fields such as `h`,
`Ta`, `Tsur`, emissivity, wall/layer resistance, segment or patch role, area,
coverage, and drive-temperature selector. Those fields can feed passive wall,
quartz/test-section, and radiation-capable predictive terms. Realized CFD
`wallHeatFlux` remains a diagnostic/scoring output, never a predictive input.

Replay semantics differ from predictive semantics:

- CFD replay with realized `wallHeatFlux`: do not add separate convection or
  radiation terms on top of it.
- Predictive `fluid+walls`: compute heat paths from setup fields and solved
  wall/fluid states, then compare resulting heat rates and temperatures to CFD.

## Current Blocker Summary

- Internal `Nu`: closed to fitting; diagnostic only.
- Test-section passive loss: not admitted.
- Radiation: active in CFD boundary metadata but inseparable in current
  `wallHeatFlux`; separate 1D radiation capability is still a TODO.
- External BC dictionary: implementation row remains open for first-class
  segment/patch dictionaries.
- Residuals: remain diagnostic owner labels, not closures.

## Files

- `heat_loss_path_contract.csv`
- `heat_loss_path_contract.json`
- `source_manifest.csv`
- `summary.json`

No solver outputs, registry state, scheduler state, Fluid source, or admission
state were changed.
