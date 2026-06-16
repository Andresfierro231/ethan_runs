# Ethan Runs Update

Date: 2026-06-05

## Observed Outputs

- Finished the transient and axial audit layer on top of `reports/2026-06-04_ethan_transient_axial_package/`.
- Added reusable audit/report script `tools/analyze/build_ethan_transient_axial_audit.py` and generated:
  - `metric_coverage_end_times.csv` / `.png`
  - `axial_field_extraction_audit.csv`
  - `case_audit_summary.csv`
  - `salt_test_*_transient_tail.png`
  - `salt_test_2_axial_temperature_profile.png`
  - `salt_test_3_axial_temperature_profile.png`
  - `plot_and_term_guide.md`
  - `scientific_numerical_analysis.md`
- Added three new reusable follow-up analysis scripts:
  - `tools/analyze/build_ethan_continuation_diagnosis.py`
  - `tools/analyze/build_ethan_wall_loss_resistance_report.py`
  - `tools/analyze/build_ethan_convergence_and_salt1_campaign.py`
- Generated new dated report packages:
  - `reports/2026-06-05_ethan_continuation_diagnosis/`
  - `reports/2026-06-05_ethan_wall_loss_resistance_coupling/`
  - `reports/2026-06-05_ethan_convergence_and_salt1_campaign/`
- Confirmed through Slurm accounting and local logs that the current continuation sequence is:
  - `3202708`: Salt 2 continuation still running
  - `3208600`, `3208837`: Salt 4 Jin bootstrap failure with `gcc --showme:link`
  - `3208905`: Salt 4 Jin dummy-Pstream failure after bootstrap repair
  - `3208956`: Salt 1 Jin dummy-Pstream failure
- Confirmed from the metadata index that Salt 4 Jin still uses effectively constant `Cp = 1423.47 J/kg-K`.
- Repaired the shared OpenFOAM 13 env wrapper at `jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh` so it now sources `etc/bashrc` with `WM_MPLIB=INTELMPI`, matching the compute-validated runtime probe path.
- Resubmitted Salt 4 Jin continuation after that repair as Slurm job `3210231`.
- Created a Salt 1 targeted campaign wrapper under `jadyn_runs/salt1/2026-06-05_targeted_campaign/` and began staging a new Salt 1 Kirst continuation candidate.

## Interpretation

- The transient/axial package is now strong enough for scientific writeup and numerical audit. The main remaining limitation is not missing package outputs, but incomplete full-field latest-time extraction on several staged rows.
- The continuation blocker is now narrow: the strongest remaining technical difference between the compute-validated recovery path and the failing Salt 1/Salt 4 continuations was the `WM_MPLIB=INTELMPI` bashrc bootstrap pattern.
- Salt 4 Jin remains worth pursuing as a background continuation once the launcher is corrected. The current scientific evidence still treats it as practically usable but borderline on steadiness.
- Cross-case evidence continues to favor a coupled wall-loss and resistance explanation for the mass-flow mismatch. Ambient-loss bias is shared across Salt 2-4, but mdot varies materially between Jin and Kirst.
- The eight-case convergence pass now supports a practical classification for all four salt representatives and all four water laminar cases. Current water rows look better than the earlier claim audit, but still show noticeable late-window drift and should be treated as borderline rather than cleanly converged.
- Salt 1 still stands out as the weakest salt test. The immediate honest next step is continuation retry, not speculative new physics runs first.

## Contradictions / Caveats

- The new water classifications depend on practical steadiness metrics rather than the coded convergence monitor. That improves decision usefulness, but the distinction must stay explicit in future reporting.
- Salt 1 Kirst did reach the coded convergence monitor, yet still fails the practical steady-state criterion because of its residual heat-balance floor.
- Salt 4 Jin continuation repair is not proven yet; `3210231` is only the new retry after the `WM_MPLIB` bootstrap fix.
- The Salt 1 Kirst continuation staging copy was still in progress at the time of this journal entry and therefore not yet submitted.

## Suggested Next Actions

- Monitor `3210231` quickly to see whether the dummy-Pstream failure is cleared.
- Finish the Salt 1 Kirst staging copy, then submit the Salt 1 Jin and Salt 1 Kirst targeted continuation retries.
- If the repaired bootstrap still fails, use an interactive compute node only then, to inspect `foamRun`, `ldd`, and loaded MPI/OpenFOAM libraries rank-by-rank.
- Build the missing transient `p_rgh` history path next, because that is the cheapest discriminating test for the resistance-coupling hypothesis.
- Refresh the June 5 convergence, continuation, and wall-loss reports after any new continuation output appears.

## Additional Visualization Pass: ParaView Latest-Time Temperature Slices

### Observed Outputs

- Added reusable ParaView batch renderer at tools/extract/render_last_timestep_temperature_slices.py.
- Added reusable OpenFOAM latest-time staging helper at tools/extract/stage_latest_time_reconstruction.py.
- Added Slurm launchers under staging/render_jobs for the reconstruction-first visualization path and the single-case smoke test.
- Confirmed the raw processors64 collated cases do not expose T cleanly to ParaView 5.13 on either login-node smoke tests or the first dev-queue direct-reader batch attempt.
- Confirmed reconstructPar latestTime field reconstruction with collated file handling succeeds against read-only mirrored staging cases without mutating imported source roots.
- Verified a successful compute-node smoke render for viscosity_screening_salt_test_1_kirst_coarse_mesh through job 3211183, producing the requested PNG and SVG outputs under figures.
- Wrote provenance manifest imports/2026-06-05_paraview_last_timestep_temperature_slices.json.

### Interpretation

- The viable rendering path is reconstruction-first: stage a mirrored case, reconstruct latest-time T, then run one pvbatch process per case against the reconstructed mirror.
- Treat the direct collated-reader path as operationally unreliable for this workspace. The field arrays either do not populate or the ParaView process destabilizes after output creation.
- The new renderer logic itself is good enough for the target visualization once the case layout is normalized into reconstructed latest-time mirrors.

### Contradictions / Caveats

- The compute smoke render created the requested PNG and SVG, but the ParaView process still exited nonzero afterward, so batch fan-out should verify file existence per case instead of trusting process exit alone.
- A single all-cases pvbatch invocation is not the safe scale-out mode here. The more defensible next step is one process per case after reconstruction.

### Suggested Next Actions

- Finish the all-case reconstruction pass and then fan out one dev or regular-queue render job per registered case.
- After each per-case render, verify the expected figures source-id PNG exists and record that in a batch summary JSON.
- If the post-render nonzero exit persists, keep the existence check as the success criterion and do not regress to the raw collated-reader route.
