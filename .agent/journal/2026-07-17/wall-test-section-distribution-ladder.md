---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_coupled_admission/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_wall_layer_drive_mapping/external_bc_drive_table.csv
  - work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/external_bc_segment_equivalents.csv
tags: [journal, AGENT-498, wall-circuit, test-section, heat-placement]
related:
  - .agent/status/2026-07-17_AGENT-498.md
  - predictive-wall-test-section-submodels
task: AGENT-498
date: 2026-07-17
role: Implementer/Tester/Writer
type: journal
status: complete
---
# Wall/Test-Section Distribution Ladder

## Why This Exists

AGENT-494 showed that PB1 passive-total hA scaling can improve mdot versus M3
while sharply worsening TP/TW/all-probe temperature RMSE. That means the next
scientific question is not total heat removal, but local heat placement.

## Implementation

AGENT-498 adds `tools/analyze/build_wall_test_section_distribution_ladder.py`
and `tools/analyze/test_wall_test_section_distribution_ladder.py`.

The dry-run package emits:

- segment/role heat-placement audit from setup external-boundary rows;
- AGENT-494 probe-shape regression audit versus M3;
- two Salt2-trained local wall candidates;
- static/runtime gates;
- 12 coupled scenario contracts pairing each wall candidate with lumped and
  N16 segmented HX models across Salt2/Salt3/Salt4.

The two local wall candidates are:

- `PB2_salt2_local_shape_passive_hA_p1`
- `PB3_upcomer_test_section_attenuated_shape_p1`

Both use Salt2-only training information. Salt3/Salt4 wall/probe/flux evidence
is scoring-only and is not used in runtime contracts.

## Coupled Result

Latest coupled Fluid scoring was run as a foreground compute-node replay in
this session. The first non-overlap `srun` attempt could not create a job step
because the allocation was busy and was cancelled before writing scoring
output. The completed replay was:

`srun -N1 --overlap -n1 python3 tools/analyze/build_wall_test_section_distribution_ladder.py --run-fluid --timeout-seconds 273`

The package was then refreshed without another Fluid launch:

`python3 tools/analyze/build_wall_test_section_distribution_ladder.py --reuse-existing-coupled --timeout-seconds 273`

The coupled scorecard has `12/12` completed rows with accepted roots. No
candidate is admitted. PB2 and PB3 both preserve the desired mdot direction,
but fail because all-probe/TW RMSE remains much worse than M3.

The probe-level evidence is now regenerated for the current PB2/PB3 candidate
set, replacing stale D0-D4 probe tables from an earlier overwritten pass. The
package contains `204` coupled probe localization rows, `136` validation/holdout
probe-delta rows, and `80` role/segment summaries. Among comparable probes,
`106` fail vs M3 and `14` pass; `16` are explicitly labeled `not_compared`
because M3 has no sensor prediction. The largest compared regressions localize
to Salt4 TW heated-incline sensors, especially TW5/TW6.

The directory still contains legacy extra files `admission_review.csv` and
`coupled_distribution_scorecard.csv` from the earlier overwritten D0-D4 package
state. They were not deleted because cleanup was not requested; the canonical
AGENT-498 evidence is the file list in the generated README, manifest, and
summary.

Representative rows:

- PB2 validation all-probe RMSE `53.2089137 K` vs M3 `17.749 K`; TW
  `61.72786766 K` vs M3 `19.332 K`.
- PB3 holdout all-probe RMSE `58.22289604 K` vs M3 `16.971 K`; TW
  `67.2998088 K` vs M3 `18.623 K`.

## Next Work

Do not spend the next pass on another passive external hA redistribution. The
useful next candidate must attack temperature-shape physics directly: local wall
temperature drive, heater/source placement, axial mixing/upcomer thermal
stratification, or test-section wall/fluid coupling. Keep the same split rule:
Salt2 fit only; Salt3 validation; Salt4 holdout; no realized validation/holdout
wallHeatFlux, mdot, cooler duty, test-section heat, wall temperature, or probe
temperature as runtime inputs.
