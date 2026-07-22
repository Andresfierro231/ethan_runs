# Math, Assumptions, Theory, And Results Register

## Split Discipline

The active split remains Salt2 train, Salt3 validation, Salt4 holdout. Any
candidate fitted on Salt2 must be scored on Salt3 and Salt4 without refitting.
Perturbation and diagnostic rows do not become independent training rows unless
a later admission package documents a new split.

## Cooler/HX Screens

The relevant quantity is the residual between modeled cooler heat removal or
temperature response and the CFD/reference target. Candidate rows are useful
only when runtime inputs are setup-only. Rows using imposed CFD cooler heat or
realized CFD cooler heat are diagnostics and leakage checks.

## Hydraulic Root Diagnostics

For pressure-root rows, mdot is varied until the model pressure residual is
near zero. This locates whether thermal/source assumptions imply a different
hydraulic operating point, but the result cannot replace raw two-tap/F6/reset-K
evidence from the pending hydraulic chain.

## Boundary And Radiation Policy

CFD wallHeatFlux under rcExternalTemperature includes convection and radiation
in one total flux. The forward model may use boundary metadata for setup, but
must not replay realized wallHeatFlux as predictive closure or add a second
radiation term on top of realized flux.

## Internal Nu Policy

No fitted internal Nu row is available for predictive scoring. Effective
upcomer Nu evidence remains diagnostic/validation-only until onset candidates
and matched-plane extraction reopen the fitting gate.

## Current Result

AGENT-391 and AGENT-392 landed useful candidate and diagnostic evidence, but
final forward-v1 remains blocked by non-terminal hydraulics/cfd-pp gates and a
cancelled PM5 matched-plane/upcomer job.
