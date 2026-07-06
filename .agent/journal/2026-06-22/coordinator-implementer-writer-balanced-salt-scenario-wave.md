# AGENT-105 Journal

Date: `2026-06-22T18:25:00-05:00`
Role: `Coordinator / Implementer / Writer`
Task: `AGENT-105`

## Intent

Apply the new strict Salt scenario gate
`|Q_in - Q_lost| < 2 W` at the parent reference state, then replace or remove
the current queued Salt scenario jobs accordingly.

## Observed state at start

- Six Salt bracket jobs were already running as standalone 64-rank jobs:
  `3250778`-`3250783`.
- One packed insulation-only Salt optimum job was pending:
  `3250784`.
- The bracket children changed heater and insulation, but left the cooling
  branch inherited from the parent.
- The readable 3D contract still exposes the cooler branch as fixed-`Q`, so
  the strict gate had to be enforced through the parent late-window sectionwise
  heat ledger rather than through a live cooler-`h` control.

## Action

- Canceled bracket jobs `3250778`-`3250783` and the insulation-only packed job
  `3250784`.
- Rebuilt the six bracket staged roots in place:
  - restored baseline insulation
  - kept the `+/-10%` heater mutations
  - solved the three cooling-branch sink patches from the parent late-window
    residual requirement
- Added a packed `3 x 64` Salt launcher and resubmitted the six balanced
  bracket cases as:
  - `3251883` `ethan_salt_hiqbal3`
  - `3251884` `ethan_salt_loqbal3`
- Left the insulation-only optimum wave out of queue because the current 3D
  fixed-`Q` contract cannot defend a `< 2 W` staging residual for an
  insulation-only mutation.

## Completion

- The bracket wave now has a rigorous queue state under the new heat-balance
  rule.
- The optimum-insulation wave remains preserved but explicitly not runnable
  under the current strict gate.
- The campaign docs, manifests, report note, and June 22 workspace journal now
  preserve the exact residual arithmetic and job mapping.
