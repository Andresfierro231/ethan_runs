# Minor Loss Two-Tap

Date: `2026-07-08`
Agent role: Implementer / Tester
Task ID: `TODO-MINOR-LOSS-TWO-TAP`
Worktree: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs`

## Files Inspected

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `tools/AGENTS.override.md`
- `staging/AGENTS.override.md`
- `operational_notes/06-26/25/2026-06-25_ethan_corner_pressure_drop_math.md`
- `tools/extract/sample_bend_minor_loss.py`
- `tools/extract/sample_feature_minor_loss_budget.py`
- `tools/analyze/summarize_corner_pressure_drops.py`
- `tools/analyze/build_pressure_term_ledger.py`
- `tools/case_analysis_profiles.py`
- `work_products/2026-07-01_claude_bend_minor_loss/bend_minor_loss_viscosity_screening_salt_test_2_jin_coarse_mesh.csv`
- `work_products/2026-07-01_claude_bend_minor_loss/bend_minor_loss_viscosity_screening_salt_test_3_jin_coarse_mesh.csv`
- `work_products/2026-07-01_claude_bend_minor_loss/bend_minor_loss_viscosity_screening_salt_test_4_jin_coarse_mesh.csv`
- `work_products/2026-07-01_claude_bend_minor_loss/bend_minor_loss_viscosity_screening_salt_test_2_jin_coarse_mesh.json`
- `work_products/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv`
- `work_products/2026-07-08_pressure_term_ledger/README.md`
- `work_products/2026-07-08_pressure_term_ledger/summary.json`

## Files Changed

- `.agent/BOARD.md`
- `.agent/status/2026-07-08_TODO-MINOR-LOSS-TWO-TAP.md`
- `.agent/journal/2026-07-08/minor-loss-two-tap.md`
- `tools/extract/sample_minor_loss_two_tap.py`
- `tools/extract/test_sample_minor_loss_two_tap.py`
- `work_products/2026-07-08_minor_loss_two_tap/README.md`
- `work_products/2026-07-08_minor_loss_two_tap/minor_loss_two_tap.csv`
- `work_products/2026-07-08_minor_loss_two_tap/minor_loss_two_tap.json`
- `work_products/2026-07-08_minor_loss_two_tap/summary.json`

## Commands Run

- `sed -n '72,82p' .agent/BOARD.md`
- `sed -n '1,220p' tools/AGENTS.override.md`
- `sed -n '1,220p' staging/AGENTS.override.md`
- `rg --files tools/extract tools/analyze work_products | rg '(minor_loss|bend|feature|corner|pressure_term_ledger|section_mean_pressure)'`
- `sed -n '1,240p' operational_notes/06-26/25/2026-06-25_ethan_corner_pressure_drop_math.md`
- `sed -n '1,260p' tools/extract/sample_bend_minor_loss.py`
- `sed -n '1,260p' tools/extract/sample_feature_minor_loss_budget.py`
- `sed -n '1,260p' tools/analyze/summarize_corner_pressure_drops.py`
- `head -5 work_products/2026-07-01_claude_bend_minor_loss/bend_minor_loss_viscosity_screening_salt_test_2_jin_coarse_mesh.csv`
- `head -5 work_products/2026-07-01_claude_bend_minor_loss/bend_minor_loss_viscosity_screening_salt_test_3_jin_coarse_mesh.csv`
- `head -5 work_products/2026-07-01_claude_bend_minor_loss/bend_minor_loss_viscosity_screening_salt_test_4_jin_coarse_mesh.csv`
- `sed -n '520,590p' tools/case_analysis_profiles.py`
- `sed -n '240,320p' tools/analyze/build_pressure_term_ledger.py`
- `python -m pytest tools/extract/test_sample_minor_loss_two_tap.py -q`
- `python -m py_compile tools/extract/sample_minor_loss_two_tap.py tools/extract/test_sample_minor_loss_two_tap.py`
- `python tools/extract/sample_minor_loss_two_tap.py`
- `find work_products/2026-07-08_minor_loss_two_tap -maxdepth 1 -type f -print | sort`
- `sed -n '1,240p' work_products/2026-07-08_minor_loss_two_tap/README.md`
- `head -20 work_products/2026-07-08_minor_loss_two_tap/minor_loss_two_tap.csv`
- `python -m json.tool work_products/2026-07-08_minor_loss_two_tap/summary.json`

## Results

Built `work_products/2026-07-08_minor_loss_two_tap/` from preserved evidence
only. No new OpenFOAM extraction was run.

Output counts:

- `15` rows total: `3` Salt cases × `5` expected features.
- `12` computed preserved corner rows.
- `3` unavailable `test_section_complex` rows flagged for raw extraction.
- `K_apparent` range: `6.2247` to `16.5038`.
- `K_local` range after minimum adjacent straight-loss subtraction: `1.0661`
  to `8.7476`.

Validation:

- `python -m pytest tools/extract/test_sample_minor_loss_two_tap.py -q`:
  `5 passed`.
- `python -m py_compile tools/extract/sample_minor_loss_two_tap.py tools/extract/test_sample_minor_loss_two_tap.py`:
  passed.
- `python tools/extract/sample_minor_loss_two_tap.py`: generated the target
  package.

## Observed Facts

- The preserved July 1 bend/minor-loss CSVs contain four corner rows per Salt
  2/3/4 case.
- The case-analysis profile also defines `test_section_complex`, but that row is
  absent from the preserved July 1 bend/minor-loss CSVs.
- The preserved rows include feature total-pressure proxy loss, local dynamic
  pressure, buoyancy term, dynamic-head change, and `dz_across_feature_m`.
- The preserved rows do not include a full centerline tap-to-tap feature length.
- The July 8 pressure ledger supplies adjacent distributed-loss gradients and
  recirculation flags.

## Inferred Interpretation

- Legacy `K_minor_loss` values are best treated as `K_apparent`: they reproduce
  a two-interface total-pressure proxy drop but do not subtract adjacent straight
  loss.
- `K_local` in this package is a stricter upper-bound estimate because it
  subtracts the available minimum straight-loss proxy, but the proxy length is
  `abs(dz)`, not a full centerline tap-to-tap length.
- Corner rows adjacent to recirculation spans remain validation diagnostics and
  should not become ordinary single-stream minor-loss closure coefficients.

## Blockers / Work In Progress

- Full centerline tap-to-tap lengths are missing from preserved feature rows.
- `test_section_complex` / reducer-connector rows need raw two-tap extraction.
- Mesh/GCI uncertainty remains unavailable.
- Recirculation-adjacent features are not ordinary closure-fit rows.

## Recommended Next Action

Run a raw two-tap feature extraction that emits centerline tap-to-tap length and
includes `test_section_complex` plus reducer/junction taps. Then refresh the
pressure ledger minor-loss column from this package's `K_local` / `local_minor_loss_pa`
instead of the legacy apparent K values.

## Analysis Classification

- Independent total-pressure ledger: 3D CFD postprocessing / bridge table. It
  should feed 1D validation but is not a 1D solver task.
- Two-tap minor-loss extraction: 3D CFD postprocessing.
- Station-resolved development analysis: 3D CFD postprocessing, with 1D closure
  model-form implications.
- Recirculation invalidity quantification: 3D CFD postprocessing / regime
  classification.
- Uncertainty package: mixed bridge layer. Mesh, time-window, station-placement,
  and pressure-averaging uncertainty are 3D/postprocessing; model-form
  uncertainty is 1D/closure-bakeoff.
- Loop-level closure audit: bridge layer. It sums 3D-derived terms in the form
  needed to challenge or validate the 1D model.
