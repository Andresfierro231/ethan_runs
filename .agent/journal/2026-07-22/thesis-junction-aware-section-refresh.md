---
provenance:
  - reports/thesis_dossier/Chapters_and_sections/current/05_junction_aware_ledgers.md
tags: [journal, thesis, junction-aware-ledger, no-admission]
related:
  - .agent/status/2026-07-22_TODO-THESIS-JUNCTION-AWARE-SECTION-REFRESH.md
  - imports/2026-07-22_thesis_junction_aware_section_refresh.json
task: TODO-THESIS-JUNCTION-AWARE-SECTION-REFRESH
date: 2026-07-22
role: Writer / Reviewer / Hydraulics / Thermal-modeling
type: journal
status: complete
---
# Thesis Junction-Aware Section Refresh

## Attempted

Updated the current junction-aware section with July 22 junction/stub heat,
pressure/energy-basis, heat-loss partition, PASSIVE-H2, pressure-anchor,
upcomer-onset, and mesh-uncertainty outcomes.

## Observed

New evidence sharpens the same conclusion: local ownership lanes are necessary,
but admission remains closed. Current cited values include Salt2-4
junction/stub train-context losses `39.128349537..48.485215891 W`,
`val_salt2` external-test junction/stub loss `40.926087 W`, PASSIVE-H2
corrected radiation `22.4052516482..25.6530978934 W`, full passive operator
`38.6073163603..44.6770586908 W`, pressure replacement-ready rows `0`,
same-QOI pressure UQ-ready rows `0`, component-K/F6 release rows `0`, upcomer
ordinary admissions `0`, exchange admissions `0`, and formal S13 GCI-ready rows
`0`.

## Inferred

The right thesis claim is residual ownership and model-form necessity. The
wrong claim would be coefficient recovery, freeze, final score, or protected
validation.

## Caveats

No blocker register was changed. `.agent/BLOCKERS.md` remains generated and
read-only for this row.

## Next Useful Actions

Use this section as the durable narrative bridge while continuing the actual
unblock work in separate runtime, endpoint, and same-QOI UQ rows.
