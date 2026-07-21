# Ethan Runs Update

Date: 2026-06-25

## Observed Outputs

- Staged eight new June 25 Salt case roots under `jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runs/` plus a campaign-local `runtime_libs/libRCWallBC.so` copy.
- Submitted eight packed `normal`-partition chain launches covering the requested Water relaunches, the requested Salt 1 continuation plus Salt 1-4 high-Q cases, and seven bounded extra Salt heater-only boundary cases.
- The exact job chains are:
  - `ethan_w12_nq9d`: `3259055-3259059`
  - `ethan_w34_nq9d`: `3259060-3259064`
  - `ethan_s1cont_s1hi_nq9d`: `3259065-3259069`
  - `ethan_s23hi_nq9d`: `3259070-3259074`
  - `ethan_s4hi_s1lo_nq9d`: `3259075-3259079`
  - `ethan_s2mid_nq9d`: `3259080-3259084`
  - `ethan_s3mid_nq9d`: `3259085-3259089`
  - `ethan_s4mid_nq9d`: `3259090-3259094`
- At submission time the first segment of each chain was `PENDING` on `Resources`, and later segments were `PENDING` on `Dependency`.

## Interpretation

- The original normal-queue relaunch failure was a runtime-packaging issue, not evidence that the Water or high-Q Salt cases themselves were invalid. Moving `libRCWallBC.so` into the campaign root under `/scratch` removes the specific `/home1/.../ethan_data` dependency that caused the instant failures.
- The best currently bounded recirculation-onset screen is a heater-only ladder, not another insulation sweep. The June 17 nondimensional table shows Salt 1 has the lowest mean upcomer state but the largest baseline loop temperature span, while Salt 4 is hottest in mean state without having the largest span. That means onset can only be separated cleanly by bracketing both effects.
- The compact extra set that does that without wasting nodes is: Salt 1 `-10%/+10%` bracketing and balanced Salt 2-4 `+/-5%` midpoint cases, layered on top of the already requested Salt 1-4 high-Q cases and the live baseline / live `-10%` references.

## Contradictions / Caveats

- The user-requested `216 h` single-job walltime is not legal on this account's `normal` queue. `qnormal` hard-caps each job at `2-00:00:00`, so the submitted form had to become five dependent `48 h` segments per packed pair.
- Existing NuclearEnergy jobs `3254178` and `3254179` were still running when the June 25 normal chains were submitted.
- Queue acceptance is now confirmed, but solver-level continuation still needs runtime monitoring once the first segments start.

## Suggested Next Actions

- Watch the first segment of each chain for actual node start and verify the new June 25 Salt roots materialize `processors64/` and enter `foamRun` cleanly.
- If the first segments survive startup, let the boundary ladder accumulate enough retained-time evidence to compare recirculation onset against both `temp_upcomer_bulk_k` and `heater_to_cooler_bulk_delta_k`.
- If onset still cannot be localized after the midpoint ladder, the next bounded follow-on should target mean-state-isolation cases rather than reopening insulation as a free variable.

## Checkpoint / Stopping Point

- The active submission record is `imports/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave.json`.
- The campaign manifest with case-to-chain mapping is `jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/campaign_manifest.csv`.
