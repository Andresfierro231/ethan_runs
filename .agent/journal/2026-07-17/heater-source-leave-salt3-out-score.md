---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_heater_source_leave_salt3_out_score/
  - logs/2026-07-17/heater_source_leave_salt3_out_score.out
  - logs/2026-07-17/heater_source_leave_salt3_out_score_diag.out
tags: [forward-model, heater-source, validation-split, salt3-holdout]
related:
  - .agent/status/2026-07-17_AGENT-529.md
  - imports/2026-07-17_heater_source_leave_salt3_out_score.json
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-529
date: 2026-07-17
role: Thermal-modeling/Forward-pred/Implementer/Tester/Writer
type: journal
status: complete
---
# Heater Source Leave-Salt3-Out Score

## Why This Exists

AGENT-511 trained the heater-source redistribution lambda on Salt2 only. The
user asked why we did not train on Salt1/Salt2/Salt4 and test on Salt3 plus
perturbation/external rows. AGENT-529 implements that split-corrected screen.

## What Ran

The executable lane is `HS1_BASELINE_LOSO_SALT124`: Fluid default predictive
outer/wall setup, frozen constant-UA cooler from AGENT-482, and one heater-source
lambda spanning the TW4-to-TP3 source redistribution family. The PB2 wall lane is
represented but blocked because Salt1 external-boundary role rows are missing.

Two Slurm jobs ran:

- `3301102`: full `21 x 3` train grid over Salt1/Salt2/Salt4, completed
  `63/63` rows.
- `3301155`: reused the train grid and appended four selected nominal diagnostic
  rows, completing `67/67` total rows.

## Observed Output

Strict selection requires accepted roots for Salt1/Salt2/Salt4. Salt1 and Salt2
are accepted, but all Salt4 train-grid rows are `root_status=rejected`, so no
admitted lambda can be selected.

For diagnostic continuity only, the finite-row objective selected `lambda=1.0`.
Salt3 then failed vs M3 by all gates: mdot, TP, TW, and all-probe RMSE.

## Inference

The corrected split does not rescue heater-source redistribution. The dominant
failure is not just where the setup heater source is placed: Salt4 root rejection
blocks strict training, and Salt3 diagnostic temperature errors are much worse
than M3. The remaining scientific path is wall/test-section coupling and
executable blind-row adapters, not another heater-source-only lambda scan.

## Guardrails Preserved

- No Salt3 fitting or model selection.
- No Salt2 +/-5Q or `val_salt2` fitting or model selection.
- No native solver output mutation.
- No registry/admission mutation.
- No external Fluid source edit.
- Diagnostic finite-root selection is labeled non-admissible.

## Next Task Sequence

1. Diagnose why Salt4 is rejected under the executable baseline Fluid lane.
2. Generate or promote Salt1 external-boundary role rows so PB2 can run under the
   Salt1/Salt2/Salt4 training split.
3. Add executable score-only Fluid adapters for Salt2 +/-5Q and `val_salt2`.
4. Only after those pass, rerun strict admission with no diagnostic fallback.
