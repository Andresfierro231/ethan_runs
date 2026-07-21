---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit
  - work_products/2026-07/2026-07-15/2026-07-15_mdot_temperature_error_report_and_presentation
  - work_products/2026-07/2026-07-15/2026-07-15_forward_v1_row_admission_ledger
  - work_products/2026-07/2026-07-15/2026-07-15_setup_predictive_heat_loss_fluid_variant
  - work_products/2026-07/2026-07-15/2026-07-15_diagnostic_cfd_heat_loss_replay_and_predictive_loss_plan
tags: [journal, forward-v1, boundary-conditions, mdot, temperature, setup, model-form, thesis-source]
related:
  - .agent/status/2026-07-15_AGENT-424.md
  - imports/2026-07-15_setup_bc_model_error_synthesis_report.json
  - work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/README.md
task: AGENT-424
date: 2026-07-15
role: Writer/Forward-pred/BC-modeling/Tester
type: journal
status: complete
---
# Setup/BC/Model-Form Error Synthesis Report

User request: produce a report on the different setup, boundary conditions,
modeling assumptions/forms, and resulting mass-flow and temperature errors.

Actions:

1. Claimed AGENT-424 with a non-overlapping scope because AGENT-420 already
   owned a related active report package.
2. Read the existing AGENT-360/420 audit outputs, row-admission ledger, forced
   CFD heat-loss replay package, and setup-predictive Fluid variant package.
3. Implemented
   `tools/analyze/build_setup_bc_model_error_synthesis_report.py` to generate a
   compact report and source tables from existing evidence only.
4. Added
   `tools/analyze/test_setup_bc_model_error_synthesis_report.py` with focused
   checks for headline error values and diagnostic/predictive guardrails.
5. Generated
   `work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/`.

Scientific summary:

- M2, the CFD heater + test-section net + cooler diagnostic pressure-root mode,
  is the current best combined mdot/temperature diagnostic: 10.397 percent mean
  absolute mdot error and 26.972 K all-probe RMSE.
- M3, the CFD heater + cooler diagnostic mode, has the lowest all-probe RMSE
  at 18.023 K but worsens mdot error to 16.826 percent, showing a heat-placement
  and buoyancy tradeoff.
- M1, full realized CFD segment heat-ledger replay, still has 35.874 percent
  mean absolute mdot error and 159.168 K all-probe RMSE, so exact realized heat
  placement alone does not solve the current 1D state/reference-temperature
  mismatch.
- The exact section-placement forced replay remains diagnostic-only because it
  consumes realized CFD wallHeatFlux.
- The setup-predictive Fluid hooks now exist for future scoring, but they are
  implementation capability, not admitted final forward-v1 evidence.

Validation:

- `python3.11 tools/analyze/build_setup_bc_model_error_synthesis_report.py`
- `python3.11 -m unittest tools.analyze.test_setup_bc_model_error_synthesis_report`
- `python3.11 -m json.tool work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/summary.json`

No native CFD outputs, scheduler state, registry/admission state, generated
indexes, or external Fluid files were modified.
