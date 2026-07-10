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

## Decisions made (finalized 2026-07-10)

- **Committed and pushed.** This session's tooling/docs are committed to `main`
  (commit `ae73682` "Add postprocessor time-series/steady-state + pressure figure
  tooling") and pushed to origin. Generated SVGs stay on scratch (gitignored).
- **Averaging window: adopt 600 s** for paper-facing steady-state stats (current
  package on disk is 300 s — regenerate when picked up; command below). Rationale:
  sample interval = 1 s; integrated autocorrelation time median ~7–11 s but up to
  ~56–64 s for the slowest quantities; runs settle by ~1000 s and are 2,400–11,700 s
  long, so the last 600 s is pure settled tail for every run and ~doubles the
  effective sample size vs 300 s. For the few slow quantities (τ≈60 s) use a
  1,000–1,500 s window on the long runs only if paper-grade SEM on those is needed.
- **Q-perturbation submission plan (evidence: AGENT-244 mdot steadiness + AGENT-237
  gate resubmit_list):**
  - **Submit extended continuations for the 10 clean rows** — salt2 {lo5q, hi5q,
    lo10q, hi10q}, salt4 {lo5q, hi5q, lo10q, hi10q}, salt3 {lo5q, lo10q}. All are
    already stationary in the last window; the gate flags them only "too_short," so
    extensions just carry them to `operating_point_verdict=requalified`.
  - **Do NOT resubmit salt3 hi5q / hi10q — diagnose first.** mdot still drifting
    24 % / 45 % over the last 300 s, gate class `rerun_or_rebuild`, and near-empty
    scalar output (~32 KB). Open a diagnosis task, not a continuation.
  - **salt1 hi10q → rebuild; salt1 lo10q → defer to the salt1 review track.**

## PICKUP NEXT TIME — do these in order

1. **Allocation/SU check first** (submission was blocked before by TACC allocation
   encumbrance): from a login node, `ssh login3.ls6.tacc.utexas.edu` then check
   `sbalance` / project balance for `ASC23046`. Do not `sbatch` until SUs are clear.
2. **Coordinate with Codex** — the perturbation campaign
   (`jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/`) is
   Codex-owned (AGENT-178/181/237). Claim a fresh BOARD row and **stage extended
   continuations into a new dated dir** (do not mutate their `case_stage` trees).
3. **Submit the 10 clean extend rows** (list above). Use
   `ssh login3.ls6.tacc.utexas.edu "/usr/bin/sbatch <absolute_path>"` from a
   compute node. After they advance, rerun the `3280969`-style gate inventory and
   admit only rows that reach `operating_point_verdict=requalified`.
4. **Open a diagnosis task for salt3 hi5q/hi10q** (why still transient + near-empty
   output; likely rebuild).
5. **Regenerate the steady-state package at 600 s:**
   `python tools/analyze/build_timeseries_steadystate_report.py --window-seconds 600`
   (~2.5 min; overwrites the 300 s package in place).
6. **Integrate the improved pressure figures** into the July-8 deck: update
   `tools/analyze/build_postprocessor_summary_charts.py` (Codex AGENT-233 scope) to
   call `svg_chart_kit`, regenerate in place, and fix its stale
   `test_postprocessor_summary_charts.py` figure-count assertion. Needs Codex coord.
7. **Optional:** add an absolute heat-vs-time series (aggregate per-patch
   `wallHeatFlux.dat`) so thermal steadiness is judged on absolute heat, not just
   the near-zero net residual; optionally push steady-state/SEM quality flags into
   the closure observation table.

## Artifact pointers (for whoever picks up)

- Time-series pkg: `work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/`
  (README, METHODOLOGY, DATA_DISCLOSURE, steady_state_summary.csv, case_inventory.csv,
  cases/<slug>/figures + stats.csv).
- Pressure figs: `work_products/2026-07/2026-07-09/2026-07-09_pressure_decomposition_figures/`.
- Reusable tools: `tools/analyze/{openfoam_timeseries,timeseries_stats,svg_timeseries_chart,
  build_timeseries_steadystate_report,svg_chart_kit,palette_validator,
  build_pressure_decomposition_figures}.py` (+ their `test_*`).
- Gate resubmit list: `work_products/2026-07/2026-07-09/2026-07-09_corrected_salt_q_gate_3280969_review/resubmit_list.csv`.
- Status/journal: `.agent/status/2026-07-09_AGENT-234.md`, `_AGENT-244.md`;
  `.agent/journal/2026-07-09/implementer-writer-{pressure-decomposition-figures,timeseries-steadystate}.md`.
- Imports: `imports/2026-07-09_{pressure_decomposition_figures,timeseries_steadystate}.json`.
- Rerun tests: `python -m pytest tools/analyze/test_openfoam_timeseries.py
  tools/analyze/test_timeseries_stats.py tools/analyze/test_pressure_decomposition_figures.py
  tools/analyze/test_svg_chart_kit.py -q` (56 pass).
