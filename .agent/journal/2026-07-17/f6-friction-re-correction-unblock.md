---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock/README.md
  - tools/analyze/build_f6_friction_re_correction_unblock.py
  - tools/analyze/test_f6_friction_re_correction_unblock.py
tags: [f6, friction, recirculation, blocker]
related:
  - .agent/status/2026-07-17_AGENT-487.md
  - imports/2026-07-17_f6_friction_re_correction_unblock.json
task: AGENT-487
date: 2026-07-17
role: Hydraulics/Implementer/Tester/Writer
type: journal
status: complete
---
# F6 Friction/Re-Correction Unblock

## Files Inspected

- `.agent/BOARD.md`
- `.agent/blockers.yml`
- `work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/f6_onset_scorecard.csv`
- `work_products/2026-07/2026-07-16/2026-07-16_f6_upcomer_blocker_status_scorecard/README.md`
- `work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/README.md`
- `work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design/README.md`

## Files Changed

- `.agent/BOARD.md`
- `.agent/blockers.yml`
- `.agent/status/2026-07-17_AGENT-487.md`
- `.agent/journal/2026-07-17/f6-friction-re-correction-unblock.md`
- `imports/2026-07-17_f6_friction_re_correction_unblock.json`
- `tools/analyze/build_f6_friction_re_correction_unblock.py`
- `tools/analyze/test_f6_friction_re_correction_unblock.py`
- `work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock/**`

## Results

The package keeps `f6-friction-re-correction` open but removes ambiguity about
what remains. All 12 current PM5 rows are material-recirculation diagnostics.
There are no ordinary F6 candidates and no scoreable recirculation-modeled
F6/onset rows. `F3_shah_apparent` remains the production closure.

The narrowed extraction/admission queue is:

- non-recirculating pressure anchors;
- hybrid pressure-residual movement against `F3_shah_apparent`;
- same-window wall-core or wall-bulk Delta T, Gz, RAF/RMF/SVF, and pressure metrics;
- mesh/time uncertainty;
- Salt3 Q x insulation anchors after jobs `3299610` and `3299620` are harvestable.

## Commands Run

- `python3 tools/analyze/test_f6_friction_re_correction_unblock.py`
- `python3 tools/analyze/build_f6_friction_re_correction_unblock.py`
- `python3 tools/docs/build_repo_index.py --check`

## Incomplete Lines

Generated index refresh is intentionally pending. Active `AGENT-482` owns the
generated docs index files, so this task did not write `.agent/BLOCKERS.md`,
`.agent/STATE.md`, `.agent/catalog.json`, or `.agent/catalog.csv`.
