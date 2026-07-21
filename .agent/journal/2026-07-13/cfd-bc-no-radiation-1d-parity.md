# CFD BC No-Radiation 1D Parity

Task: `AGENT-279`
Date: 2026-07-13
Role: Coordinator / Implementer / Tester / Writer

## Context

The previous AGENT-270 and AGENT-271 packages showed that cooler duty is
first-order, but the next question is stricter: impose the CFD heater and cooler
boundary setup together, disable radiation in the 1D comparison, and identify
where section heat gain/loss still disagrees.

AGENT-272 was already assigned to a time-series package. A concurrent board
cleanup also retired the earlier AGENT-276 starter row after seeing only the
contract and run-plan CSVs, so this completed package is recorded under the new
`AGENT-279` board item.

## Work Performed

Added a new repo-local builder:

`tools/analyze/run_cfd_bc_no_radiation_1d_parity.py`

The builder reads AGENT-263 patch-role rows and July 8 fixed-mdot targets,
imports Fluid read-only, and executes four radiation-off fixed-mdot modes:

- `N0_current_fluid_rad_off`
- `N1_heater_cooler_imposed_rad_off`
- `N2_cfd_setup_bc_plus_passive_conv_rad_off`
- `N3_realized_wallflux_diagnostic_rad_off`

The `N2` mode is the closest current repo-local temperature-dependent boundary
replay: CFD heater/test-section imposed sources, CFD cooler imposed duty, and
non-cooler `hA/Ta` convection-only losses. It remains an approximation because
Fluid does not yet accept first-class CFD wall-layer/external-boundary
dictionaries.

Added focused tests:

`tools/analyze/test_cfd_bc_no_radiation_1d_parity.py`

## Observed Results

Generated package:

`work_products/2026-07/2026-07-13/2026-07-13_cfd_bc_no_radiation_1d_parity/`

Key counts:

- 24 CFD boundary-contract rows.
- 12 fixed-mdot replay rows.
- 60 section heat-loss comparison rows.
- 48 discrepancy-attribution rows.
- 5 correction-proposal rows.

Mean absolute Tmean error by mode:

- `N0_current_fluid_rad_off`: `81.130364 K`
- `N1_heater_cooler_imposed_rad_off`: `4.933870 K`
- `N2_cfd_setup_bc_plus_passive_conv_rad_off`: `22.650368 K`
- `N3_realized_wallflux_diagnostic_rad_off`: `118.919783 K`

## Interpretation

Imposing heater and cooler setup terms together with radiation disabled closes
most of the first-order mean-temperature mismatch. However, section comparison
shows remaining physically meaningful discrepancies:

- Heater imposed source is higher than realized CFD heat transfer; mean
  realized/imposed heater transfer ratio is `0.918126`.
- Cooler imposed and realized duties agree to numerical precision; a per-case
  cooler hack is not justified for setup parity.
- Test section remains a model-form issue: CFD setup has `+37 W`, but realized
  wallHeatFlux is a net sink for Salt2-4.
- The convection-only `hA/Ta` replay over-removes heat relative to the best
  heater+cooler mode; the output proposes an initial diagnostic hA multiplier
  of `0.666719` from non-cooler hA-row realized losses, but marks it blocked
  pending wall-layer/bulk-temperature mapping review.

## Preserved Blocks

- No Fluid source files were edited.
- No native CFD solver outputs were mutated.
- No registry or admission changes were made.
- The package is fixed-mdot diagnostic evidence, not predictive hydraulic
  validation.

## Validation

- `python -m py_compile tools/analyze/run_cfd_bc_no_radiation_1d_parity.py tools/analyze/test_cfd_bc_no_radiation_1d_parity.py`
- `python tools/analyze/test_cfd_bc_no_radiation_1d_parity.py`
- `python tools/analyze/run_cfd_bc_no_radiation_1d_parity.py --plan-only --strict --output-dir /tmp/agent279_plan_only`
- `python tools/analyze/run_cfd_bc_no_radiation_1d_parity.py --strict`
- `python -m json.tool work_products/2026-07/2026-07-13/2026-07-13_cfd_bc_no_radiation_1d_parity/run_metadata.json`

System `python` was used for full Fluid-backed replay because this shell's
`python3.11` lacks `numpy`.
