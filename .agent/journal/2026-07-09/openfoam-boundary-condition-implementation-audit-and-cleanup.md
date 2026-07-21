# OpenFOAM Boundary-Condition Implementation Audit And Cleanup

Date: `2026-07-09`
Task: `AGENT-240`
Role: Coordinator / Reviewer / Cleaner / Writer

## Prompt

The user asked for a careful verification that documented Ethan-run boundary
conditions match the actual implemented OpenFOAM conditions, followed by a
large cleanup where needed.

## Work Performed

Built a read-only audit script and focused tests:

- `tools/analyze/build_openfoam_boundary_condition_audit.py`
- `tools/analyze/test_openfoam_boundary_condition_audit.py`

Generated the audit package:

- `work_products/2026-07/2026-07-09/2026-07-09_openfoam_boundary_condition_implementation_audit/README.md`
- `work_products/2026-07/2026-07-09/2026-07-09_openfoam_boundary_condition_implementation_audit/openfoam_case_boundary_summary.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_openfoam_boundary_condition_implementation_audit/openfoam_field_boundary_summary.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_openfoam_boundary_condition_implementation_audit/temperature_patch_inventory.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_openfoam_boundary_condition_implementation_audit/target_q_restart_consistency.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_openfoam_boundary_condition_implementation_audit/claim_verdicts.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_openfoam_boundary_condition_implementation_audit/cleanup_dry_run.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_openfoam_boundary_condition_implementation_audit/summary.json`

Also wrote:

- `operational_notes/07-26/09/2026-07-09_repo_cleanup_dry_run.md`
- `imports/2026-07-09_openfoam_boundary_condition_implementation_audit.json`

## Evidence Checked

The audit reads actual OpenFOAM dictionaries, not only prior documentation:

- root `0/*` boundary dictionaries for 20 Salt case roots
- root `0/T` patch-level thermal parameters
- corrected Salt-Q manifest target values
- latest retained corrected-Q restart `processors64/<time>/T` files, scanned
  textually across all 64 processor boundary blocks
- July 8/9 documentation packages used only as claims to verify or as
  admission/status context

## Main Findings

- `claim_verdicts.csv` reports `6/6` verified claims.
- Mainline Salt 2/3/4 root `0/T` files implement the documented thermal
  boundary family counts: `externalTemperature:10`,
  `rcExternalTemperature:36`, and `zeroGradient:23`.
- All 20 audited Salt roots carry the documented `0.03556 m` layer in the
  thermal boundary stack.
- Emissivity exists as `rcExternalTemperature` patch metadata, with no detected
  `constant/radiationProperties` file and no `qr` or `G` field in audited roots
  or latest retained restart time.
- Corrected-Q root dictionaries and latest retained restart dictionaries carry
  the expected heater/cooler Q targets. The restart check required every one of
  the 64 processor boundary blocks to contain the expected value.
- The audit does not promote corrected-Q or Salt 1 nominal continuation rows to
  closure-fit evidence. It preserves the existing admission boundary.

## Cleanup Result

Performed a non-destructive cleanup dry run rather than deleting or moving
large trees. Six candidates were documented in `cleanup_dry_run.csv` and in the
operational note:

- `tmp/`
- `tmp_extract/`
- `reports/2026-06/2026-06-23/2026-06-23_ethan_cfd_freeze_checkpoint`
- `jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/TODO.md`
- `jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/submitted_jobs.csv`
- `work_products/2026-07-06_overnight_postprocess_jobs`

No deletion was performed because repo policy requires explicit approval for
destructive cleanup, and both `tmp/` and `tmp_extract/` may contain provenance
referenced by reports.

## Validation

- `python3.11 -m py_compile tools/analyze/build_openfoam_boundary_condition_audit.py tools/analyze/test_openfoam_boundary_condition_audit.py`
- `python3.11 -m unittest tools.analyze.test_openfoam_boundary_condition_audit`
- `python3.11 tools/analyze/build_openfoam_boundary_condition_audit.py`

## Next Suggested Actions

1. Approve or reject a follow-up manifest pass over `tmp/` and `tmp_extract/`
   before any pruning.
2. Add a README to the June 23 freeze checkpoint package.
3. Add additive status notes for stale campaign status files rather than
   rewriting original submission records.
4. Move `work_products/2026-07-06_overnight_postprocess_jobs` into the sorted
   July work-products layout only after checking active references.
