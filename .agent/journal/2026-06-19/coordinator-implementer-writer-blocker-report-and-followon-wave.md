# AGENT-089 Raw Journal — Blocker Report And Follow-On Wave

## 2026-06-19

- Re-read the root repo instructions, ownership map, role map, and the
  `jadyn_runs/` and `tools/` local overrides before claiming the new scope.
- Opened a fresh additive task because the user asked for:
  - a report explaining why the currently submitted CFD wave was needed
  - a blocker-first 1D-model plan
  - the best next CFD runs to be suggested and submitted

## Main decision before staging anything

- The June 18 DOE scaffold mentioned heater power, cooler `h`, and insulation.
- The boundary-modeling report made the readable boundary explicit:
  - cooler metadata preserves a nominal `h`
  - readable `0/T` uses a fixed negative `Q` cooler sink
  - the transformation from metadata `h` to readable fixed sink is not visible
- Because of that, I refused to submit a literal cooler-`h` DOE from the
  readable artifacts.

## Report package

- Added:
  - `reports/2026-06-19_ethan_blocker_report_and_followon_wave/README.md`
  - `blocker_queue.csv`
  - `one_d_model_steps.csv`
  - `run_recommendations.csv`
  - `summary.json`
- The report does four things:
  - explains why the June 18 continuation wave was still necessary
  - separates the current blockers into “needs more CFD runtime” vs “needs a
    new retained-time extraction method”
  - fixes the defended Salt-first 1D-model boundary
  - records which follow-on CFD controls are actually visible and safe to
    mutate from the readable case trees

## Case-selection logic

- I used the June 19 v3 handoff plus exact fit-used rows.
- Salt 2 Jin and Salt 4 Jin were selected for immediate submission because:
  - both already contribute to defended Salt fit rows
  - Salt 2 stays near the lower-Re / validation-anchor side
  - Salt 4 stays near the hotter / higher-Re side
- Salt 1 was not selected because it does not currently contribute defended fit
  rows.
- Salt 3 was left as the next deferred midpoint extension, not the first
  bracket wave.
- Water was excluded because it remains readiness-only.

## Staging

- Created a fresh campaign root:
  - `jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/`
- Reused the generic OpenFOAM 13 continuation sbatch wrapper from the June 18
  wave.
- Staged four child cases from static, non-running parents:
  - Salt 2 Jin from the staged source at latest visible time `2431`
  - Salt 4 Jin from the prior continuation parent at latest visible time
    `5776`
- I initially interrupted the heavy copy commands before assuming they were
  complete, then validated the staged trees before patching them.

## Mutation details

- Submitted four visible-control children:
  - `salt2_jin_hiq_hiins`
  - `salt2_jin_loq_loins`
  - `salt4_jin_hiq_hiins`
  - `salt4_jin_loq_loins`
- Applied only:
  - lower-heater patch `Q` changes on `pipeleg_lower_04/05/06_straight`
  - mirrored heater-power changes in `case_config.yaml`
  - outer insulation-thickness changes throughout `0/T`
- Intentionally left unchanged:
  - powered test-section patch
  - cooler branch fixed sinks

## One staging correction

- The first patch only changed the targeted heater blocks and a few nearby
  thickness entries.
- A sanity grep showed that the outer insulation layer still appeared
  everywhere else in `0/T`.
- I corrected that by replacing the remaining baseline outer-insulation value
  across each staged child `0/T`, so the insulation mutation is now globally
  consistent within each case.

## Submission

- Submitted through:
  - `ssh login3.ls6.tacc.utexas.edu ... sbatch --parsable ...`
- Returned job IDs:
  - `3246561` `ethan_s2j_hiqins`
  - `3246564` `ethan_s2j_loqins`
  - `3246562` `ethan_s4j_hiqins`
  - `3246563` `ethan_s4j_loqins`
- Initial queue check:
  - all four jobs are `PD (Priority)`

## Remaining scientific boundary after this task

- The new Salt bracket wave is justified and submitted.
- It does not solve the feature `K_eff` blocker by itself.
- The feature blocker still needs a retained-time full-path hydro closure.
- The straight-friction late-window blocker still depends first on the ongoing
  continuation wave recovering defended retained-time straight rows.

## Follow-on implementation-spec pass

- The first version of the report package was still too handoff-like for
  immediate model-building work, so I extended it into a real Salt-first 1D
  implementation spec under the same claimed report root.
- Added:
  - `blocker_resolution_plan.md`
  - `one_d_implementation_spec.md`
  - `one_d_state_vector.csv`
  - `one_d_closure_map.csv`
  - `one_d_calibration_table_spec.csv`
- The key modeling decision is to make v1 explicitly hybrid rather than fake a
  fully closed geometry model:
  - admitted straight friction fit on `lower_leg` and `test_section_span`
  - primary thermal surface `UA'(x)` on the safe Salt branch subset
  - optional direct `Nu(Re)` only on `left_lower_leg`
  - one lumped hydraulic residual and one lumped thermal residual to absorb
    blocked feature / unsupported return-path behavior
- I also made the CFD-versus-implementation split explicit:
  - more CFD is directly useful for retained-time straight rows
  - more CFD alone is not enough for feature `K_eff`; that path needs a new
    retained-time feature-path extractor first
- I preserved the earlier cooler boundary refusal in the 1D spec too:
  - the readable cases expose fixed cooler `Q`, not a live cooler-side `h`
    control, so both CFD DOE planning and the 1D input contract should treat
    cooler duty as fixed-`Q` unless a readable preprocessing link is found

## Same-day follow-on staging after the initial submission

- After the user confirmed the 3D path remains the priority, I staged the
  deferred Salt 3 Jin midpoint bracket instead of inventing any new Water,
  cooler-`h`, or feature-focused CFD wave.
- Parent used for both deferred children:
  - `staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_3_jin_coarse_mesh`
  - latest visible restart time retained from the staged source: `2514 s`
- Staged children:
  - `salt3_jin_hiq_hiins`
    - heater `Q` raised from `297.5 W` to `327.25 W`
    - each lower-heater segment in `0/T` raised from `99.16666666666667 W` to
      `109.08333333333333 W`
    - global outer insulation changed from `0.035559999999999994 m` to
      `0.04572 m`
  - `salt3_jin_loq_loins`
    - heater `Q` lowered from `297.5 W` to `267.75 W`
    - each lower-heater segment in `0/T` lowered from `99.16666666666667 W` to
      `89.25 W`
    - global outer insulation changed from `0.035559999999999994 m` to
      `0.0254 m`
- These two children were intentionally left unsubmitted.
- Reason for deferral:
  - the current queue already contains:
    - three still-running June 18 Jin continuations
    - four pending Salt 2 / Salt 4 Jin bracket children
  - the next justified new submission remains the Salt 3 midpoint pair, but it
    should wait until the active bracket wave shows acceptable health and value

## Monday restart context

- If Monday starts with presentation prep as the main priority, the first
  scientific status check should be:
  - `squeue -j 3244950,3244951,3244954,3246561,3246562,3246563,3246564`
- The Monday CFD decision tree is now simple:
  - if the running continuations and the Salt 2 / Salt 4 bracket wave look
    healthy, the staged Salt 3 midpoint pair is the next bounded submission
  - if the running jobs still dominate queue attention, presentation work
    should treat Salt 3 as ready-but-held rather than as missing
  - if discussion pivots back to feature `K_eff`, the real next blocker is the
    retained-time feature-path extractor, not another scenario expansion

## Same-day packed optimum-thickness submission

- After the insulation-optimizer follow-up request, I staged a dedicated
  optimum-thickness subcampaign under:
  - `jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/optimum_insulation_wave/`
- Four per-case Salt Jin targets were fixed from the June 19 optimizer package:
  - Salt 1 Jin: `2.4000 in`
  - Salt 2 Jin: `1.7291 in`
  - Salt 3 Jin: `1.6696 in`
  - Salt 4 Jin: `1.8277 in`
- I verified that the current Jin Salt 3D cases use one uniform outer
  insulation layer value across the loop in `0/T`:
  - baseline outer layer: `0.035559999999999994 m` (`1.400 in`)
- I also rechecked scheduler efficiency:
  - the current June 18 continuation wave and the June 19 bracket-wave jobs
    each occupy a full 256-core node while running only `64` MPI ranks
  - the current running young bracket jobs are:
    - `3246561` `ethan_s2j_hiqins`
    - `3246564` `ethan_s2j_loqins`
- I deliberately did not cancel any existing jobs in this pass.
- I built two launch paths:
  - a local staging script plus packed sbatch wrapper
  - a compute-node self-staging packed sbatch wrapper for the same four cases
- Reason for the self-staging fallback:
  - the local sandboxed copy path was slow enough that waiting on four full
    login-node stages would delay the actual queue submission
  - self-staging on the allocated compute node keeps the launch reproducible
    while avoiding partial local copies as a submission blocker
- Submitted packed job:
  - job ID: `3246927`
  - job name: `ethan_salt_optpack`
  - submit path:
    - `ssh login3.ls6.tacc.utexas.edu 'cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch --parsable jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/optimum_insulation_wave/scripts/run_packed_optimum_insulation_wave_selfstage.sbatch'`
  - immediate queue state:
    - `PD (Priority)`
- Packed-launch design details:
  - allocation: `-N 1 -n 256`
  - one 64-rank `srun` per Salt Jin case
  - `--exclusive --exact --cpu-bind=cores --distribution=block:block`
  - the launcher validates `0/`, `constant/`, `system/`, and `processors64/`
    after each compute-node copy and before any solver start
- Cancellation boundary left explicit:
  - no queued or running jobs were canceled here
  - I asked the user specifically whether to cancel only the two young June 19
    bracket jobs after the packed job was in queue
  - I did not broaden that to the older June 18 continuation jobs because the
    sunk runtime there is already much larger and the stop/restart tradeoff is
    materially different

## Monday presentation handoff

This section is the intended restart point for Monday work if the priority
shifts from CFD submission to presentation preparation.

### Core scientific story already assembled on June 19

- The blocker-first Salt modeling story is already packaged in:
  - `reports/2026-06-19_ethan_blocker_report_and_followon_wave/README.md`
  - `blocker_resolution_plan.md`
  - `one_d_implementation_spec.md`
- The insulation-thickness story is already packaged in:
  - `reports/2026-06-19_ethan_insulation_optimizer_package/README.md`
  - `case_thickness_tables.md`
  - `thickness_scientific_analysis.md`
- The setup-modeling / readable-boundary warning that blocked a literal
  cooler-`h` DOE is already packaged in:
  - `reports/2026-06-15_ethan_boundary_modeling_report/README.md`
- The defended closure boundary and the reason the June 18 continuation wave
  was still necessary are already packaged in:
  - `reports/2026-06-19_ethan_closure_to_modeling_handoff/README.md`
  - `reports/2026-06-19_ethan_salt_model_dependency_package_v3/README.md`

### Exact CFD state to remember

- June 18 continuation wave:
  - still the main blocker-first runtime path
  - scientifically more valuable than the scenario-expansion children because
    it is the direct route to more retained-time defended straight rows
- June 19 Salt bracket-wave children:
  - `3246561` `ethan_s2j_hiqins`
  - `3246564` `ethan_s2j_loqins`
  - `3246562` `ethan_s4j_hiqins`
  - `3246563` `ethan_s4j_loqins`
- Salt 4 bracket-wave failure mode already diagnosed:
  - the failed Salt 4 children were incomplete staged copies missing
    `system/controlDict`
  - that is why later launch paths added explicit tree validation
- Packed optimum-thickness wave:
  - `3246927` `ethan_salt_optpack`
  - one `-N 1 -n 256` job
  - four concurrent `64`-rank Salt Jin cases
  - launcher:
    - `jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/optimum_insulation_wave/scripts/run_packed_optimum_insulation_wave_selfstage.sbatch`
- No jobs were canceled in this pass.

### Exact insulation-thickness context to remember

- Current Jin Salt 3D cases use one uniform outer insulation layer across the
  loop:
  - baseline outer layer in `0/T`: `0.035559999999999994 m` (`1.400 in`)
- Per-case solver-optimum Salt targets used for the packed wave:
  - Salt 1 Jin: `2.4000 in`
  - Salt 2 Jin: `1.7291 in`
  - Salt 3 Jin: `1.6696 in`
  - Salt 4 Jin: `1.8277 in`
- Family-level optimizer summary to remember:
  - Salt effective mean optimum: `1.907 in`
  - rounded Salt family recommendation: `1.90 in`
  - Water effective mean optimum: `0.393 in`
  - rounded Water family recommendation: `0.40 in`
- Important interpretation boundary:
  - the optimizer result is an effective wall-loss fit, not a fully validated
    literal redesign proof for insulation thickness alone

### Scheduler / compute insight to preserve

- The June 18 continuations and the first June 19 bracket jobs were not
  consolidated; each single `64`-rank case occupied a full `256`-core node.
- The packed-node conclusion is still:
  - four `64`-rank cases on one `256`-CPU LS6 node is the right CPU packing
    for these Salt jobs
  - use `--exclusive --exact --cpu-bind=cores --distribution=block:block`
  - keep `OMP_NUM_THREADS=1`
- The memory argument was not proven from strong Slurm telemetry, but there was
  no evidence that the Salt runs were close to exhausting node RAM.
- Practical recommendation preserved from the compute discussion:
  - do not cancel the mature June 18 continuation wave casually
  - if waste reduction becomes necessary, the first clean candidates are the
    younger June 19 Salt 2 bracket jobs rather than the older continuations

### Monday TODO for presentation prep

1. Recheck queue state first so the presentation says the right thing about
   what is still running, queued, failed, or already finished.
   - start with:
     - `squeue -j 3244950,3244951,3244954,3246561,3246562,3246563,3246564,3246927`
     - `sacct -j 3246927,3246561,3246562,3246563,3246564 --format=JobID,JobName,State,Elapsed,AllocCPUS,NodeList`
2. Decide whether the presentation should frame the June 19 work primarily as:
   - blocker-first 1D model planning
   - insulation-thickness optimization
   - compute-efficiency / packed submission cleanup
   - or a combined “next safe CFD actions” narrative
3. Pull the exact presentation-safe figures / tables from the already-written
   June 19 packages instead of recomputing new science on Monday unless queue
   state materially changes the story.
4. Keep the following lines explicit in any slides:
   - Water remains readiness-only.
   - feature `K_eff` is still blocked by missing retained-time feature-path
     hydro extraction.
   - the readable cooler branch remains fixed-`Q`, so a literal cooler-`h`
     DOE was refused.
   - the insulation optimizer gives effective wall-loss targets, not a final
     physical redesign proof.
5. If the user wants an operations-status slide, include:
   - which jobs were wasteful before packing
   - that `3246927` was submitted as a packed node
   - that no cancellations were executed yet
6. If the user wants a next-steps slide, preserve this order:
   - monitor the packed optimum-thickness job
   - keep harvesting retained-time support from the June 18 continuations
   - decide later whether to cancel the young June 19 Salt 2 bracket jobs
   - only after the queue / retained-time story is clear, revisit deferred
     Salt 3 midpoint submission

### Monday files to open first

- `reports/2026-06-19_ethan_blocker_report_and_followon_wave/README.md`
- `reports/2026-06-19_ethan_insulation_optimizer_package/README.md`
- `reports/2026-06-15_ethan_boundary_modeling_report/README.md`
- `jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/README.md`
- `jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/optimum_insulation_wave/README.md`
- `.agent/status/2026-06-19_AGENT-089.md`

### Monday unresolved decisions

- Whether to cancel `3246561` and `3246564`
- Whether `3246927` starts cleanly and self-stages without the earlier partial
  copy failure mode
- Whether presentation prep should stay report-first or widen into a live
  compute-status / queue-efficiency story

## 2026-06-22 repair refresh

- Rechecked the June 19 queue state from `sacct` and confirmed the exact
  runtime outcomes:
  - `3246562` and `3246563` failed in seconds because their Salt 4 staged
    trees lacked `system/controlDict`
  - `3246927` failed because the compute-node self-staging launcher called
    `rg`, which was unavailable on the runtime path
  - `3244952`, `3244953`, and `3244956` timed out on June 22, reinforcing the
    bounded Water-readiness story without changing the Salt-first modeling
    boundary
- Preserved the failed artifacts instead of overwriting them:
  - Salt 4 bracket failures under
    `failed_stage_preserved/2026-06-22_salt4_bracket_repair/`
  - optimum self-stage failure under
    `optimum_insulation_wave/failed_stage_preserved/2026-06-19_job3246927_selfstage_failed_rg_missing`
- Hardened the launchers before resubmission:
  - replaced `rg` checks with `grep -Eq` in the optimum staging path
  - added fail-fast `0/`, `constant/`, `system/`, and `system/controlDict`
    validation to the generic continuation launcher
- Rebuilt the failed Salt 4 children from the static parent continuation tree,
  then re-applied only the intended mutated `0/T` and `case_config.yaml`
  files.
- Relaunched only the failed jobs:
  - `3250524` `ethan_s4j_hiqins_r2`
  - `3250525` `ethan_s4j_loqins_r2`
  - `3250526` `ethan_salt_optpack`
- Queue state immediately after the repair relaunch:
  - running:
    - `3246561`, `3246564`, `3250524`, `3250525`
  - pending:
    - `3250526`
- Updated the blocker report, campaign manifest, optimum subcampaign manifest,
  import manifest, and task status so the durable record now matches the real
  June 22 runtime lineage instead of the original June 19 submission-only
  snapshot.
