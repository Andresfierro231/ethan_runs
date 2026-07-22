# OpenFOAM Boundary-Condition Implementation Audit

Generated: `2026-07-09`
Task: `AGENT-240`

## Scope

This package verifies the documented Ethan Salt boundary-condition claims
against actual OpenFOAM dictionaries in the current mainline Salt roots,
corrected Salt-Q roots, and the active Salt 1 nominal continuation root. It
does not run OpenFOAM, reconstruct fields, edit case trees, or mutate native
solver outputs.

## Outputs

- `openfoam_case_boundary_summary.csv`: case-level `0/T` implementation checks,
  latest retained time, radiation-file flags, and comparison to the July 8
  scenario contract where applicable.
- `openfoam_field_boundary_summary.csv`: boundary-condition type counts for
  every root `0/*` field file in each audited case.
- `temperature_patch_inventory.csv`: patch-level `0/T` type, Q, h, Ta,
  emissivity, and thickness-layer inventory.
- `target_q_restart_consistency.csv`: heater/cooler/test-section Q checks for
  root `0/T` and latest retained restart `T` files.
- `claim_verdicts.csv`: documented claim versus implementation verdicts.
- `cleanup_dry_run.csv`: non-destructive cleanup candidate classification.

## Result

Claim checks verified: `6/6`.

The core documented thermal-boundary claims are supported by the implemented
OpenFOAM dictionaries: mainline Salt 2/3/4 use the documented three thermal BC
families in `0/T`, all audited Salt roots carry the `0.03556 m` layer, and
emissivity metadata is present without a detected `radiationProperties`, `qr`,
or `G` field. Corrected-Q root and latest retained restart `T` files were also
checked for target heater/cooler Q values across all 64 processor boundary
blocks.

The audit also surfaces cleanup needs, but destructive cleanup is intentionally
not performed here. The largest cleanup candidates are `tmp/` and
`tmp_extract/`; both need provenance-aware manifests before deletion.
