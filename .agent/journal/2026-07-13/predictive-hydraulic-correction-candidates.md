---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_gate/hydraulic_fit_safety_gate.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_gate/forward_v0_hydraulic_residuals.csv
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/named_pressure_loss_table.csv
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/reset_distance_map.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_correction_candidates/decision_summary.json
tags: [predictive-model, hydraulics, pressure-evidence, mdot]
related:
  - .agent/status/2026-07-13_AGENT-300.md
  - imports/2026-07-13_predictive_hydraulic_correction_candidates.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_correction_candidates/README.md
task: AGENT-300
date: 2026-07-13
role: Implementer/Reviewer/Writer
type: journal
status: complete
---

# Predictive Hydraulic Correction Candidates

Task: `AGENT-300`

Role: Implementer / Reviewer / Writer

## Context

TODO-PRED-HYDRAULIC-GATE already showed that forward-v0 pressure roots converge with small pressure residuals but overpredict CFD `mdot` for every Salt row. The AGENT-300 question was narrower: build and rank low-dimensional hydraulic correction candidates from fit-safe pressure evidence, and report whether `mdot` can improve without thermal fitting.

Inputs used:

- `work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_gate/`
- `work_products/2026-07/2026-07-13/2026-07-13_salt2_pressure_only_mesh_family_comparison/`
- `work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/`

No native CFD outputs, registry state, or external Fluid files were modified.

## Work

Added `tools/analyze/build_predictive_hydraulic_correction_candidates.py`, which emits:

- `fit_safe_raw_pressure_rows.csv`, restricted to raw pressure-gradient spans admitted by the hydraulic gate;
- `diagnostic_momentum_corrected_rows.csv`, explicitly marked as debuoyed/profile diagnostic evidence;
- `mdot_resistance_scaling.csv`, a hydraulic-only resistance-scaling check from current forward-v0 `mdot` to CFD `mdot`;
- `candidate_rankings.csv`, ranking low-dimensional candidate forms and rejecting thermal fitting/global masking where appropriate;
- `decision_summary.json` and package `README.md`.

Added `tools/analyze/test_predictive_hydraulic_correction_candidates.py` to verify lane separation, hydraulic-only scaling, candidate rank order, and thermal-fit exclusion.

## Observed Evidence

Raw pressure-gradient fit-safe rows:

- `left_lower_leg`
- `left_upper_leg`

Momentum-corrected diagnostic rows:

- `left_lower_leg`
- `left_upper_leg`
- `lower_leg`
- `right_leg`
- `test_section_span`
- `upper_leg`

Hydraulic-only scaling:

- Mean required resistance multiplier across all forward-v0 rows is `2.115`.
- `F0_current_fluid_sources` requires resistance multipliers from `2.277` to `2.449`.
- `F1_heater_only` requires resistance multipliers from `1.826` to `1.898`.
- Every row points in the same direction: increase hydraulic resistance to reduce `mdot` toward CFD.

Candidate ranking:

1. `H1_localized_named_loss_and_reset_bundle`: best next hydraulic rerun candidate. It uses localized named losses and reset/development sensitivity with raw fit-safe spans as guardrails.
2. `H2_fit_safe_raw_two_span_friction_scale`: one-scalar raw pressure-gradient screen; conservative but underinformed.
3. `H3_momentum_corrected_profile_scale`: diagnostic debuoyed/profile lane only.
4. `H4_global_loop_resistance_multiplier`: numerically useful as a math baseline but rejected as an exported correction because it hides localized losses.
5. `T0_thermal_parameter_fit`: blocked and rejected for this task.

## Interpretation

Mdot can plausibly improve without thermal fitting: the current forward-v0 roots are too high in `mdot`, and a hydraulic resistance increase moves the solution in the correct direction. The best next candidate is localized hydraulic resistance, not thermal adjustment and not a global loop multiplier.

This is not an admitted publication closure. Raw fit-safe pressure-gradient evidence is limited to two Salt2 spans, named-loss rows remain coarse/no-GCI, some K rows are upper bounds, and the candidate must be tested in a forward rerun. Thermal closure remains blocked.

## Validation

- `python3 -m py_compile tools/analyze/build_predictive_hydraulic_correction_candidates.py tools/analyze/test_predictive_hydraulic_correction_candidates.py`
- `python3 -m unittest tools.analyze.test_predictive_hydraulic_correction_candidates`
- `python3 tools/analyze/build_predictive_hydraulic_correction_candidates.py`

All completed successfully.
