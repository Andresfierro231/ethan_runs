# 2026-06-22 Ethan Runs

## Summary

Completed the current repo-local frozen-state and feature-path hardening pass:

- `reports/2026-06-22_ethan_feature_path_hydro_decomposition`
- `reports/2026-06-22_ethan_salt_feature_path_hydraulic_hardening_v2`
- `reports/2026-06-22_ethan_salt_model_dependency_package_v4`
- `reports/2026-06-22_ethan_frozen_state_results`
- `reports/2026-06-22_ethan_frozen_state_roadmap`

## Observed Output

- The new feature-path decomposition proves the preserved raw patch extractor
  already contains an exact retained-time endpoint `p` versus `p_rgh`
  decomposition for every current Salt feature row.
- The path-to-proxy provenance check is exact:
  - `max_path_vs_proxy_delta_p_residual_pa = 0.0`
  - `max_path_vs_proxy_delta_p_rgh_residual_pa = 0.0`
- The refreshed feature hardening pass reopens 21 of 45 feature case rows and
  stabilizes two feature names for model use:
  - `corner_upper_right`
  - `test_section_complex`
- The refreshed Salt dependency package v4 now reports:
  - straight friction: `provisional_defended`
  - feature `K_eff`: `provisional_defended`
  - Salt Nu: `provisional_defended`
- The frozen-state results package now records:
  - retained late-window mean as the primary pseudo-steady basis
  - latest retained time as the sensitivity overlay
  - branchwise drift rollups from mean to latest retained time
  - branch behavior and modeling notes for upcomer versus downcomer
  - readable external Fluid diagnostics as a pre-refresh 1D reference surface

## Inferred Interpretation

- Straight sections are still not being treated as automatically fully
  developed. The admitted hydraulic rows remain bounded CFD-supported straight
  closures on the current Salt subset only.
- The best current direct internal HTC or Nu evidence remains `left_lower_leg`.
- `upcomer` is still a separate modeling problem:
  - it is derived
  - it remains sensitivity-only
  - it should not be treated as just another direct straight Nu branch
- `right_leg` or downcomer remains blocked for direct Nu and needs more
  branchwise retained-time observables.
- The feature-path blocker has been reduced substantially:
  - the repo now has a defended patch-endpoint path decomposition
  - the remaining limitation is the local straight-reference basis, not missing
    endpoint hydro support

## Contradictions And Limits

- The reopened feature `K_eff` basis is still provisional rather than a final
  feature-volume integral closure.
- The readable external Fluid diagnostics are still a stale reference surface:
  they predate the June 22 feature-path reopening and do not count as the
  current post-refresh replay.
- The straight late-window sensitivity refresh still depends on the active
  continuation jobs preserving stronger retained windows.
- LitRev support for a broader developing-flow internal HTC surface has not yet
  been refreshed in the external `papers` repo.

## Scripts And Reproducibility

- Added builders:
  - `tools/analyze/build_ethan_feature_path_hydro_decomposition.py`
  - `tools/analyze/build_ethan_salt_feature_path_hydraulic_hardening_v2.py`
  - `tools/analyze/build_ethan_salt_model_dependency_package_v4.py`
  - `tools/analyze/build_ethan_frozen_state_results_package.py`
- Added tests:
  - `tools/analyze/test_ethan_feature_path_hydro_decomposition.py`
  - `tools/analyze/test_ethan_closure_modeling_v4.py`
  - `tools/analyze/test_ethan_frozen_state_results_package.py`
- The source set for this pass is recorded in:
  - `imports/2026-06-22_ethan_frozen_state_results.json`

## Next Suggested Actions

- Let the current continuation jobs finish, then open the queued straight
  sensitivity refresh (`AGENT-104`).
- Use the frozen-state package as the reference surface for the external Fluid
  rerun (`AGENT-102`).
- Use the roadmap package and board split to keep the external LitRev update
  (`AGENT-101`) disjoint from the 1D replay and continuation refresh lanes.

## Heat-Balance Contract Follow-On

### Observed Output

- The readable Salt 3D cases are not controlled by a live cooler-`h` DOE path.
  `case_config.yaml` still carries cooler metadata, but the authoritative
  cooling branch in `0/T` is fixed `Q` on the cooler and two adjacent reducer
  patches.
- The June 19 Salt bracket children changed lower-heater `Q` and insulation,
  but inherited the parent cooling-branch fixed sinks unchanged.
- The preserved June 10 Salt 2 late-tail ledger still shows that near-zero
  runtime closure is achievable in the current mixed contract
  (`net total = +0.241 W`), but that is an observed late-time result rather
  than a staging invariant.

### Inferred Interpretation

- Past runs were not all balance-by-construction under a strict heater/cooler
  DOE rule.
- The right future bookkeeping is
  `Q_in - Q_lost = 0` with `Q_lost = Q_removed + Q_ambient` at a chosen parent
  late-window reference state.
- For the current fixed-`Q` Salt setup, `Q_removed` must be solved from the
  residual cooling-branch sink needed to preserve that reference-state balance.
- `ambient_proxy_w` must not be added on top of full cooling removal because
  the existing audit semantics already fold cooling-branch excess into that
  proxy.

### Actions Landed

- Added a dedicated contract note:
  `operational_notes/06-26/22/2026-06-22_salt_heat_balance_contract.md`
- Added a short report package:
  `reports/2026-06-22_ethan_heat_balance_contract/`
- Updated the June 18 continuation-wave and June 19 Salt follow-on campaign
  READMEs/TODOs so future Salt DOE children carry an explicit parent
  reference-state heat ledger before submission.

## Balanced Salt Scenario Wave

### Observed Output

- The six June 22 Salt bracket relaunches (`3250778`-`3250783`) all failed the
  stricter reference-state heat gate even before counting the insulation-driven
  ambient-loss drift.
- Their lower-bound parent-ledger residuals were:
  - Salt 2 high-Q: `+26.93 W`
  - Salt 2 low-Q: `-26.21 W`
  - Salt 3 high-Q: `+30.72 W`
  - Salt 3 low-Q: `-28.78 W`
  - Salt 4 high-Q: `+34.13 W`
  - Salt 4 low-Q: `-33.39 W`
- The packed optimum-insulation node `3250784` also lacked a defensible
  `< 2 W` 3D staging guarantee because the measured-state wall-loss optimizer
  is not the same object as the readable 3D sectionwise heat ledger.

### Actions Landed

- Canceled bracket jobs `3250778`-`3250783` and the insulation-only packed job
  `3250784`.
- Rebuilt the six bracket roots in place to:
  - restore baseline insulation
  - keep the `+/-10%` heater mutation
  - solve the cooling-branch fixed sinks from the parent reference-state
    residual
- Repacked the corrected bracket family as:
  - `3251883` `ethan_salt_hiqbal3`
  - `3251884` `ethan_salt_loqbal3`

### Interpretation

- The queue now matches the stricter Salt scenario steady-state contract much
  better than the earlier visible-control heater+insulation relaunches.
- The optimum-insulation wave remains scientifically interpretable as a
  measured-state wall-loss clue, but it is not currently a runnable strict-gate
  3D scenario family.
