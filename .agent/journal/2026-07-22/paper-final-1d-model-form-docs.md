---
provenance:
  - reports/thesis_dossier/2026-07-22_final_1d_model_form_for_paper.md
tags: [journal, paper, model-form, fluid-walls, no-admission]
related:
  - .agent/status/2026-07-22_TODO-PAPER-FINAL-1D-MODEL-FORM-DOCS.md
  - imports/2026-07-22_paper_final_1d_model_form_docs.json
task: TODO-PAPER-FINAL-1D-MODEL-FORM-DOCS
date: 2026-07-22
role: Writer / Reviewer / Forward-pred / Thermal-modeling / Hydraulics
type: journal
status: complete
---
# Paper Final 1D Model Form Docs

## Attempted

Assembled a concise paper-facing model-form document from the current
`fluid+walls` note, current CSEM model-form section, junction/pressure sections,
and July 22 model-form, PASSIVE-H2, mesh, onset, and pressure-anchor summaries.

## Observed

The evidence supports a steady `fluid+walls` architecture, not a frozen final
prediction. The strongest exact numbers for the paper-facing state are:
`0` admitted final candidates, `0` final score values, `0` source/property
release-ready rows, PASSIVE-H2 corrected radiation `22.4052516482..25.6530978934 W`,
PASSIVE-H2 full passive operator `38.6073163603..44.6770586908 W`, model-form
bakeoff `1032` observations and `15` case/model score rows, upcomer onset
`3` recirculation-cell-observed train rows, and S13 formal GCI-ready rows `0`.

## Inferred

The useful paper claim is architectural and methodological: the model form is
ready to state, while score/freeze remains blocked by runtime implementation,
source/property, same-QOI UQ, and pressure endpoint gates.

## Caveats

No external manuscript was edited. The document must not be used to imply
closure admission, final validation, or hidden use of protected/runtime-forbidden
inputs.

## Next Useful Actions

Use the report as an evidence-backed source for a manuscript writer. Keep S11
and S15 trigger-gated until one runtime-legal candidate exists.
