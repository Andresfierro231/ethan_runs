# Test-Section Heat Contract And Enthalpy Charts

Date: `2026-07-08`
Task: `AGENT-207`
Role: Coordinator / Implementer / Writer
Owner: codex

## Observed Facts

- Salt cases in the 1D Fluid config include `test_section_power_W = 37.0 W`.
- The Fluid solver applies that value as a positive source in the test-section
  segment.
- The CFD patchwise heat ledger shows the test-section patch is a net sink at
  the fluid wall for Salt 2/3/4.
- The postprocessor chart package now includes a separate enthalpy residual
  figure and table using span endpoint temperatures.

## Inferred Interpretation

The current 1D test-section source is implemented according to the gross input
contract, but a predictive thermal model must solve net exchange:
gross imposed source minus quartz/external losses, compared against CFD
wallHeatFlux and segment enthalpy change.

## Blockers

- Upcomer/test-section residuals remain recirculation diagnostics.
- Junction heat residuals are not bracketed by the endpoint-temperature source.
- Radiation remains absent unless a `qr` output appears.

## Files Used

- `tools/analyze/build_postprocessor_summary_charts.py`
- `tools/analyze/test_postprocessor_summary_charts.py`
- `work_products/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.csv`
- `work_products/2026-07-08_span_endpoint_temperatures/span_endpoint_temperatures.csv`
- `work_products/2026-07-08_postprocessor_summary_charts/**`
- `operational_notes/07-26/08/2026-07-08_test_section_heat_contract_and_analysis_plan.md`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/geometry.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/cases.yaml`

## Recommended Next Action

Feed the heat residual table into model-form bakeoff as a thermal validation
axis, not as a fit target.
