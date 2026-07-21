---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/README.md
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/paper_methods_pressure_basis.md
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/paper_results_current_evidence.md
tags: [journal, pressure-ledger, two-tap, recirculation, paper-dossier]
related:
  - .agent/status/2026-07-20_TODO-TWO-TAP-RECIRC-SECTION-EFFECTIVE-MODEL.md
  - imports/2026-07-20_two_tap_recirc_section_effective_model.json
task: TODO-TWO-TAP-RECIRC-SECTION-EFFECTIVE-MODEL
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: journal
status: complete
---
# Two-Tap Recirculating Section-Effective Model

Task: `TODO-TWO-TAP-RECIRC-SECTION-EFFECTIVE-MODEL`

## Work Completed

Built a paper-facing package that answers why the current `corner_lower_right`
two-tap pressure rows are blocked and how to continue scientifically:

- ordinary `component_K` remains rejected for current rows;
- static apparent `K` is flagged as hydrostatic/buoyancy dominated;
- `p_rgh`/kinetic residual handling is defined for a section-effective lane;
- `RAF`, `RMF`, and `SVF` are carried as model features, not treated as noise;
- same-QOI mesh/time UQ requirements are written as a sampling contract;
- paper claim, limitation, artifact crosswalk, and figure/table manifest files
  are emitted for later manuscript drafting.

## Scientific Decision

Recirculation is expected and should be modeled. The correct next lane is not
ordinary component K from the current raw endpoint pairs, but a named
section-effective pressure residual:

```text
Delta_p_resid = Delta_p_rgh - Delta_p_kin - Delta_p_straight - Delta_p_dev
K_eff_recirc = Delta_p_resid / q_ref
```

The denominator `q_ref` must be same-window throughflow dynamic pressure; near
zero throughflow is a no-fit diagnostic state.

## Documentation Added

The thesis/paper layer now has
`13_two_tap_recirc_section_effective_pressure_model.md`, and the claim ledger
has CL-26 for the recirculating section-effective model contract. The pressure
map points future hydraulic work to the new package.

## Validation

- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/build_two_tap_recirc_section_effective_model.py`
- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/test_two_tap_recirc_section_effective_model.py`

Both passed before closeout.
