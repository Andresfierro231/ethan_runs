# End-of-Day Handoff & TODO — 2026-07-10 (claude)

Wrap-up for the 2026-07-09 → 07-10 Claude session. Two tasks completed
(AGENT-234, AGENT-244). This note records what is done, what to document as TODO,
what is submittable, and prioritized next steps.

## Done this session

- **AGENT-234 — pressure decomposition figures.** Redesigned the two pressure
  figures (stacked mechanical-loss composition; paired buoyancy-drive-vs-
  resistance), fixing the AGENT-233 grouped-bar illegibility and the AGENT-207
  diverging-overlap/scale bugs. Added reusable `tools/analyze/svg_chart_kit.py`
  and `palette_validator.py`, full data disclosure, and an additive July 8
  presentation reference. Outputs:
  `work_products/2026-07/2026-07-09/2026-07-09_pressure_decomposition_figures/`.
- **AGENT-244 — postprocessor time-series & steady-state.** Parsed every Ethan
  run's `postProcessing` scalar series (52 dirs, 47 unique after de-dup), plotted
  grouped value-vs-time + last-300 s trend (equation + R² in legend) + CLT
  SEM-vs-averaging-time, and reported RMSE/variance/oscillation + steady-state
  verdicts + autocorrelation-corrected uncertainty. 417 SVGs, 2577 series.
  Outputs: `work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/`.
  Reusable: `openfoam_timeseries.py`, `timeseries_stats.py`,
  `svg_timeseries_chart.py`, `build_timeseries_steadystate_report.py`.

Status/journal/imports written for both; BOARD rows marked COMPLETE. 56 module
tests pass (37 figures/kit + 19 timeseries).

## Key results to carry forward

- mdot and fluid/wall temperatures are **steady in nearly all runs** (stationary,
  gently oscillating). Mainline Salt 2/3/4 mdot: autocorrelation-corrected
  relative uncertainty ~0.001–0.05 % of the mean.
- `total_Q` is the **net heat residual** (~0.1 W vs hundreds-of-W loop scale); its
  "not steady" verdicts are residual noisiness near a zero mean, not thermal
  runaway (handled with a scale-free drift_ratio).
- **salt3 corrected-Q hi5q / hi10q mdot is still drifting** (24 % / 45 % over the
  window) — independent corroboration of the corrected-Salt gate verdict
  "too short / needs extended continuation" (AGENT-237 review).

## Document as TODO (unclaimed; open a dated row when picked up)

1. **Integrate improved pressure figures into the July 8 package.** Update
   `build_postprocessor_summary_charts.py` (Codex AGENT-233 scope) to call
   `svg_chart_kit` and regenerate the pressure figures in place, and fix its stale
   `test_postprocessor_summary_charts.py` figure-count assertion. Needs Codex
   coordination (their owned paths).
2. **Time-series follow-ups (AGENT-244 extensions).**
   - Rerun with alternate windows (`--window-seconds`) if a different averaging
     horizon is wanted for the paper.
   - Add an **absolute** heat-vs-time series by aggregating per-patch
     `wallHeatFlux.dat` (heater/cooler groups), so thermal steadiness can be judged
     on absolute heat, not just the net residual.
   - Optionally fold the per-case steady-state verdict + relative SEM into the
     closure observation table as a data-quality flag.
3. **Corrected-Salt Q requalification** (see below) — extend continuations, then
   rerun the `3280969`-style inventory; do not admit any corrected-Q row until
   `operating_point_verdict = requalified`.

## What can be submitted (with decisions/blockers)

- **Git commit (small, safe once approved).** Only the new *tools + tests +
  status + journal + imports* are git-eligible — `work_products/*` is gitignored,
  so the 119 MB of SVGs are not committed (regenerable from scripts on scratch).
  The repo is shared and currently dirty (76 modified, 412 untracked across many
  agents), so any commit must be **staged narrowly** to this session's files.
  Decision needed: commit now, or leave for a coordinated repo-wide commit.
- **CFD jobs — corrected-Salt Q extended continuations.** The natural submittable
  compute work is extending the partial corrected-Q rows in
  `work_products/2026-07/2026-07-09/2026-07-09_corrected_salt_q_gate_3280969_review/resubmit_list.csv`
  (priority 1: salt2 ±5/±10Q; priority 2: salt3; etc.). **Blockers:** (a) prior
  sessions hit TACC allocation/SU encumbrance that blocked submission; (b) this is
  the Codex-owned corrected-Salt campaign (AGENT-181/178/237). **Do not submit
  without** an allocation/SU check and coordinator + user go-ahead.

## Prioritized next steps

1. Decide on the git commit scope (this session's tools vs coordinated repo commit).
2. Allocation/SU check; if clear and approved, coordinate with Codex to submit the
   priority-1 corrected-Salt Q extended continuations, then rerun the gate inventory.
3. Integrate the improved pressure figures into the July 8 presentation package.
4. Add the absolute heat-vs-time series and (optionally) push steady-state/SEM
   quality flags into the observation table.

## Open decisions for the user

- Commit now (narrow) or defer?
- Submit the corrected-Salt Q extended continuations tonight (if allocation
  permits) or hold for coordination?
- Preferred averaging window for the paper-facing steady-state figures (currently
  300 s)?
