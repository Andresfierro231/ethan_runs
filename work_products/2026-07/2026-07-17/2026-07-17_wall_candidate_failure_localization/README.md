---
provenance:
  created_by: AGENT-515
  created_utc: 2026-07-17T21:53:32.610998+00:00
  source_packages:
    - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_coupled_admission
    - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder
    - work_products/2026-07/2026-07-17/2026-07-17_corrected_split_final_predictive_scorecard
    - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_corrected_freeze_join_unblock
    - work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell
tags:
  - forward-predictive-model
  - wall-test-section
  - freeze-blocker
  - existing-evidence
related:
  - .agent/status/2026-07-17_AGENT-515.md
  - .agent/journal/2026-07-17/wall-candidate-failure-localization.md
  - imports/2026-07-17_wall_candidate_failure_localization.json
status: current
---

# Wall Candidate Failure Localization

This package explains why `freeze_blocked_no_wall_candidate_admitted` remains
blocked after the completed July 17 wall/test-section harvests. It is diagnostic
only: no solver, scheduler, Fluid, fitting, tuning, registry, or admission state
was changed.

## Main Finding

AGENT-498 produced `4` local distribution
candidates and `8` coupled rows. All four
candidates pass runtime legality, and every validation/holdout row improves
mdot versus M3. None can be admitted because all validation/holdout rows worsen
the aggregate temperature field, especially all-probe and TW errors.

The failure is therefore not "we forgot to freeze it" and not a runtime-input
leak. It is a physics/localization failure: heat is placed in the wrong 1D
roles/segments, and populated per-probe rows are available for held-out
sensor-level diagnosis of the aggregate regression.

## Files

- `wall_candidate_gate_failure_matrix.csv` - validation/holdout gate rows for
  the AGENT-498 candidates.
- `temperature_shape_regression_summary.csv` - PB1/PB2/PB3 shape-regression
  evidence, with data-limit notes where TP deltas are unavailable.
- `probe_localization_data_gap.csv` - explicit audit of per-probe localization
  export availability.
- `segment_heat_placement_failure_modes.csv` - role/segment heat-placement
  errors and failure-mode labels.
- `candidate_family_decision.csv` - PB1/PB2/PB3 family decisions and next
  action recommendations.
- `next_candidate_ladder.csv` - ordered next studies without duplicating active
  AGENT-511/513 work.
- `freeze_unblock_decision.csv` - corrected-freeze decision; currently blocked.
- `wall_candidate_gate_deltas.svg` and `segment_heat_placement_errors.svg` -
  quicklook plots.
- `runtime_leakage_audit.csv`, `source_manifest.csv`, and `summary.json` -
  provenance and guardrail checks.

## Scientific Interpretation

The pressure/flow side moves in the desired direction, but the thermal field
does not. That combination is typical of a model that has the right integrated
loss direction but the wrong source placement, drive temperature, axial exchange,
or junction ownership. The segment heat audit shows the strongest held-out
pattern: upcomer/test-section loss is underpredicted while junction and
downcomer roles absorb too much loss.

The defensible next move is to consume the completed wall-temperature-drive and
heater-source redistribution candidate packages together with the populated
per-probe residual exports for sensor-level diagnosis. The corrected freeze
should stay blocked until a wall/test-section candidate passes the predeclared
validation and holdout gates.
