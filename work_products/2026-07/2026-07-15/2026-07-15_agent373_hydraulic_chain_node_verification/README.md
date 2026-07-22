# AGENT-421 AGENT-373 Hydraulic Chain Node Verification

Created: `2026-07-15T14:40:49.240718+00:00`

## Result

The original AGENT-373 stage logic was rerun locally into
`agent373_stage_outputs/`. The later scratch OpenFOAM evidence from AGENT-409
is used for the real raw two-tap landing decision, and AGENT-406/414 are used
for PM5/F6 review.

- Raw two-tap landed: `3` diagnostic rows.
- F6 review rows landed: `12`, with
  `0` fit-admissible rows.
- Reset-K sweep landed: `128` rows, admitted only as
  component-separation diagnostics.
- PM5 matched-pressure/upcomer landed: `12` rows, all with
  wallHeatFlux.
- Final hydraulic residual attribution status:
  `blocked_not_final`.

## Admission Decision

Diagnostic admission is supported for raw two-tap pressure scale, reset-K
component separation, and PM5/F6 onset review. Fit admission is not supported
today because the raw two-tap rows are coarse-only reduced-pressure proxies with
recirculation and no mesh/GCI/component policy admission, and all PM5 F6 review
rows remain recirculating/onset diagnostics.

No native CFD solver outputs, registry/admission state, scheduler state,
generated indexes, or external Fluid code were mutated by this package.
