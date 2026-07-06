# Ethan Balanced Salt Scenario Wave

Generated: `2026-06-22`

## Conclusion

The June 22 Salt scenario queue was tightened to the new strict gate
`|Q_in - Q_lost| < 2 W` at the parent reference state.

That forced two changes:

- the six June 22 bracket relaunches were canceled and rebuilt in place as
  heater-only, residual-balanced children with baseline insulation restored
- the packed optimum-insulation wave was canceled without relaunch because an
  insulation-only mutation does not currently have a defensible 3D residual
  guarantee under the fixed-`Q` cooling contract

## Queue result

- canceled bracket jobs:
  - `3250778`
  - `3250779`
  - `3250780`
  - `3250781`
  - `3250782`
  - `3250783`
- canceled insulation-only packed job:
  - `3250784`
- replacement packed balanced jobs:
  - `3251883` `ethan_salt_hiqbal3`
  - `3251884` `ethan_salt_loqbal3`

## Scientific basis

- For the original six bracket relaunches, the lower-bound parent-ledger
  residuals already missed the new gate by `26-34 W` before counting the
  additional ambient-loss drift caused by the `±0.40 in` insulation change.
- For the replacement bracket cases, the same staged roots now:
  - restore baseline insulation
  - keep the `+/-10%` heater change
  - solve the three cooling-branch fixed sinks as the exact residual needed to
    keep the parent reference-state balance near zero
- For the optimum-insulation wave, the measured-state wall-loss optimizer is
  not the same object as the readable 3D sectionwise heat ledger, so it cannot
  certify a `< 2 W` 3D staging residual on its own.

See `queue_rebalance_summary.csv` for the exact residual arithmetic and job
mapping.
