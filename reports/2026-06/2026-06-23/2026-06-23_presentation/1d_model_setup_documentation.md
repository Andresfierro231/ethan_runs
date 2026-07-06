# 1D Model Setup Documentation

Date: `2026-06-23`

This note is the compact model-setup companion for the presentation-local 1D
section. It is based on:

- `reports/2026-06-23_ethan_1d_closure_bakeoff/2026-06-23_one_d_setup_and_confidence.md`
- `reports/2026-06-23_ethan_1d_closure_bakeoff/2026-06-23_modeling_assumptions_results_and_next_steps.md`

## Setup Table

| Item | Current published June 23 local setting |
| --- | --- |
| Comparison basis | CFD frozen-state last-window mean, not experiment |
| Frozen CFD source package | `reports/2026-06-22_ethan_frozen_state_results/` |
| Active 1D solver | `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2` |
| Active solver mode | `predictive_airside_hx` |
| Defended scored scenario | `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1` |
| Scenario class | baseline, not hybrid |
| Base insulation setting | `1.0 in` |
| Radiation treatment | on |
| External convection treatment | blended Churchill-Chu natural-convection correlation |
| Radiation model | linearized Stefan-Boltzmann exchange to ambient |
| Test-section emissivity | quartz `0.95` |
| Heat-input treatment | tracked heater power plus separate `37 W` quartz test-section source |
| Heat-loss comparison contract | `Q_lost = Q_removed + Q_ambient` |

## Energy Error Formula

The presentation-local `energy error` metric is defined directly from the
current validation code path:

- `Q_lost,1D = qhx_total_W + qambient_total_W`
- `Q_lost,CFD = cfd_removed_w + cfd_ambient_w`
- `energy_error_w = Q_lost,1D - Q_lost,CFD`
- `energy_error_pct_of_heater = 100 * abs(energy_error_w) / abs(cfd_heater_w)`

This means the reported percentage is the magnitude of the 1D-vs-CFD total
heat-loss mismatch, normalized by the CFD heater net power to fluid.

## Branch Closure Assignment

| Loop region or branch | Current treatment | Status |
| --- | --- | --- |
| `lower_leg` and `test_section_span` friction | `straight_friction_class_aware_re_power_law` | `provisional_defended` |
| `left_lower_leg` thermal closure | `left_lower_leg_nu_branch_aware_re_power_law` | `provisional_defended_limited_domain` |
| `left_lower_leg`, `test_section_span`, `left_upper_leg`, `upcomer` | `primary_ua_profile_library` | admitted state-surface thermal lane |
| same subset | `secondary_htc_profile_library` | diagnostic secondary thermal lane |
| `right_leg` / downcomer | residual or lumped treatment only | direct `Nu` blocked |
| `upcomer` | sensitivity-only thermal branch | needs different reduced-order treatment |

## What We Are Explicitly Not Assuming

- We are not assuming one global fully developed internal closure around the
  entire loop.
- We are not treating `upcomer` as just another straight developing-flow
  branch.
- We are not claiming the current readable bundle already contains a globally
  matched `1.4 in` Salt scenario.
- We are not claiming the current local bakeoff is the refreshed external
  `Fluid` replay.

## Confidence And Current Boundary

| Topic | Current confidence |
| --- | --- |
| CFD late-window heat ledger | high |
| `left_lower_leg` direct developing-flow thermal evidence | high |
| baseline `1.0 in`, radiation-on row as best full-coverage readable scenario | medium |
| hybrid family as best global predictive choice | low, because readable coverage is too narrow |
| direct downcomer HTC / direct downcomer `Nu` | low / blocked |
| globally matched insulation treatment | uncertain |

## Presentation One-Liner

The current 1D model is branch-aware enough to diagnose where it fails, but it
is not yet predictive enough to claim accurate steady-state Salt temperatures
or mass flow without a better upcomer treatment, better return-leg treatment,
and a cleaner insulation / heat-input contract.
