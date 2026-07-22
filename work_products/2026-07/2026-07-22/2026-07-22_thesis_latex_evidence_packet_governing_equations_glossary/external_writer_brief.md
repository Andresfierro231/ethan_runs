---
provenance:
  - governing_equation_ledger.csv
  - symbol_glossary.csv
  - sign_convention_ledger.csv
  - model_slot_admission_terms.csv
  - runtime_legality_ledger.csv
  - assumptions_caveats_ledger.csv
tags: [thesis, external-writer, governing-equations, glossary]
task: TODO-THESIS-LATEX-EVIDENCE-PACKET-GOVERNING-EQUATIONS-GLOSSARY-2026-07-22
date: 2026-07-22
status: current
---
# External Writer Brief: Governing Equations And Definitions

Use this packet as the controlled vocabulary for the thesis.

The most important rule: equations define the model architecture and evidence
slots, not admitted closures.  A term is admitted only when a separate
admission/source/property/uncertainty ledger says so.

Use these forms consistently:

- loop pressure root: buoyancy drive balances modeled losses;
- pressure loss sum: distributed `f_i` and local `K_i` are slots, not automatic
  component admissions;
- pressure decomposition: hydrostatic, kinetic, distributed/developing,
  section/cluster, transient, and residual terms stay separate;
- steady fluid energy balance: heater, cooler, wall loss, other source/sink,
  and residual lanes remain distinct;
- wall-loss resistance: name the drive temperature and every resistance owner;
- test-section balance: electrical deposition minus quartz/external loss, with
  either sign allowed;
- upcomer exchange variables: future contract only unless later S13/S15 gates
  admit them.

Forbidden shortcuts:

- using CFD mdot, realized wallHeatFlux, imposed cooler duty, validation
  temperatures, holdout rows, or external-test rows as predictive runtime
  inputs;
- saying a residual was fixed by internal Nu, component K, UA, or a global
  multiplier without a release gate;
- calling CFD evidence experimental validation;
- treating SAM relevance as SAM validation.
