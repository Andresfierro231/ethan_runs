---
provenance:
  - .agent/BOARD.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_upcomer_onset_anchor_design_and_recirc_fraction_uq/README.md
tags: [status, upcomer, recirculation, onset, uq]
related:
  - .agent/journal/2026-07-22/thesis-study-upcomer-onset-anchor-design-and-recirc-fraction-uq.md
  - imports/2026-07-22_thesis_study_upcomer_onset_anchor_design_and_recirc_fraction_uq.json
task: TODO-THESIS-STUDY-UPCOMER-ONSET-ANCHOR-DESIGN-AND-RECIRC-FRACTION-UQ-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Writer / Reviewer / Tester
type: status
status: complete
---
# Status: Upcomer Onset Anchor Design And Recirculation-Fraction UQ

## Objective

Define the minimum evidence needed to move from observed upcomer recirculation
diagnostics to a defensible onset/recirculation-fraction map.

## Changes Made

- Published
  `work_products/2026-07/2026-07-22/2026-07-22_thesis_study_upcomer_onset_anchor_design_and_recirc_fraction_uq/`.
- Added metric definition, diagnostic evidence, nondimensional regime,
  same-QOI UQ/mesh, ordinary-closure disable, future anchor design,
  figure/table, source manifest, guardrail, summary, and SVG artifacts.
- Recorded this status file, journal entry, and import manifest.

## Outcome

Complete. Decision:
`diagnostic_onset_evidence_ready_closed_fraction_and_admission_fail_closed`.

Current Salt2/Salt3/Salt4 reverse-flow and S13 current-coarse exchange/tau
proxies support a diagnostic onset narrative. Closed recirculation fraction,
same-window same-CV Ri, medium/fine mesh/GCI, production harvest, exchange-cell
coefficient admission, and ordinary upcomer closures remain closed.

## Validation

PASS: `python3.11 work_products/2026-07/2026-07-22/2026-07-22_thesis_study_upcomer_onset_anchor_design_and_recirc_fraction_uq/check_upcomer_onset_packet.py`

Output: `PASS upcomer onset packet: 3 cases, 9 metric definitions, 6 UQ/mesh rows, 5 closure-disable rows`. The SVG is a static handoff figure.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, active
S13 sampler output, Fluid/external repository, source/property release, Qwall
release, production harvest, coefficient admission, protected score, or final
score was changed.
