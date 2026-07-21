---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_residual_scorer/README.md
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_residual_scorer/paper_diagnostic_note.md
tags: [journal, pressure-ledger, two-tap, recirculation, lower-apparent-k]
related:
  - .agent/status/2026-07-20_TODO-TWO-TAP-RECIRC-RESIDUAL-SCORER.md
  - imports/2026-07-20_two_tap_recirc_residual_scorer.json
task: TODO-TWO-TAP-RECIRC-RESIDUAL-SCORER
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: journal
status: complete
---
# Two-Tap Recirculating Residual Scorer

Task: `TODO-TWO-TAP-RECIRC-RESIDUAL-SCORER`

## Work Completed

Built a diagnostic package for the current recirculating `corner_lower_right`
two-tap rows. It explains the lower apparent `K` trend, audits throughflow
`q_ref`, emits a partial residual scorecard, and writes the next extraction
contract needed before any coefficient review.

## Scientific Decision

The lower static apparent `K` trend is not evidence of lower admitted component
loss. The trend is consistent with dynamic-pressure denominator growth while
static pressure remains hydrostatic/buoyancy dominated. The endpoint normal
mass flux is tiny relative to speed-based mass flux, so throughflow `q_ref`
must remain untrusted until a single-leg orientation/masking audit passes.

## Next Evidence Needed

- face-level positive/negative mass flux and single-leg mask support;
- same-label/same-formula/same-sign mesh/time UQ for the pressure residual;
- a separate non-recirculating same-topology anchor before ordinary K is
  revisited.

## Validation

- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_residual_scorer/build_two_tap_recirc_residual_scorer.py`
- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_residual_scorer/test_two_tap_recirc_residual_scorer.py`

Both passed before closeout.
