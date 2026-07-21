---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/RUNNING.md
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/raw_endpoint_pressure_velocity.csv
  - tools/analyze/build_two_tap_staged_endpoint_sampler.py
tags: [pressure-ledger, two-tap, raw-endpoints, scheduler]
related:
  - .agent/status/2026-07-18_TODO-TWO-TAP-ENDPOINT-RESUBMIT-HARVEST.md
  - imports/2026-07-18_two_tap_endpoint_resubmit_harvest.json
  - .agent/blockers.yml
task: TODO-TWO-TAP-ENDPOINT-RESUBMIT-HARVEST
date: 2026-07-18
role: Hydraulics/cfd-pp/Scheduler/Implementer/Tester/Writer
type: journal
status: complete
---
# Two-Tap Endpoint Resubmit Harvest

## Attempted

Claimed a new scheduler row because the prior launch row explicitly forbade a
third submission. Validated the regenerated staged-copy runner, submitted one
new `two_tap_ep` job through `login3`, monitored all three case stages, and
harvested the raw endpoint VTKs after repairing the parser.

## Observed

Job `3302464` progressed past both prior staging failures. Salt2, Salt3, and
Salt4 each reconstructed the target time and ran `foamPostProcess` on the
task-owned staged copy. All six expected VTK files were written under
`tmp/2026-07-18_two_tap_staged_endpoint_sampler/staged_reconstructed/**`.

The batch still ended as `FAILED` `1:0` because the old Python parser assumed
one polygon per line and scalar/vector sections, while OpenFOAM wrote wrapped
`POLYGONS` connectivity and `FIELD attributes` cell data.

## Inferred

The remaining failure after resubmission was not a CFD/OpenFOAM sampling
failure. It was a harvest parser format gap. Reading the declared polygon
connectivity count and parsing `FIELD attributes` arrays is sufficient for the
OpenFOAM VTK files written by this sampler.

## Result

After the parser fix, local harvest from the staged VTKs produced six sampled
rows in `raw_endpoint_pressure_velocity.csv`. Each row remains diagnostic raw
sample evidence only, with `fail_recirculation` and
`raw_sample_only_no_component_k_admission` labels. The blocker
`two-tap-raw-endpoint-sampling-pending` is resolved only for raw endpoint
surface availability.

## Next Useful Actions

Open a separate pressure/velocity basis audit task. That task should compute
loss terms from the six sampled rows, retain the recirculation evidence, and
keep straight-reference/component isolation, same-QOI UQ, F6, and component-K
admission as explicit downstream gates.
