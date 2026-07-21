---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_3d_1d_heat_loss_alignment/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_3d_1d_heat_loss_alignment/heat_loss_alignment_by_segment.csv
  - work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_salt_forward_v1_unblock/salt_training_fit_input_table.csv
  - work_products/2026-07/2026-07-15/2026-07-15_diagnostic_cfd_heat_loss_replay_and_predictive_loss_plan/README.md
tags: [thermal-parity, heat-loss, diagnostic-replay, validation-split, val-salt2, thesis-source]
related:
  - reports/thesis_dossier/2026-07-15_powerpoint_outline.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
task: AGENT-410
date: 2026-07-15
role: Forward-pred/Thermal parity/Writer/Implementer/Tester
type: journal
status: complete
---
# Diagnostic CFD Heat-Loss Replay And Predictive Loss Plan

## Why This Exists

The user asked to include a diagnostic run where the 1D model forces heat losses
into the exact CFD-realized locations, to evaluate whether Salt1-4 can train a
heat-loss model tested on other CFD runs or `val_salt2`, and to plan a
setup-predictive variant that uses junction/stub coverage, wall/shell drive,
external boundary metadata, and setup-only HX/cooler behavior.

## What Was Done

I created a reproducible builder:

- `tools/analyze/build_diagnostic_cfd_heat_loss_replay_and_predictive_loss_plan.py`

and focused tests:

- `tools/analyze/test_diagnostic_cfd_heat_loss_replay_and_predictive_loss_plan.py`

The builder reads existing packages only. It filters AGENT-350
`heat_loss_alignment_by_segment.csv` to `path_id=B2_realized_wallflux_roles`,
then writes a report-ready addendum package under:

- `work_products/2026-07/2026-07-15/2026-07-15_diagnostic_cfd_heat_loss_replay_and_predictive_loss_plan/`

I also added the forced-CFD replay and setup-predictive implementation plan to
`reports/thesis_dossier/2026-07-15_powerpoint_outline.md`.

## Findings

The forced-CFD realized replay already exists in the prior work as the
`B2_realized_wallflux_roles` lane. Extracted as its own addendum, it has:

- `15` forced replay rows.
- `3` Salt cases: Salt2, Salt3, Salt4.
- `5` segments per case: lower leg, upcomer, cooling branch, downcomer, and
  junction.
- `0 W` maximum segment net residual after forcing, by construction.

This is an important diagnostic but not a predictive model. It consumes realized
CFD `wallHeatFlux`, so it is a leakage/upper-bound style replay. Predictive
rows admitted from the forced replay: `0`.

For train/test sufficiency:

- A July 15 user-policy table supports Salt1/Salt4-family rows as training and
  Salt2 +/-5Q rows as holdout screening, with caveats.
- That split must not be mixed with the older Salt2 train / Salt3 validation /
  Salt4 holdout split.
- Other CFD runs are not currently a robust external heat-loss test set unless
  they have matched heat-loss ledgers, boundary contracts, and admission labels.

For `val_salt2`:

- A Jin Salt2 versus `val_salt_test_2_coarse_mesh` documentation package exists
  under AGENT-354.
- A current AGENT-350-style section heat-loss replay/admission package for
  `val_salt2` was not found in this task's scoped evidence.
- Therefore `val_salt2` is a good future test target, not a current thermal
  heat-loss holdout.

## Setup-Predictive Work Packets

The new `predictive_heat_loss_variant_plan.csv` defines seven packets:

1. Segment and patch data contract.
2. External circuit physics from h/Ta/Tsur/emissivity/layers.
3. Wall/shell temperature-drive model.
4. Setup-only HX/cooler model.
5. Heater and test-section source contract.
6. Declared split and validation gate.
7. `val_salt2` and external tests after thermal extraction/admission.

Each packet includes required inputs, outputs, a rigor gate, source paths, and a
runtime leakage guardrail.

## Validation

Passed:

```bash
python3.11 -m unittest tools.analyze.test_diagnostic_cfd_heat_loss_replay_and_predictive_loss_plan
python3.11 -m py_compile tools/analyze/build_diagnostic_cfd_heat_loss_replay_and_predictive_loss_plan.py tools/analyze/test_diagnostic_cfd_heat_loss_replay_and_predictive_loss_plan.py
```

## Guardrails

No native CFD solver outputs, scheduler state, registry/admission state, or
external `../cfd-modeling-tools` files were mutated. Realized CFD
`wallHeatFlux`, CFD `mdot`, imposed CFD cooler duty, and validation
temperatures remain forbidden runtime inputs for setup-only prediction.
