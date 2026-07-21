# Preparing for Presentation

Date: `2026-07-01`  
Role: Coordinator / Implementer / Writer  
Task ID: `AGENT-169`  
Branch or worktree: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs`

## Purpose

Save the July 1 presentation-prep state and produce a reusable package for
tomorrow's meeting. The goal is to separate what is presentation-ready from what
is merely diagnostic, blocked, or future validation work for the 1D ROM.

## Files Inspected

- `reports/2026-06/2026-06-23/2026-06-23_ethan_1d_closure_bakeoff/summary.json`
- `reports/2026-06/2026-06-23/2026-06-23_ethan_1d_closure_bakeoff/surface_summary.csv`
- `reports/2026-06/2026-06-23/2026-06-23_ethan_frozen_state_1d_validation/`
- `reports/2026-06/2026-06-29/2026-06-29_ethan_salt_pressure_drop_predictivity/`
- `reports/2026-06/2026-06-30/2026-06-30_claude_closure_results/README.md`
- `reports/2026-07/2026-07-01/2026-07-01_rom_postprocessing_correctness_validation/README.md`
- `reports/2026-07/2026-07-01/2026-07-01_model_form_comparison/README.md` as read-only AGENT-168 provenance

## Files Changed

- `.agent/BOARD.md` own AGENT-169 row
- `.agent/status/2026-07-01_AGENT-169.md`
- `.agent/journal/2026-07-01/preparing-for-presentation.md`
- `tools/analyze/build_presentation_readiness_and_rom_agenda.py`
- `tools/analyze/test_presentation_readiness_and_rom_agenda.py`
- `reports/2026-07/2026-07-01/2026-07-01_presentation_readiness_and_rom_agenda/**`
- `work_products/2026-07-01_presentation_readiness_and_rom_agenda/**`
- `tmp/2026-07-01_presentation_readiness_jobs/**`
- `reports/2026-07/2026-07-01/2026-07-01_local_1d_validation_refresh/**`
- `reports/2026-07/2026-07-01/2026-07-01_local_1d_closure_bakeoff_refresh/**`
- `reports/2026-07/2026-07-01/2026-07-01_local_1d_discrepancy_refresh/**`
- `imports/2026-07-01_local_1d_validation_refresh.json`
- `imports/2026-07-01_local_1d_closure_bakeoff_refresh.json`
- `imports/2026-07-01_local_1d_discrepancy_refresh.json`

## Results Saved

Generated package:
`reports/2026-07/2026-07-01/2026-07-01_presentation_readiness_and_rom_agenda/`

Work-product tables:
`work_products/2026-07-01_presentation_readiness_and_rom_agenda/`

Key rows:

- `paper_readiness_matrix.csv`: 9 items separating paper-ready methods,
  meeting-ready diagnostics, blocked uncertainty, running CFD, and future
  experimental validation.
- `figure_inventory.csv`: 8 existing figures with readiness labels and slide
  use.
- `model_form_inventory.csv`: F0-F5 model forms with assumptions, current
  metrics, and credibility limits.
- `coefficient_inventory.csv`: Salt 2/3/4 thermal HTC, UA', R', upcomer Nu, and
  local hydraulic replay error metrics.
- `future_model_forms.csv`: 6 next model forms including buoyancy-corrected
  mechanical loss, low-Re bend K, redevelopment loss, UA' laws, upcomer
  recirculation onset, and experiment-validated uncertainty.
- `experimental_validation_next_steps.md`: data contract and validation protocol
  needed before claiming real-world predictivity.

Meeting-ready numbers:

- Defended current 1D scenario:
  `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`.
- Current 1D bakeoff metrics: mean energy error `11.27%` of heater power;
  mean mass-flow relative error `26.69%` vs CFD.
- Local hydraulic replay: probe replay mean `|mdot|` error `0.000255 kg/s`;
  major-only `0.554 kg/s`; endpoint replay `0.484 kg/s`.
- Thermal closure extraction: lower-leg HTC `252/269/288 W/m2-K` for
  Salt 2/3/4; upcomer Nu `3.11/4.06/4.99`.

Interpretive boundary:

- Strongest paper-facing material now is post-processing method/provenance and
  diagnostic mechanism evidence.
- Full predictive ROM remains in progress because mesh independence is blocked,
  perturbation runs were false-steady, and pressure gradients need the
  variable-density buoyancy/mechanical-loss decomposition before fitting Darcy
  losses.

## Local Jobs

Created lightweight local wrappers:

- `tmp/2026-07-01_presentation_readiness_jobs/run_presentation_builder.sh`
- `tmp/2026-07-01_presentation_readiness_jobs/run_1d_refresh_chain.sh`

Attempted detached background launch, but the shell wrapper did not preserve
useful child PIDs/logs in this environment. I then ran both wrappers directly
and with log redirection. They completed quickly, so no overnight local process
remains. This still produced the requested refreshed local analysis outputs.

Refresh outputs:

- `reports/2026-07/2026-07-01/2026-07-01_local_1d_validation_refresh/`
- `reports/2026-07/2026-07-01/2026-07-01_local_1d_closure_bakeoff_refresh/`
- `reports/2026-07/2026-07-01/2026-07-01_local_1d_discrepancy_refresh/`

## Commands Run

- `python3 -m pytest tools/analyze/test_presentation_readiness_and_rom_agenda.py -q`
- `python3 tools/analyze/build_presentation_readiness_and_rom_agenda.py`
- `bash tmp/2026-07-01_presentation_readiness_jobs/run_presentation_builder.sh`
- `bash tmp/2026-07-01_presentation_readiness_jobs/run_1d_refresh_chain.sh`

## Validation

- Focused test: `5 passed`.
- Presentation package generated with 9 paper-readiness rows, 8 figure rows,
  6 model-form rows, 21 coefficient rows, 6 future model-form rows, and 5
  run-inventory rows.
- Refreshed 1D validation package generated 33 comparison rows and 528 sensor
  error rows.
- Refreshed bakeoff package generated 6 scenarios and defended the same current
  scenario as the June 23 package.
- Refreshed discrepancy package generated 9 cases, 3 supported explanations,
  and 1 possible explanation.

## Incomplete Lines of Investigation

- The AGENT-164 true-steady insulation CFD runs are still the next useful data
  source; do not touch their active directories.
- The AGENT-162 mesh-centerline extractor wiring should feed the next pressure
  decomposition pass once ownership clears.
- No GCI bound exists because the mesh generator/refinement plan is missing.
- Experimental validation remains planned future work and needs a formal data
  contract plus calibration/validation split.

## Next Steps

1. Use the generated README and `figure_inventory.csv` for tomorrow's slide
   selection.
2. Use `model_form_inventory.csv` and `future_model_forms.csv` as the working
   agenda for the next ROM fit/bakeoff wave.
3. After AGENT-164 produces true-steady windows, update the upcomer recirculation
   and insulation-response rows.
4. Implement buoyancy-corrected pressure/mechanical-loss decomposition before
   fitting pressure-derived Darcy friction in heated/cooled legs.
