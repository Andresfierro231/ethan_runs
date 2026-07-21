---
task: AGENT-495
date: 2026-07-17
role: Hydraulics/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
tags: [journal, AGENT-495, upcomer, onset, recirculation]
related:
  - .agent/status/2026-07-17_AGENT-495.md
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_data_sparsity_progress/README.md
---
# Upcomer Onset Data-Sparsity Progress

## Why This Avenue Exists

The current blocker register says `upcomer-onset-data-sparsity` is open because
existing evidence has observed recirculation points but no non-recirculating
anchor and no single-stream fit-admitted row. The immediate risk was misuse:
recirculation diagnostics could be accidentally treated as ordinary `Nu`,
`f_D`, or component `K` evidence.

## Observed Facts

- AGENT-464 records `3` mainline onset points, all
  `observed_recirculation_only`.
- The consolidated AGENT-495 ledger has `68` rows:
  `36` `recirculation_diagnostic` rows and `32`
  `not_admissible_missing_same_window_fields` rows.
- The current ledger has `0` ordinary or conditional `Nu`, `f_D`, or component
  `K` fit rows.
- The current ledger has `0` non-recirculating or transition anchor candidates.
- PM5 readiness rows can include same-window wallHeatFlux/thermal fields, but
  their reverse-flow and Ri evidence still route them to the hybrid/onset lane.

## Interpretation

AGENT-495 narrows the work by completing the row-policy guardrail, not by
closing the blocker. Current upcomer/test-section rows are valid evidence of a
recirculating mixed-convection regime and a validity boundary for ordinary pipe
closures. They are not coefficient-fit evidence.

The next scientific progress must come from a near-onset evidence design or
harvest: at least one non-recirculating or bounded transition anchor, with
same-window pressure, wall/bulk Delta-T, wallHeatFlux, onset metrics, and
mesh/time uncertainty.

## Commands

- `python3.11 -m unittest tools.analyze.test_upcomer_onset_data_sparsity_progress`
- `python3.11 -m py_compile tools/analyze/build_upcomer_onset_data_sparsity_progress.py tools/analyze/test_upcomer_onset_data_sparsity_progress.py`
- `python3.11 tools/analyze/build_upcomer_onset_data_sparsity_progress.py`

## Do Not Do

- Do not fit ordinary upcomer `Nu`, ordinary upcomer `f_D`, or component `K`
  from the current recirculating rows.
- Do not hide recirculation in a global friction multiplier.
- Do not treat `test_section_span` as a separate non-upcomer ordinary-pipe fit
  lane.
