# Recirculation Feature Admission And Hybrid 1D Contract

Generated: `2026-07-16T22:25:44+00:00`

## Decision

Current evidence does not admit a predictive recirculation model for the 1D
solver. It does admit a stronger rule: material upcomer/test-section
recirculation blocks ordinary single-stream `Nu`, `f_D`, and component `K`
labels.

## Current Evidence

- Feature/admission rows consolidated: `42`.
- Rows allowing ordinary single-stream fit today: `0`.
- Recirculating/effective-lane rows: `42`.
- Future evidence queue rows: `10`.

## Thesis-Safe Claim

Say that the current admitted upcomer/test-section evidence is a recirculating
mixed-convection regime and therefore a validity boundary for ordinary 1D
closures. The next predictive model should use a named hybrid upcomer lane with
ordinary-pipe, transition, and recirculating-section states.

## Do Not Claim

Do not claim a calibrated transferable recirculation closure, ordinary upcomer
`Nu`, ordinary upcomer `f_D`, or component `K` from the current rows. Do not hide
recirculation in a global friction multiplier.
