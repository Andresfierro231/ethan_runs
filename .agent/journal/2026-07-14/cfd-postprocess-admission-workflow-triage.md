---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_cfd_postprocess_admission_workflow_triage/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission/stopped_salt2_salt4_pm5q/status_table/selected_corrected_q_status_table.csv
  - jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/campaign_manifest.csv
tags: [cfd-pp, salt-cfd, postprocessing, admission, split-discipline]
related:
  - .agent/status/2026-07-14_AGENT-347.md
task: AGENT-347
date: 2026-07-14
role: cfd-pp / Implementer / Tester / Writer
type: journal
status: complete
---
# CFD Postprocess Admission Workflow Triage

## Observed

The workflow can be automated into five gates: terminal harvest, registered
postprocessing, BC role labeling, steady/operating-point admission, and split
discipline.

The completed harvest job `3295437` has concrete outputs and registry aggregate
paths for:

- `salt2_jin_lo5q_corrected`
- `salt2_jin_hi5q_corrected`
- `salt4_jin_lo5q_corrected`
- `salt4_jin_hi5q_corrected`

The harvest status table marks all four as closure-fit admissible under current
coordinator policy, with the former `too_short` context not an exclusion.

The seven user-named rows are not all the same evidence class. `salt4_jin` is
already an admitted holdout. Salt1 corrected/continued rows need Salt1-specific
admission policy. Legacy Salt4 `balq`/`hiins` rows are historical/diagnostic.

## Interpretation

Training should not be expanded by reclassifying historical `balq`/`hiins`
rows. The immediate useful path is to process the harvested corrected +/-5Q rows
through BC role reduction, admission-matrix refresh, and explicit split policy.

The June 19 campaign manifest shows `salt3_jin_hiq_hiins` as
`hiQ_balQ_baselineIns` with `insulation_delta_in=0.00`, so it is not a valid
true high-insulation construction without a further dictionary-level audit.

`2026-06-01_continuation_candidate` is distinct from current `salt2_jin`.
Future reports should display it as
`val_salt_test_2_coarse_mesh_laminar_continuation`, preserving the original path
for provenance.

## Validation

Ran:

- `python3 tools/analyze/build_cfd_postprocess_admission_workflow_triage.py`
- `python3 -m unittest tools.analyze.test_cfd_postprocess_admission_workflow_triage`

Both passed.

## Next

Open a follow-up cfd-pp row to run the next workflow stage on the four harvested
corrected +/-5Q rows: BC role reduction, admission matrix refresh, and
split-policy labeling. Do not launch duplicate harvest for `3295437`.
