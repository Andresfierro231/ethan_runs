---
task: TODO-LITREV-FINAL-RELEASE-TASK-DISPATCH-2026-07-22
date: 2026-07-22
role: Coordinator
type: handoff
status: current
tags: [litrev, predictive-1d, model-admission, thesis]
related:
  - .agent/BOARD.md
  - operational_notes/maps/forward-predictive-model.md
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/UNRESOLVED_CLAIMS.md
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/audit_outputs/final_release/README.md
---
# LitRev Final Release Task Dispatch

## Why This Exists

The new LitRev final release is not just a prose report. Its controlling
machine-readable evidence layer is:

`../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/audit_outputs/final_release/`

The final release preserves UC-01 through UC-08 as unresolved TAMU-dependent
model-admission inputs. The near-term path is therefore not to paste more
correlations into the 1D model. It is to convert source envelopes, model-form
admission cards, boundary-condition rules, pressure/energy accounting, and
reverse-flow taxonomy into executable gates.

## Files To Open First

- `../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/UNRESOLVED_CLAIMS.md`
- `../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/reports/HITEC_FINAL_RELEASE_RED_TEAM_QA.md`
- `../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/notes/HITEC_PROMPT7_MODELING_DISCOVERIES_AND_NEXT_STEPS.md`
- `../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/audit_outputs/final_release/HITEC_final_source_validity_envelope.csv`
- `../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/audit_outputs/final_release/HITEC_final_model_form_hierarchy.csv`
- `../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/audit_outputs/final_release/HITEC_final_pressure_energy_accounting_rules.csv`
- `../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/audit_outputs/final_release/HITEC_final_reverse_flow_taxonomy.csv`

LitRev repo commit observed for this dispatch: `a0b1205`.

## Lessons To Incorporate

1. The strongest defensible near-term model is MF-01: a gated, segmentwise,
   single-stream developing-flow network with explicit reset history, property
   guards, source-status labels, pressure basis, and thermal boundary class.
2. Fully developed laminar friction and fixed Nusselt values are reference
   limits or diagnostics, not automatic active closures.
3. Source validity must be decided case-by-segment. The required groups are
   `Re`, `Pr`, `Gr`, `Gr_star`, `Ri`, `Ra`, `Bo`, `Gz`, `L/D_h`, and reset
   distances, plus geometry, property package, and boundary-condition class.
4. Property selection is a model-form gate. Viscosity is high leverage; cp and k
   remain sensitivity lanes unless final TAMU salt state and temperature
   envelope evidence admit one package.
5. Reverse flow is not one phenomenon. Local wall reversal, core-wall
   counterflow, localized recirculation, negative branch flow, and exchange
   flow need separate labels before any switching calibration.
6. Pressure and minor-loss results must carry static/total/reduced-static
   pressure basis, velocity basis, recovery-plane definition, straight-loss
   subtraction, hydrostatic/kinetic corrections, and section/cluster/component
   naming.
7. Thermal fitting must not let internal Nu absorb heater efficiency, passive
   loss, jacket removal, radiation, insulation/contact resistance, wall
   conduction, storage, or residual heat loss.
8. CFD-derived `wallHeatFlux`, validation temperatures, and CFD mdot are not
   predictive runtime inputs. CFD should instead produce the same observables
   the 1D model consumes for diagnostics, gate calibration, and held-out
   validation.
9. ROM remains deferred until a trustworthy full-order model, snapshots,
   parameter space, basis construction, stabilization, and held-out validation
   exist.
10. Negative and fail-closed results are useful thesis evidence when they show
    why source envelopes, runtime legality, or freeze gates block overclaim.

## Board Rows Added

- `TODO-LITREV-FINAL-CASE-BY-SEGMENT-ADMISSION-ENGINE-2026-07-22`
- `TODO-LITREV-FINAL-UC01-UC08-THESIS-GAP-CROSSWALK-2026-07-22`
- `TODO-1D-FINAL-PROPERTY-PACKAGE-SELECTION-GATE-2026-07-22`
- `TODO-1D-FINAL-REVERSE-FLOW-SWITCHING-CALIBRATION-DESIGN-2026-07-22`
- `TODO-1D-FINAL-PRESSURE-ENERGY-BASIS-AND-BC-EQUIVALENCE-CONTRACT-2026-07-22`
- `TODO-1D-FINAL-HEAT-LOSS-POWER-PARTITION-CALIBRATION-DESIGN-2026-07-22`
- `TODO-THESIS-LITREV-FINAL-RELEASE-EVIDENCE-PACKET-FOR-CSEM-WRITER-2026-07-22`

## Suggested Sequence

1. Run the UC-01..UC-08 thesis gap crosswalk so the paper writer and
   coordinator can see which narrative claims are ready, partial, or blocked.
2. Build the case-by-segment admission engine. This is the highest-value code
   task because it turns the LitRev into executable model-selection logic.
3. Use the property-package gate to freeze or explicitly defer the property
   lane before interpreting friction, heat transfer, buoyancy, or heat-loss
   residuals.
4. Publish the pressure/energy/boundary-condition contract before any component
   K, section K, or Nu release.
5. Design reverse-flow switching calibration after exact same-label S13 fields
   or equivalent topology labels exist.
6. Design heat-loss and power-partition calibration before any internal-Nu
   tuning.
7. Build the CSEM writer evidence packet after the crosswalk and, ideally, the
   admission-engine package exist.

## Do Not Do

- Do not mutate native CFD/OpenFOAM outputs.
- Do not change registry/admission state from these rows.
- Do not launch scheduler jobs unless a later row explicitly claims that action.
- Do not edit Fluid or external repos from these coordination rows.
- Do not edit thesis body/LaTeX prose from this repo.
- Do not admit `K`, `f_D`, `Nu`, source/property rows, Qwall, or final score
  values from literature evidence alone.
- Do not use CFD mdot, realized CFD `wallHeatFlux`, imposed cooler duty,
  realized test-section heat, validation temperatures, holdout temperatures, or
  external-test temperatures as predictive runtime inputs.

