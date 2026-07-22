# Thesis Reuse Index

## Where This Fits

Use this package in the master's thesis as the bridge between:

- diagnostic CFD-to-1D heat-path accounting, and
- the next predictive 1D boundary/HX/refinement work.

It belongs in a chapter or section on thermal model-form diagnosis, not in a
final validation section.

## Thesis Claim Status

| Claim | Status | Use |
| --- | --- | --- |
| Current best predictive-style model can be compared by physical heat-loss leg. | Supported | Methods/results. |
| Aggregate heat balance hides wrong-location heat loss. | Supported by this package | Presentation and thesis result. |
| Junction/stub regions are the largest under-loss lane. | Supported diagnostic | Model-refinement target. |
| Pipe legs over-lose heat under the current ambient model. | Supported diagnostic | External-boundary target. |
| The model is final predictive HX. | Not supported | Do not claim. |

## Canonical Citation Inside Repo

Use:

`work_products/2026-07/2026-07-14/2026-07-14_best_predictive_heat_loss_discrepancy/`

Primary table:

`best_predictive_leg_heat_loss_discrepancy.csv`

## Short Thesis Paragraph

Although the best current predictive-style model nearly closes the aggregate
heat balance, a leg-resolved comparison shows that agreement is partly
cancellation. The 1D model removes too much heat from pipe legs and too little
from junction/stub regions. This motivates a branchwise external-boundary and
junction heat-loss treatment rather than a single global heat-loss correction.
