# AGENT-090 Raw Journal — Lit Review To 1D Modeling Handoff

## 2026-06-19

- Re-read the root repo instructions, board, ownership map, roles, and the
  `reports/` local override before claiming a new report-only scope.
- Confirmed that the active June 19 modeling handoff roots already belong to
  `AGENT-087` and `AGENT-089`, so the new work had to use a fresh additive
  report root rather than editing those packages in place.

## Intent

- Build one local package that turns the literature-review closure menu into a
  repo-usable 1D modeling handoff.
- Correct the overly strong assumption that long sections can simply be treated
  as fully developed.
- Keep the output machine-readable so future model-building work can use it
  directly.

## Main source stack used

- Literature-review evidence tables:
  - `correlation_table.csv`
  - `implementation_ready_recommendations.csv`
  - `modeling_decision_memo.csv`
- Literature-review prose anchors:
  - friction / apparent-friction chapter
  - June 18 larger overlap chapter
- Repo-local modeling anchors:
  - June 19 closure-to-modeling handoff
  - June 19 blocker report and 1D implementation spec
  - June 19 Salt dependency package v3
  - June 18 Salt thermal surface ranking
  - June 17 nondimensional dashboard
  - June 15 boundary-modeling report
  - June 2 1D discrepancy report

## Decisions made in the package

- Kept the first defended model explicitly hybrid:
  - straight defended hydraulic closures where current evidence supports them
  - `UA'(x)` as the primary thermal state surface
  - `HTC(x)` as the secondary surface
  - direct `Nu(Re)` only on `left_lower_leg`
  - residual buckets for blocked feature and unsupported return-path behavior
- Refused to promote feature `K_eff` because the retained-time full-path hydro
  integral is still missing.
- Refused to promote live cooler-side `h` as a defended 1D input because the
  readable 3D boundary is fixed sink `Q`, not a directly readable convective
  `h` control.
- Kept Salt and Water separate in the current handoff because Water remains
  readiness-only.

## Durable outputs

- Added:
  - `reports/2026-06-19_ethan_litrev_to_1d_modeling_handoff/README.md`
  - `summary.json`
  - `closure_crosswalk.csv`
  - `segment_closure_policy.csv`
  - `nondimensional_group_spec.csv`
  - `required_future_cfd_observables.csv`
  - `report_outline.md`
  - `writing_checklist.md`
  - `open_questions.md`
- Also added:
  - `imports/2026-06-19_ethan_litrev_to_1d_modeling_handoff.json`
  - `journals/2026-06/2026-06-19_ethan_runs.md`

## Follow-on execution layer added the same day

- Reopened the same claimed report root to convert the package from a closure
  handoff only into a dual-path implementation brief.
- Added:
  - `dual_path_execution_report.md`
  - `correlation_registry.csv`
  - `shared_closure_bundle_contract.csv`
  - `rom_test_matrix.csv`
  - `dual_path_workstreams.csv`
- Updated the package README, checklist, open questions, summary JSON, import
  manifest, and curated journal entry so the new execution layer is visible in
  both human-facing and machine-readable provenance.

## New decisions from the execution layer

- The answer to "can we start?" is yes for Salt CFD-informed ROM analysis.
- The first executable path should be the current `Fluid` solver because it
  already has replay-capable diagnostics, calibration entrypoints, and tests.
- The second path should be a clean solver named `salt_cfd_rom`, but it must
  consume the same closure bundle rather than a divergent hand-tuned dataset.
- The first-pass scorecard should remain CFD-only.
- `K_eff` remains readiness-only even in the execution plan; the report now
  codifies the blocker into the shared bundle contract instead of turning it
  into an implied future coefficient table.

## Limits preserved explicitly

- Fully developed friction and fully developed `Nu` remain baseline references,
  not universal section closures.
- Entry / redevelopment logic remains sensitivity-only until a cleaner reset
  contract is published for the affected transitions.
- Boundary-layer ratios remain diagnostic-only.
- Feature `K_eff` still needs a new extractor, not just more runtime.

## 2026-06-19 Follow-On Plan And Monday Handoff

- Reopened the same claimed writer scope after the user clarified the next
  modeling direction:
  - friction may depend on `Nu`, `Re`, `Pr`, and buoyancy-aware terms
  - `Nu` may depend on `Re`, `Pr`, friction state, and development location
- Chose to translate that into a development-aware nondimensional closure plan
  instead of jumping directly into unsupported coupled fit claims.

### Queue check

- Verified active continuation status with:
  - `sacct -j 3244950,3244951,3244952,3244953,3244954,3244955,3244956,3244957 --format=JobID,JobName%30,State,Elapsed,Start,End`
- Observed:
  - running:
    - `3244950` Salt 3 Jin continuation
    - `3244951` Salt 2 Jin continuation
    - `3244952` Water 3 continuation
    - `3244953` Water 1 continuation
    - `3244954` Salt 4 Jin continuation
    - `3244956` Water 4 continuation
    - `3244957` Water 2 continuation
  - completed:
    - `3244955` Salt 1 Jin continuation

### Submission decision

- Did not launch an additional weekend CFD submission from this task.
- Why:
  - the active June 18 continuation wave is already the highest-priority CFD
    action for straight retained-time hardening and Water readiness
  - the June 19 blocker package already records the first justified follow-on
    bracket as the submitted Salt 2 / Salt 4 heater-plus-insulation child wave
  - the same blocker plan says to defer the Salt 3 Jin midpoint bracket until
    the first bracket wave clears
  - no new Water scenario wave and no feature `K_eff` DOE are justified yet

### New durable file

- Added:
  - `reports/2026-06-19_ethan_litrev_to_1d_modeling_handoff/development_aware_closure_plan.md`

### Main planning decisions added there

- Fit normalized closure residuals first:
  - `phi_f = f_D / (64 / Re)`
  - `phi_nu = Nu / Nu_ref`
- Start with nondimensional inputs:
  - `Re`
  - `Pr`
  - `Ri = Gr / Re^2`
  - `Gz`
  - development distance from the last reset normalized by `D_h`
  - branch/reset class
- Use a staged fit order:
  - hydraulic development family first
  - uncoupled direct thermal family second
  - hydraulically informed thermal family third
  - shared latent development-amplitude family as the fallback if the separate
    fits are unstable
- Preserve the same boundary:
  - Salt only
  - no promoted feature `K_eff`
  - no Water dependency fit
  - no right-leg direct thermal law

### Monday todo that must survive

- Freeze the reset-coordinate contract for hydraulic and thermal development.
- Open the separate 1D code-workspace task for:
  - current `Fluid` replay/import lane
  - clean `salt_cfd_rom` skeleton
- Build a small closure-family harness for:
  - `F1`
  - `T1`
  - `T2`
  - `LT1`
- Keep Monday presentation prep focused on:
  - why fully developed values are references rather than defaults
  - what is admitted now
  - what remains blocked
  - why the current weekend queue is already the right CFD action

## 2026-06-22 Queue-State Refresh

- Reopened the same claimed writer scope only to refresh stale runtime-facing
  prose after the June 19 queue evolved.
- Rechecked the relevant 3D jobs with:
  - `squeue -j 3244950,3244951,3244954,3244957,3246561,3246564,3250524,3250525,3250526`
  - `sacct -j 3244950,3244951,3244952,3244953,3244954,3244955,3244956,3244957,3246561,3246562,3246563,3246564,3246927,3250524,3250525,3250526 --format=JobID,JobName%24,State,ExitCode,Elapsed,Start,End`

### Observed June 22 runtime state

- Running:
  - `3244950` Salt 3 Jin continuation
  - `3244951` Salt 2 Jin continuation
  - `3244954` Salt 4 Jin continuation
  - `3244957` Water 2 continuation
  - `3246561` Salt 2 high-Q/high-insulation bracket child
  - `3246564` Salt 2 low-Q/low-insulation bracket child
  - `3250524` repaired Salt 4 high-Q/high-insulation bracket child
  - `3250525` repaired Salt 4 low-Q/low-insulation bracket child
- Pending:
  - `3250526` repaired packed optimum-insulation wave
- Completed:
  - `3244955` Salt 1 Jin continuation
- Failed or timed out:
  - `3246562` initial Salt 4 high-Q/high-insulation bracket child failed
  - `3246563` initial Salt 4 low-Q/low-insulation bracket child failed
  - `3246927` initial packed optimum self-stage job failed
  - `3244952`, `3244953`, `3244956` timed out Water continuations

### Interpretation boundary kept explicit

- The June 22 runtime refresh changes queue truth, not closure truth.
- The repaired Salt 4 relaunches show the earlier issue was launch hygiene
  rather than a new scientific blocker in the Salt-only scenario definition.
- The Water timeouts strengthen the current caution around Water readiness, but
  they do not revoke the already-admitted Salt-only 1D handoff boundary.
