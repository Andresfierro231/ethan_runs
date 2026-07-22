---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_gate/hydraulic_fit_safety_gate.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_gate/forward_v0_hydraulic_residuals.csv
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/named_pressure_loss_table.csv
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/reset_distance_map.csv
tags: [predictive-model, hydraulics, pressure-evidence, mdot]
related:
  - .agent/journal/2026-07-13/predictive-hydraulic-correction-candidates.md
  - .agent/status/2026-07-13_AGENT-300.md
task: AGENT-300
date: 2026-07-13
role: Implementer/Reviewer/Writer
type: work_product
status: complete
---

# Predictive Hydraulic Correction Candidates

Task: `AGENT-300`

This package ranks low-dimensional hydraulic correction candidates from existing pressure evidence. It does not mutate native CFD outputs, does not edit external Fluid, and does not fit thermal UA/HTC/Nu parameters.

## Start Here

Why this exists: TODO-PRED-HYDRAULIC-GATE showed that forward-v0 pressure roots converge at low residual but overpredict `mdot` for every Salt row. That means thermal-looking improvements cannot be claimed until a hydraulic resistance path is tested.

Files to open first:

- `candidate_rankings.csv` for the ranked correction candidates.
- `mdot_resistance_scaling.csv` for the hydraulic-only resistance factor needed to move current forward-v0 `mdot` toward CFD `mdot`.
- `fit_safe_raw_pressure_rows.csv` for raw pressure-gradient rows admitted as fit-safe.
- `diagnostic_momentum_corrected_rows.csv` for debuoyed/profile diagnostic rows.
- `decision_summary.json` for machine-readable counts and the package decision.

Trusted packages: TODO-PRED-HYDRAULIC-GATE, AGENT-262 Salt2 pressure-only mesh-family comparison, and TODO-LITREV-RESET-NAMED-LOSSES.

Active board row: `AGENT-300`.

Next task sequence: implement the `H1` localized named-loss/reset bundle in a bounded forward hydraulic rerun, keep `H2` as a raw-fit-safe scalar screen, then rerun forward scoring before reopening thermal closure.

Output contract: raw pressure-gradient fit rows and momentum-corrected diagnostic rows are separate files and separate candidate lanes.

Do-not-do guardrails: no native solver mutation, no per-case thermal hacks, no thermal fitting, no global resistance multiplier as the exported correction.

## Decision

- Best next candidate: `H1_localized_named_loss_and_reset_bundle`.
- Mean resistance multiplier needed to hit CFD `mdot` under the simple hydraulic scaling check: `2.115`.
- Hydraulic-only mdot improvement is plausible because every forward-v0 row overpredicts `mdot`; increasing hydraulic resistance moves the root in the needed direction.
- This is not publication-ready closure: named losses are coarse/no-GCI, raw fit-safe evidence is limited to two spans, and a full forward rerun is still required.
- Thermal closure remains blocked.

## Outputs

- `candidate_rankings.csv`
- `mdot_resistance_scaling.csv`
- `fit_safe_raw_pressure_rows.csv`
- `diagnostic_momentum_corrected_rows.csv`
- `decision_summary.json`

## Reproduce

```bash
python3 tools/analyze/build_predictive_hydraulic_correction_candidates.py
python3 -m unittest tools.analyze.test_predictive_hydraulic_correction_candidates
```
