# AGENT-102 Stale / Setup Questions

Date: `2026-06-23`

## Observed

- The local presentation bakeoff now compares 1D against CFD frozen-state
  last-window means, not against experimental values.
- The external readable `Fluid` bundle remains the older
  `ethan_cfd_informed_salt_v1` snapshot, so the present 1D bakeoff still
  inherits that bundle's scenario menu.
- The defended full-coverage winner is the baseline `1.0 in` radiation-on
  scenario, not the hybrid branch-adjusted scenario.
- The same external family can express branchwise effective insulation
  multipliers in hybrid rows, including `right_vertical = 1.40`, but there is
  still no published global `1.4 in` Salt scenario in the readable bundle.

## Open questions

- Was the intended CFD setup globally `1.4 in` on the insulated loop, or was
  `1.4` only intended as an effective branchwise correction on selected legs?
- Should the next external `Fluid` refresh publish a true global `1.4 in`
  Ethan CFD-informed Salt scenario, or should it publish a branchwise
  calibrated outer-loss bundle tied directly to the retained CFD heat ledger?
- If presentation claims need physical setup fidelity, should the current
  defended `1.0 in` baseline be shown only as a surrogate boundary rather than
  as the final predictive closure?
