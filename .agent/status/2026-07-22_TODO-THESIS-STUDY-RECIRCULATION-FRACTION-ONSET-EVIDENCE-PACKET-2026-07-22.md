---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet/recirculation_onset_metric_table.csv
  - work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/shared_velocity_ranges.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight/recirc_segmentation_case_summary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis/s13_exchange_trend_table.csv
tags: [status, thesis-study, recirculation, upcomer, onset, s13]
related:
  - .agent/journal/2026-07-22/thesis-study-recirculation-fraction-onset-evidence-packet.md
  - imports/2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet.json
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet/README.md
task: TODO-THESIS-STUDY-RECIRCULATION-FRACTION-ONSET-EVIDENCE-PACKET-2026-07-22
date: 2026-07-22
role: Hydraulics / cfd-pp / Writer / Reviewer / Tester
type: status
status: complete
---
# TODO-THESIS-STUDY-RECIRCULATION-FRACTION-ONSET-EVIDENCE-PACKET-2026-07-22

## Objective

Start a refreshed recirculation/onset evidence packet from the improved upcomer
composite figures plus S13 evidence. Quantify only defensible values and fail
closed where the source basis is missing.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-22/2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet/`.

Decision:
`recirculation_onset_packet_started_diagnostic_proxies_available_closed_fraction_and_ri_fail_closed`.

Key results:

- velocity figure evidence rows: `3`
- reverse-flow topology proxy rows: `3`
- S9 onset proxy rows: `3`
- S13 exchange/tau current-coarse rows: `3`
- same-QOI temporal UQ boundary rows: `4`
- closed recirculation fraction admitted: `false`
- S13 Richardson number admitted: `false`
- mesh/GCI disposition allowed now: `false`

Quantified diagnostics in `recirculation_onset_metric_table.csv`:

- reverse-candidate fraction of right-leg ROI: Salt2 `0.157702688614`, Salt3
  `0.160299790332`, Salt4 `0.162167108784`
- maximum downward y-velocity common-render visual bound: `0.0770250484347 m/s`
- S13 positive-outward exchange proxy: Salt2 `2.68592194714e-05 kg/s`,
  Salt3 `4.23665968058e-05 kg/s`, Salt4 `7.65896288069e-05 kg/s`
- S13 tau proxy: Salt2 `868.807159089 s`, Salt3 `547.838912867 s`,
  Salt4 `301.390653047 s`

## Changes Made

Added/updated:

- `tools/analyze/build_thesis_study_recirculation_fraction_onset_evidence_packet.py`
- `tools/analyze/test_thesis_study_recirculation_fraction_onset_evidence_packet.py`
- packet tables: metric table, velocity evidence, topology proxy, onset proxy,
  exchange/tau proxy, temporal-UQ boundary, availability gate, figure/table
  targets, claim boundaries, source manifest, guardrails, README, summary
- this status, matching journal, and import manifest

## Validation

- `python3.11 -m pytest tools/analyze/test_thesis_study_recirculation_fraction_onset_evidence_packet.py`:
  passed, `2` tests.
- `python3.11 tools/analyze/build_thesis_study_recirculation_fraction_onset_evidence_packet.py`:
  passed and generated the packet.

## Unresolved Blockers

- Closed recirculation fraction remains blocked because the validated cell-VTK
  segmentation reports fragmented velocity topology, not a closed defensible
  control volume.
- S13 Richardson number remains blocked because no same-window, same-CV
  property/temperature/velocity-length basis was present in the opened sources.
- Medium/fine exact-label rows are pending Slurm sampler job `3310179`.
- Mesh/GCI disposition must not be rerun until those exact-label rows exist.

## Guardrails

Native CFD/OpenFOAM outputs, registry/admission state, blocker register, Fluid
source tree, external repos, and thesis LaTeX/current files were not mutated.
No scheduler action was launched by this evidence packet. No fitting, tuning,
production harvest, source/property release, coefficient admission, ordinary
upcomer `Nu/f_D/K/F6` admission, exchange-cell coefficient admission, final
score, or S11/S12/S13/S15/S6 trigger was performed.
