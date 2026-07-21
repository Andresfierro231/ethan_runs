# Reconstructed T Repair Trial

Task: `AGENT-267`
Date: `2026-07-13`

## Question

AGENT-265 showed the AGENT-245 reconstructed medium `T` was corrupt: five `-nan` tokens in the serial reconstructed field, while AGENT-248 diagnostics showed the native decomposed medium/fine `T` sources had zero nonfinite tokens. The immediate question was whether Salt2 refined thermal UA/HTC/Nu was blocked by native physics/data or by the reconstruction/postprocessing path.

## Observed

Fresh task-scoped staging under `work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_trial/` showed:

- `T`-only reconstruction is clean in all tested modes:
  - uncollated `-case`,
  - staged cwd using `OptimisationSwitches.fileHandler collated` and `maxThreadFileBufferSize 0`,
  - explicit `-fileHandler collated`.
- Naive scalar plausibility scanning was wrong because OpenFOAM stores non-temperature auxiliary data inside the `T` field dictionary, including `qConv`, `refGradient`, `valueFraction`, `h`, and `Q`.
- The repair scanner now separates:
  - whole-file scalar syntax/nonfinite checks, and
  - Kelvin plausibility checks for `internalField` and boundary `value` lists only.
- Full-field reconstruction that includes `T` together with `p_rgh U rho wallHeatFlux wallShearStress yPlus` can still introduce `-nan` tokens into auxiliary `T` payloads. This reproduced even with `maxThreadFileBufferSize 0`.
- Split reconstruction avoids that failure: reconstruct `T` first, reconstruct only non-`T` fields afterward, then rescan `T`.
- `system/functions` must be absent before `foamPostProcess`; otherwise OF13 ignores sampler-generated `controlDict/functions`, causing no section outputs.
- The segment HTC script hard-codes an OF12 `foamPostProcess` path. The task wrapper therefore lets it write its `segthermSurfaces` controlDict, reruns `foamPostProcess` under OF13, and then parses with `--skip-run`.

## Evidence

Accepted medium split stage:

- stage: `work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_trial/recon/medium_cwd_controlDict_collated_split_full`
- final `518/T` scan:
  - whole-file nonfinite count: `0`
  - Kelvin-valued entries: `7,158,792`
  - parsed temperature lists: `47`
  - temperature range: `347.356576..489.029692 K`
- section sampling:
  - `30/30` sampled rows
  - spans: `lower_leg`, `right_leg`, `left_lower_leg`, `test_section_span`, `left_upper_leg`, `upper_leg`
  - no OpenFOAM fatal
- segment extraction:
  - `lower_leg`: computed, `T_bulk=449.893181 K`, `T_wall=458.205862 K`, `HTC=457.342556 W/m2/K`, `UA'=40.049920 W/m/K`
  - `upcomer`: computed, `T_bulk=455.039466 K`, `T_wall=449.909007 K`, `HTC=77.937240 W/m2/K`, `UA'=6.691895 W/m/K`, `Nu=4.284836`
  - `downcomer`: still blocked by `thermally_blocked_segment_right_leg`

Primary files:

- `work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_trial/summary.json`
- `work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_trial/outputs/reconstruction_trials.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_trial/logs/segment_thermal_medium_of13_foampostprocess.log`
- `work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_trial/logs/segment_thermal_medium_skip_run.log`

## Interpretation

The original NaN/OpenFOAM failure is not native decomposed-source corruption. It is a reconstruction/postprocessing-path problem. For medium Salt2 refined, thermal extraction can be unblocked by:

1. task-scoped staging,
2. clean `T`-only reconstruction,
3. non-`T` follow-up reconstruction,
4. strict `T` rescanning,
5. removing staged `system/functions` before function-object sampling,
6. using OF13 for T-bearing `foamPostProcess` calls.

The generated medium HTC/UA/Nu rows are smoke evidence, not closure-admitted values. The lower-leg and upcomer signs also need review before publication/admission.

## Remaining Work

- Run the same split reconstruction and OF13 segment fallback on the Salt2 fine refined case.
- Review heat-balance and sign consistency for the computed medium lower-leg/upcomer rows.
- Keep downcomer thermal blocked unless a separate task explicitly changes the right-leg/downcomer policy.
- Do not use these rows as closure-fit inputs until mesh-family and admission gates are complete.

