---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/val_salt2_patch_heat_ledger.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/pressure_corner_k_admission_table.csv
  - registry/salt2/native_2d_cfd_external/salt_test_2/val_salt_test_2_coarse_mesh_laminar/aggregates/postprocessing.sqlite
tags: [val-salt2, heat-audit, pressure-k, external-test, scientific-review]
related:
  - .agent/status/2026-07-17_AGENT-483.md
  - imports/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock.json
task: AGENT-483
date: 2026-07-17
role: Implementer/Tester/Writer
type: journal
status: complete
---
# val_salt2 Training Readiness and Corner-K Unlock

## Why this exists

The user asked what `salt2_val` / `val_salt2` still needs before it can be main
evidence or training, and why pressure corner K remains diagnostic. This task
implements that audit completely from existing harvested/postprocessed outputs,
without duplicate pressure jobs.

## Observed output

The `val_salt2` registry aggregate database contains patch-level
`wall_heat_flux` rows. The new ledger extracts `69` patch entities, including
`21` junction/stub entities and zero-gradient NCC connector rows. Section
reconciliation passes against the July 15 ledger. The all-patch net is
`0.1930623451 W`, matching `total_Q_postProc` within `3.451e-07 W`.

The junction/stub split is:

- lower-left: `8.156929503 W`
- lower-right: `8.007968534 W`
- upper-left: `9.935959167 W`
- upper-right: `14.8252293652 W`

Upper-right remains the largest junction/stub loss bucket, consistent with the
Salt2-4 mainline pattern from AGENT-473.

For pressure corner K, the current joined evidence has `12` preserved corner
rows across Salt2/Salt3/Salt4, `0` admitted rows, and `12` negative
`K_local_centerline` values after using the July 14 centerline tap-length
refresh. The centerline subtraction does not prove negative physical corner K;
it proves the current straight-loss reference/tap construction over-subtracts
the preserved feature pressure loss.

## Interpretation

`val_salt2` is now strong enough as external-test target evidence: patch-level
thermal data exist, section sums close, junction/stub split closes, and BC/source
material provenance is available. It is still not legal training input under the
AGENT-481 canonical split. Using it for fitting would spend the blind external
test and should require an explicit future reclassification.

Pressure corner K remains diagnostic because all required fit gates do not pass
together: recirculation blocks ordinary single-stream branch rows, pressure
definition conflicts remain, straight-loss subtraction is not physically local
enough, and no same-QOI mesh/GCI admission exists.

## Next task sequence

1. Use this `val_salt2` package for blind external scoring once the predictive
   model is ready.
2. If the team wants to train on `val_salt2`, create a split-policy row that
   explicitly reclassifies it away from external-test status.
3. For corner K, do not tune the 1D model from current K values. Unlock requires
   new or repaired extraction with admitted pressure basis, taps outside
   recirculation, a local straight reference that does not over-subtract, and
   mesh/GCI for the same corner-loss QoI.

## Commands

- `python3.11 -m py_compile tools/analyze/build_val_salt2_training_readiness_and_corner_k_unlock.py tools/analyze/test_val_salt2_training_readiness_and_corner_k_unlock.py`
- `python3.11 -m unittest tools.analyze.test_val_salt2_training_readiness_and_corner_k_unlock`
- `python3.11 tools/analyze/build_val_salt2_training_readiness_and_corner_k_unlock.py`

## Do-not-do guardrails

- Do not submit duplicate pressure ladder jobs.
- Do not mutate native solver outputs or registry state.
- Do not feed realized `wallHeatFlux` into predictive runtime logic.
- Do not promote pressure corner K into Fluid until the admission table has
  actual fit-admitted rows.
