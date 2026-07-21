---
task: TODO-F6-ENDPOINT-PAIR-SAME-QOI-UQ-PREFLIGHT
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: journal
status: complete
---
# F6 endpoint pair same-QOI UQ preflight

Task: `TODO-F6-ENDPOINT-PAIR-SAME-QOI-UQ-PREFLIGHT`

Selected clean interior endpoint pairs for `right_leg` and `test_section_span`, computed available same-QOI section-pressure deltas, and documented that same-QOI time UQ plus raw RAF/RMF remain blockers.

The selected pairs are `right_leg__s03->right_leg__s01` and `test_section_span__s03->test_section_span__s01` for Salt2/Salt3/Salt4. The sign convention is `p_upstream - p_downstream`, set by the measured signed velocity in the section-pressure tables.

Salt2 now has a same-label/same-formula/same-sign coarse/medium/fine section-pressure spread diagnostic. That is useful evidence but not final GCI, because retained time-window provenance and raw reverse-flow metrics are still missing.

No scheduler launch, registry mutation, native CFD-output mutation, F6 fit, or component-K admission was performed.
