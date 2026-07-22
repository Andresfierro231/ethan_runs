---
provenance:
  - .agent/BOARD.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/07-26/22/2026-07-22_BOARD_CLEANUP_AND_AVENUE_GAP_DISPATCH.md
tags: [coordination, board-cleanup, predictive-1d, thesis, research-avenues]
related:
  - .agent/status/2026-07-22_TODO-BOARD-STALE-CLEANUP-AND-HIGH-VALUE-1D-AVENUES-2026-07-22.md
  - .agent/journal/2026-07-22/board-stale-cleanup-and-high-value-1d-avenues.md
  - imports/2026-07-22_board_stale_cleanup_and_high_value_1d_avenues.json
task: TODO-BOARD-STALE-CLEANUP-AND-HIGH-VALUE-1D-AVENUES-2026-07-22
date: 2026-07-22
role: Coordinator/Cleaner/Writer/Reviewer
type: operational_note
status: complete
---
# Board Stale Cleanup and High-Value 1D Avenues

Task: `TODO-BOARD-STALE-CLEANUP-AND-HIGH-VALUE-1D-AVENUES-2026-07-22`

## Why This Pass Exists

The board accumulated another wave of completed rows after the earlier cleanup. Those stale rows were making Active and Planned look busier than the actual work frontier. This pass removed completed items from live queues and added a small number of non-overlapping research avenues that strengthen the predictive 1D model and thesis without launching compute, admitting closures, or editing thesis prose.

## Board Cleanup

- Archived `28` completed rows from `## Active` after each passed `python3.11 tools/agent/finish_task.py --task-id <TASK> --json`.
- Archived this coordinator row after closeout documentation and validation.
- Archived `51` self-complete rows from `## Planned / Unclaimed`; `34` passed current `finish_task.py` validation and `17` were legacy complete rows whose manifests predate the current strict schema or whose artifacts were not discoverable by the validator.
- `TODO-THESIS-LATEX-EVIDENCE-PACKET-IMPORT-2026-07-22` initially failed closeout due a missing import manifest, then the manifest landed; it passed `finish_task.py --json` and was archived.
- `TODO-MF09-RECIRCULATING-UPCOMER-THERMAL-MODEL-ALTERNATIVES-2026-07-22` initially failed closeout due missing artifacts, then the artifacts landed; it passed `finish_task.py --json` and was archived.
- Final live board state after this pass: `## Active` has `16` rows and `0` complete-status rows; `## Planned / Unclaimed` has `24` rows and `0` complete-status rows.

## High-Value Avenues Added

1. `TODO-1D-CONSERVATIVE-THERMAL-LEDGER-RESIDUAL-OWNER-CONTRACT-2026-07-22`
   Model-facing heat ledger contract separating heater input, cooler/HX removal, passive losses, radiation, storage, and residual owners before fitting.

2. `TODO-1D-SENSOR-PROJECTION-OPERATOR-TP-TW-WALL-BULK-2026-07-22`
   Measurement operator from predicted 1D bulk/wall states to TP/TW observations, with uncertainty and runtime-temperature guardrails.

3. `TODO-1D-REGIME-MAP-NONDIMENSIONAL-CLOSURE-ELIGIBILITY-2026-07-22`
   Literature plus CFD nondimensional regime map for deciding which correlations are eligible by case and segment.

4. `TODO-1D-SETUP-ONLY-BC-UQ-PROPAGATION-2026-07-22`
   Propagate setup-input uncertainty before final scoring: heater fraction, cooler UA, ambient/radiation, insulation, geometry, property modes, pressure losses, and sensor projection.

5. `TODO-1D-MODEL-HIERARCHY-ABLATION-LADDER-PACKET-2026-07-22`
   Thesis-facing ablation ladder across baseline, pressure/mdot coupling, thermal terms, axial mixing, source/property release, UQ gates, and freeze prerequisites.

6. `TODO-1D-THERMAL-PRESSURE-ROOT-COUPLING-STABILITY-AUDIT-2026-07-22`
   Stability audit for the coupled pressure/thermal root solve under setup-only perturbations.

## Recommended Next Order

1. Run the conservative thermal ledger contract first. It is the best bridge from "mdot is fine" to a defensible thermal model.
2. Run the sensor projection operator next, because score errors are only interpretable once the model-to-sensor mapping is explicit.
3. Run the nondimensional regime map in parallel with writing work; it supplies the literature basis for closure eligibility.
4. Use the setup-only BC UQ row before any final scorecard or freeze decision.
5. Use the ablation ladder row to convert existing negative and diagnostic results into thesis structure.
6. Use the root-coupling stability audit before broader Fluid score grids or external implementation rows.

## Do Not Do

- Do not fit, tune, select, or admit a closure from these coordinator rows.
- Do not relax the runtime-input ban on CFD `mdot`, realized CFD `wallHeatFlux`, imposed CFD cooler duty, realized test-section heat, or validation temperatures.
- Do not edit Fluid, external papers, thesis body/LaTeX files, registry/admission state, scheduler jobs, or native CFD/OpenFOAM outputs from this cleanup task.
- Do not run S11/S12/S13/S15/S6 triggers from this coordination task.
