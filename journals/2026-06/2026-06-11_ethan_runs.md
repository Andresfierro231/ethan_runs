# Ethan Runs Update

Date: 2026-06-11

## Observed Outputs

- Added `reports/2026-06-11_salt2_rigor_repair_methods_note/README.md`.
- The new note reuses the completed June 11 internal brief plus the June 10
  Salt 2 case-analysis package and recent June 9-10 journal/report context.
- The note records the current report-path blockers without regenerating the
  underlying Salt 2 package.

## Interpretation

- The current Salt 2 package is still useful, but it remains a package with an
  interpretation boundary, not a fully settled manuscript result.
- The highest-priority next step is not "make the figures look cleaner." It is
  to harden the package semantics so summary-level direct-pressure claims cannot
  silently inherit invalid terminal rows.
- The next-most-important step is a narrow hydraulic diagnosis of
  `left_upper_leg` and `upper_leg`, because those spans still carry the largest
  direct-versus-shear disagreement even after the centerline repair.
- Thermal tightening should stay downstream of that hydraulic cleanup, because
  the present HTC / `UA'` products are still support-gated indicators and the
  validation anchor still lags the live heat tail.

## Contradictions / Caveats

- `major_loss_summary.csv` still reports direct-terminal `p_rgh` `nan` values
  for `left_upper_leg` and `upper_leg` even though valid direct bins exist
  immediately before terminal `missing_wall_faces` rows in the cumulative
  timeseries.
- All six major spans remain `warning_heavy`; the no-quarantine package state
  should not be misread as a full hydraulic clean bill of health.
- The current thermal package still masks or flags about `15%` of streamwise
  rows, so local thermal-coefficient language must remain qualified.
- The live heat tail remains newer than the carried direct-validation reference.

## Suggested Next Actions

- Harden the package summary logic first, then rebuild from script and rerun a
  reviewer pass before any stronger report-language refresh.
- If the rebuilt package still shows the upper-span disagreement, do a
  span-focused diagnosis on `left_upper_leg` and `upper_leg` with robust
  statistics and endpoint-validity checks rather than weakening the caveat
  language.
- Refresh the direct-validation anchor only after the hydraulic path is stable
  enough that the thermal story is not being reinterpreted at the same time.

## Checkpoint / Stopping Point

- The current stopping point is the new rigor note in
  `reports/2026-06-11_salt2_rigor_repair_methods_note/`.
- That note is intended to constrain later writing discipline: preserve the
  package contradictions, fix semantics before tightening claims, and prefer
  slower reproducible progress over cosmetically cleaner but less honest output.

## Review Gate Checkpoint

- A focused Salt 2 reviewer pass was completed against the June 10 final
  package plus the June 11 hardening slices.
- That gate accepted the current package for constrained internal report use,
  but it did not clear reusable-script rollout.
- The blocking issue was thermal reproducibility on raw reuse: hydraulic data
  rebuilt from frozen `7483-7487 s` artifacts, but heat accounting still
  regenerated from the live continuation and drifted to the newer heat tail.

## Post-Gate Fix

- The next bounded fix was completed in the package builder rather than in
  report prose.
- Raw-reuse builds now require frozen package heat artifacts adjacent to the
  supplied `raw_extraction/` directory and reuse those artifacts directly.
- The rebuilt raw-reuse smoke package now keeps `heat_latest_time_s = 7506 s`
  instead of drifting to the live continuation tail, while still rejecting
  mismatched hydraulic raw-summary metadata early.

## Updated Next Actions

- Rerun the reviewer gate on the new raw-reuse behavior before opening any
  broader Salt-family rollout task.
- If that reviewer pass clears the heat-reproducibility issue, the next
  remaining rollout boundary is the status of `flow_direction_sign_hint`:
  either validate it against extracted evidence or explicitly demote it from
  rollout acceptance criteria while keeping the assumption documented.

## Direction-Sign Boundary

- The rerun reviewer pass closed the heat-reproducibility blocker.
- The remaining rollout boundary is no longer hidden in reviewer prose only:
  `flow_direction_sign_hint` is now being treated as a manual profile
  assumption that aligns flux with the declared local span coordinate.
- The current pipeline still does not infer or independently validate direction
  automatically, so rollout must preserve that limitation explicitly instead of
  implying a stronger solved-direction capability.

## Salt 2 Rollout Gate

- With the manual direction-sign assumption now explicit in both machine-readable
  outputs and report-facing checkpoint prose, the Salt 2 hardening gate is
  clear enough to move into the first Salt-family rollout candidate.
- Residual metadata drift around live `history_time_end_s` remains documented,
  but it is not currently changing the frozen hydraulic or thermal evidence used
  by the reused package.

## Salt 1 Jin Rollout Checkpoint

- The first Salt-family rollout candidate, `viscosity_screening_salt_test_1_jin_coarse_mesh`,
  now resolves under the shared hardened profile contract as
  `salt1_jin_case_v1`.
- A complete frozen raw extraction and a full raw-reuse package rebuild were
  completed successfully:
  - `tmp/2026-06-11_salt1_jin_raw/major/`
  - `tmp/2026-06-11_salt1_jin_case_analysis_package/`
- The first retained Salt 1 Jin package uses hydraulic time `3229 s` and heat
  tail `3230 s`, carries validated raw-reuse provenance, and keeps the manual
  direction-sign limitation explicit in both manifest and summary outputs.

## Salt 1 Jin Gate Notes

- The rollout blocker was not compatibility. The case geometry, NCC patch
  family, mdot monitors, and required fields all matched the hardened contract.
- The main operational cost is the thermal kernel. The longest stage is the
  `foamPostProcess` cut-plane batch inside the major extractor, not profile
  resolution or raw-reuse validation.
- The first one-time Salt 1 Jin package reports:
  - `379` major/thermal streamwise rows
  - `152184` wall-face samples
  - `57` thermal support-flagged bins
  - negative minor residuals on `corner_lower_left`, `corner_lower_right`, and
    `test_section_complex`

## Next Reviewer Gate

- The next gate is a focused reviewer pass on
  `tmp/2026-06-11_salt1_jin_case_analysis_package/**`.
- That review should decide whether the first Salt-family rollout candidate is
  scientifically acceptable enough to continue to the next planned case, or
  whether Salt 1 Jin exposes a bounded new hardening task first.

## Salt 1 Jin Reviewer Gate

- The first Salt-family reviewer gate did not find a new profile or raw-reuse
  incompatibility.
- It did find one bounded rollout boundary: the current Salt 1 Jin artifact is
  only a one-time retained smoke at `3229 s`, while the case has a larger
  stable late retained window available.
- To keep the rollout scientifically aligned with the Salt 2 acceptance
  standard, Salt 1 Jin now needs one remediation only: rebuild on the full
  retained late window before deciding whether the family rollout can continue.

## Salt 1 Jin Full-Window Rebuild

- The bounded remediation is complete. Salt 1 Jin now has a full retained
  late-window package at `tmp/2026-06-11_salt1_jin_case_analysis_package_window4/`
  with hydraulic times `3226-3229 s`.
- The late-window package preserved the same caveat structure as the one-time
  smoke, but it removed the reviewer objection that the first rollout artifact
  was too shallow to compare fairly against the Salt 2 reference path.

## Salt 1 Jin Rerun Gate

- The rerun reviewer gate is clear enough to continue to the next Salt-family
  case.
- No new profile-contract or provenance blocker appeared when Salt 1 Jin was
  rebuilt on the full late window.
- The remaining caution is operational rather than conceptual: the thermal
  kernel is expensive, so broader rollout should keep recording runtime cost
  explicitly while preserving the existing hydraulic/thermal caveats.

## Parallelization and Slurm Gate

- The current rollout can be split operationally, but not scientifically.
- Safe parallel work:
  - read-only compatibility audits on upcoming Salt-family cases
  - dry-run emission of Slurm scripts for long package builds
  - distinct package builds that write to isolated output directories and do
    not overlap active code-edit scopes
- Work that remains sequential:
  - reviewer-gated promotion from one Salt-family case to the next
  - shared-script edits in the package builder, extractors, and profile
    contract
- Added a reusable submission helper at
  `tools/analyze/submit_ethan_case_analysis_package_sbatch.sh` for long
  `build_ethan_case_analysis_package.py` runs.
- Dry-run validation succeeded for the active Salt 1 Kirst full-window late
  build using retained times `3276-3279 s`.
- A live submission probe on a light Salt 2 raw-reuse rebuild established an
  environment boundary rather than a script bug: `sbatch` is not available on
  the current compute node and reports that submission must happen from a login
  node.
- The wrapper now treats missing or nonnumeric Slurm job IDs as failure, so the
  submission boundary is explicit in machine-visible behavior instead of hidden
  behind a blank `job_id` line.

## Salt 1 Kirst Blocker Checkpoint

- Salt 1 Kirst reached the expected retained late window at `3276-3279 s` and
  the first full-window package build started from a valid frozen snapshot.
- That build did not reach the reviewer gate. It stopped after writing
  `analysis_manifest.json` and an empty `raw_extraction/` package directory.
- The issue is not missing thermal surfaces. The keyed temp extract case under
  `tmp_extract/ethan_streamwise_friction/viscosity_screening_salt_test_1_kirst_coarse_mesh/70cc0c653ace4e30/`
  contains `streamwiseBulkThermal` outputs for `3276`, `3277`, `3278`, and
  `3279`, and the `3279` surface count matches the successful Salt 1 Jin late
  run at `379` surfaces.
- The bounded blocker is therefore inside the Python-side reduction path after
  `foamPostProcess`, not in the case-profile contract, not in frozen-snapshot
  creation, and not in OpenFOAM surface emission itself.
- A `--skip-extraction` rerun against the already-generated Salt 1 Kirst
  thermal outputs still failed to write the first major-loss CSV within several
  minutes, which is strong evidence that the thermal-kernel parse / connected-
  region / aggregation stage needs a narrow fix before the rollout can return
  to review.

## Salt 1 Kirst Blocker Resolution

- The initial Salt 1 Kirst blocker diagnosis was directionally useful but too
  strong. The package was not scientifically invalid; the problem was that the
  long thermal reduction stage was silent enough to look dead, and the major
  extractor could not reuse already-generated `streamwiseBulkThermal` outputs on
  rerun when `--skip-extraction` was not set.
- The bounded reusable-script fix landed in
  `tools/extract/sample_leg_centerline_major_loss.py`:
  - the cross-section thermal reduction now reports progress by retained time
    and processed surface count
  - the major extractor now reuses complete `streamwiseBulkThermal` outputs on
    rerun instead of regenerating them unconditionally
- A resumed full Salt 1 Kirst package build then completed cleanly on the same
  `3276-3279 s` retained window and refreshed the package outputs.

## Salt 1 Kirst Reviewer Gate

- Salt 1 Kirst now clears the same caveated late-window rollout standard used
  for Salt 1 Jin.
- The package keeps the accepted limitation structure:
  - no quarantined spans, but all major spans remain `warning_heavy`
  - `left_upper_leg` and `upper_leg` still show large direct-vs-shear
    disagreement and must stay caveated
  - negative feature residuals remain on `corner_lower_left`,
    `corner_lower_right`, and `test_section_complex`
  - `flow_direction_sign_hint` remains an explicit manual profile assumption,
    not an inferred direction rule
  - streamwise thermal products remain effective support-gated indicators, with
    `228` flagged bins
- With those caveats preserved, the rollout may continue to the next planned
  Salt-family case.

## Salt 2 Jin Rollout Checkpoint

- The next Salt-family rollout candidate,
  `viscosity_screening_salt_test_2_jin_coarse_mesh`, matches the same shared
  geometry and monitor naming contract used by the prior Salt-family cases.
- Stable retained late hydraulic times are available at `2428-2431 s`.
- The shared hardened case-analysis profile now registers this case as
  `salt2_jin_case_v1`.

## Salt 2 Jin Reviewer Gate

- The retained-window package finished at
  `tmp/2026-06-11_salt2_jin_case_analysis_package_window4/` with hydraulic
  times `2428-2431 s` and heat tail `2432 s`.
- Salt 2 Jin clears the same caveated late-window rollout standard used for
  Salt 1 Jin and Salt 1 Kirst.
- The package keeps the accepted limitation structure:
  - no quarantined spans, but all six major spans remain `warning_heavy`
  - `left_upper_leg` and `upper_leg` still show the strongest
    direct-vs-shear disagreement and must stay caveated
  - negative feature residuals remain on `corner_lower_left` and
    `corner_lower_right`
  - `flow_direction_hints` remains an explicit manual profile assumption, not
    an inferred direction rule
  - streamwise thermal products remain effective support-gated indicators, with
    `224` flagged bins and explicit `-nan` sanitization provenance
- With those caveats preserved, the rollout may continue to the next planned
  Salt-family case, `viscosity_screening_salt_test_2_kirst_coarse_mesh`.
