# Repo Cleanup Dry Run

Date: `2026-07-09`
Task: `AGENT-240`

## Scope

This is a non-destructive cleanup record produced during the OpenFOAM
boundary-condition implementation audit. It identifies clutter, stale metadata,
and structure issues that make the Ethan-run workspace harder to reference.

No files were deleted, moved, force-overwritten, or pruned.

## Boundary

The following were intentionally read-only:

- native solver outputs
- Ethan OpenFOAM case trees under `jadyn_runs/**`
- `tmp/**`
- `tmp_extract/**`
- registry and staging state
- scheduler state
- external `../cfd-modeling-tools/**`

## Cleanup Candidates

| Path | Classification | Recommendation | Approval Required |
| --- | --- | --- | --- |
| `tmp/` | Stale but potentially useful | Build a dated manifest by task/subtree, then archive or remove only after owner review. | yes |
| `tmp_extract/` | Stale but potentially useful | Identify report-cited roots before pruning. | yes |
| `reports/2026-06/2026-06-23/2026-06-23_ethan_cfd_freeze_checkpoint` | Under-documented package metadata | Add a README explaining freeze semantics and how CSV/JSON outputs should be used. | no |
| `jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/TODO.md` | Stale coordination note | Add or update a campaign status note; avoid solver-output changes. | no |
| `jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/submitted_jobs.csv` | Stale status metadata | Add a status addendum rather than rewriting initial submission facts. | no |
| `work_products/2026-07-06_overnight_postprocess_jobs` | Misplaced file tree | Move only after reference checks, manifest update, and compatibility symlink. | yes |

## Recommended Order

1. Create manifests for `tmp/` and `tmp_extract/` with owner/task/date/size and
   report-reference status.
2. Add the missing README for the June 23 freeze checkpoint package.
3. Add additive status addenda for the two stale campaign metadata files.
4. Check references to the July 6 overnight postprocess package before moving
   it into the sorted `work_products/YYYY-MM/YYYY-MM-DD` layout.

## Rationale

The workspace contains large scratch and extraction trees that are tempting
cleanup targets, but current reports may still cite them as provenance. A
manifest-first cleanup is slower than broad deletion, but it preserves
traceability and avoids invalidating prior report references.

The audit package records the machine-readable dry-run table at:

- `work_products/2026-07/2026-07-09/2026-07-09_openfoam_boundary_condition_implementation_audit/cleanup_dry_run.csv`
