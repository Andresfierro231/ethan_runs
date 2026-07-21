# Salt2 Fine Closure-QOI Smoke And Overnight

Task: `AGENT-239`

## Observed

- The Salt2 refined cases have the expected latest-time decomposed fields:
  - medium: `processors64/518/{T,U,p_rgh,rho,wallHeatFlux,wallShearStress,yPlus}`
  - fine: `processors128/399/{T,U,p_rgh,rho,wallHeatFlux,wallShearStress,yPlus}`
- OF13 is available on compute node `c318-008` and reports the custom
  `libRCWallBC.so` runtime as ready.
- `python3` has `numpy 1.21.2` and `scipy 1.6.1`; `python3.11` still lacks
  `pytest`.

## Implementation

- Built a task package at
  `work_products/2026-07/2026-07-09/2026-07-09_salt2_fine_closure_qoi_smoke_and_overnight/`.
- Added a generator that emits a stage-safe runner:
  - stages `constant/`, `system/`, `0/`, and `case_config.yaml` locally;
  - symlinks source `processors<N>` read-only into the staged mirror;
  - symlinks source monitor folders needed for mdot and wallHeatFlux reads;
  - reconstructs only closure fields into the staged mirror;
  - runs section pressure, segment friction, momentum budget, and thermal closure extraction under the existing tool contracts.
- Because refined Salt2 source IDs are not registered in
  `tools.case_analysis_profiles`, the runner uses
  `viscosity_screening_salt_test_2_jin_coarse_mesh` as the station/segment
  profile while recording the physical medium/fine source paths separately.

## Smoke Failure And Repair

The first persistent `tmux` launch reached medium reconstruction and failed with
an OpenFOAM fatal IO error: staged `controlDict` still included
`system/functions`, but the initial runner had removed that file. The generator
was patched to write an empty include-compatible `system/functions` in the staged
mirror instead.

## Live Run

- Persistent session: `agent239_salt2_refined_r2`.
- Live log:
  `work_products/2026-07/2026-07-09/2026-07-09_salt2_fine_closure_qoi_smoke_and_overnight/logs/tmux_smoke_then_overnight_r2.log`.
- The medium and fine extraction chain completed before 17:00:
  - medium completed at `2026-07-09T16:44:14-05:00`;
  - fine completed at `2026-07-09T16:58:31-05:00`.

## Batch Clarification

After the interactive run completed, a 10pm `sbatch` wrapper was created and job
`3287480` was submitted as a scheduled rerun. The user clarified that no rerun is
needed if the outputs already exist. The 10pm job was cancelled. It would have
run the same `smoke_then_overnight` driver and produced no new analysis beyond
the completed medium/fine extraction.

## Interpretation

This is extraction only. Any produced medium/fine closure-QOI rows still need
review against the aligned mainline coarse baseline before GCI or
`closure_observations.csv` changes are justified.
