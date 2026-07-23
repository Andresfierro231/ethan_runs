---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_clean_sampler_gci_readiness/face_lane_contract_inventory.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_clean_sampler_gci_readiness/gci_go_no_go_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_clean_sampler_gci_readiness/clean_next_run_contract.csv
tags: [journal, s13, sampler, mesh-gci, readiness]
related:
  - .agent/status/2026-07-22_TODO-S13-CLEAN-SAMPLER-GCI-READINESS-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_clean_sampler_gci_readiness/README.md
  - imports/2026-07-22_s13_clean_sampler_gci_readiness.json
task: TODO-S13-CLEAN-SAMPLER-GCI-READINESS-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# S13 Clean Sampler/GCI Readiness

## Attempted

I took the next non-overlapping S13 action while the endpoint geometry recovery
row is active. The pass audited the old failed medium/fine sampler, the later
successful split rerun, and the current coarse/GCI disposition.

## Observed

The old sampler package is stale failure evidence: it has `0` terminal rows,
`0` exact-label QOI rows, and `6` sampling errors. Its face CSV headers show
partial repair only: `9/18` face lanes pass the local header audit, and the
ready lanes are concentrated in Salt2 plus Salt3 medium.

The later split rerun is the current medium/fine evidence: `6` successful
case-mesh pairs, `18` terminal reductions, `72` exact-label QOI rows, and `0`
sampling errors. That means a duplicate medium/fine rerun is not the next clean
action unless input contracts change.

## Inferred

The current S13 blocker is no longer medium/fine exact-label availability. It
is strict same-label coarse equivalence and then formal GCI disposition. The
endpoint-face recovery row remains separate and should handle throughflow
endpoint release masks.

## Caveats

This row did not run Slurm, mutate native outputs, regenerate sampler outputs,
release Qwall/source-property values, or admit formal GCI. The face-lane audit
uses package CSV headers as evidence, not native OpenFOAM files.

## Next Useful Actions

1. Resolve strict same-label coarse equivalence, or document a final no-go for
   formal GCI.
2. Continue the active endpoint-face geometry release-mask recovery row for
   throughflow endpoint masks.
3. Keep production harvest and exchange coefficient admission closed until
   coarse/GCI, endpoint geometry, and source/property/cp gates all pass.
