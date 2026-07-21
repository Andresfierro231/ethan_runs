# AGENT-155 Raw Notes

Date: `2026-06-30`
Role: `Implementer / Coordinator`
Task ID: `AGENT-155`

## Scope

- `.agent/BOARD.md`
- `.agent/status/2026-06-30_AGENT-155.md`
- `.agent/journal/2026-06-30/implementer-latest-window-salt4-failure-repair.md`
- `tools/extract/sample_leg_centerline_major_loss.py`
- `tmp/2026-06-23_ethan_latest_window_case_analysis_refresh/**`
- `tmp_extract/ethan_streamwise_friction/viscosity_screening_salt_test_4_jin_coarse_mesh/**`
- `journals/2026-06/2026-06-30_ethan_runs.md`

## Observed starting point

- Salt 4 full output root stalled after major-loss extraction.
- The cached streamwise-friction extract root
  `tmp_extract/ethan_streamwise_friction/viscosity_screening_salt_test_4_jin_coarse_mesh/ad9ca25a2259410c`
  had partial boundary-layer outputs and still contained `-nan` lines in
  retained `T` files at least at `8110`, `8111`, and `8123`.
- `sample_leg_centerline_major_loss.py` was skipping re-sanitization whenever
  `thermal_sanitization_summary.json` already existed for the same selected
  time list, even if the cached reconstructed fields were later stale or
  reintroduced invalid tokens.

## Actions taken

- Removed the stale early-return path in
  `sanitize_reconstructed_thermal_fields` so the extractor always rescans the
  selected retained `T` fields and rewrites
  `thermal_sanitization_summary.json`.
- Verified the code change with:
  - `python -m py_compile tools/extract/sample_leg_centerline_major_loss.py`
- Quarantined the stale cache root:
  - from
    `tmp_extract/ethan_streamwise_friction/viscosity_screening_salt_test_4_jin_coarse_mesh/ad9ca25a2259410c`
  - to
    `tmp_extract/ethan_streamwise_friction/viscosity_screening_salt_test_4_jin_coarse_mesh/ad9ca25a2259410c_stale_20260630T100000`
- Rebuilt Salt 4 locally far enough to confirm the repaired cache was fresh:
  - new `thermal_sanitization_summary.json` was generated at
    `2026-06-30T11:01:45-05:00`
  - replacement counts now include the formerly bad retained times
    `8110`, `8111`, and `8123`
- Observed the resumed OpenFOAM thermal post-processing advance through
  retained times `8104`, `8105`, and `8106` without reproducing the prior
  fatal `T`-field read.
- Stopped the local validation process tree before completion so the repaired
  queue resubmission could reuse the same Salt 4 cache without concurrent
  writes.
- Handed the repaired state back to AGENT-154, which submitted the new chain
  beginning with `3267436` `lw_s234_full`.

## Current handoff state

- The root cause is fixed in code and the stale Salt 4 cache has been
  quarantined.
- Full queued rebuild is now delegated to `3267436` rather than the canceled
  local validation run.
