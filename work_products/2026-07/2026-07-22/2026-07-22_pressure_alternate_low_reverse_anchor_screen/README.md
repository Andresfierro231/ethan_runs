---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_pressure_low_recirc_nonrecirc_anchor_inventory/anchor_inventory_gate.csv
  - work_products/2026-07/2026-07-17/2026-07-17_f6_anchor_first_refinement/anchor_gate_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_predict_salt_pm10_terminal_admission/pm10_recirc_onset_summary.csv
tags: [pressure, f6, low-reverse-anchor, no-launch, no-admission]
related:
  - .agent/status/2026-07-22_TODO-PRESSURE-ALTERNATE-LOW-REVERSE-ANCHOR-SCREEN-2026-07-22.md
  - .agent/journal/2026-07-22/pressure-alternate-low-reverse-anchor-screen.md
  - imports/2026-07-22_pressure_alternate_low_reverse_anchor_screen.json
task: TODO-PRESSURE-ALTERNATE-LOW-REVERSE-ANCHOR-SCREEN-2026-07-22
date: 2026-07-22
role: Hydraulics/Implementer/Tester/Writer/Reviewer
type: work_product
status: complete
---
# Pressure Alternate Low-Reverse Anchor Screen

Decision: `pressure_alternate_anchor_screen_complete_existing_replacement_not_found`.

This package screens existing pressure evidence after the lower-right two-tap
component-isolation path failed. It treats the lower-right evidence as
section-effective residual evidence and asks whether any existing PM5, PM10,
branch-mask, or inventory row can replace `CAND001`.

Key counts:

- screen rows: `40`
- existing evidence rows: `29`
- future design rows: `11`
- existing replacement-ready rows: `0`
- PM10 strong-recirculation rows: `4`
- future designs preserved without launch: `11`

Primary outputs:

- `alternate_anchor_screen.csv`
- `disqualification_matrix.csv`
- `no_launch_shortlist.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

No scheduler query/action, launch, harvest, sampler/UQ run, fitting, model
selection, component-K/F6/Shah release, source/property release, candidate
freeze, or native-output mutation occurred.
