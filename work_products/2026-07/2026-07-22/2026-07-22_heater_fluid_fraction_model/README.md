---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract/case_heat_ledger.csv
  - work_products/2026-07/2026-07-14/2026-07-14_heater_fraction_forward_v1_paper_methods/heater_fraction_scalar_candidates.csv
tags: [forward-model, heater, heat-loss, predictive-1d]
related:
  - TODO-PREDICT-HEATER-FLUID-FRACTION
task: TODO-PREDICT-HEATER-FLUID-FRACTION
date: 2026-07-22
status: complete
---
# Heater Fluid Fraction Model

Decision: `heater_eta_candidate_passes_wallflux_score_no_final_forward_admission`.

The useful candidate is `HF2_eta_wallflux_salt2`: fit one heater-to-fluid
fraction from Salt2 train wallHeatFlux evidence, then predict Salt3/Salt4
heater heat-to-fluid using setup heater power only. It passes the predeclared
held-out wallHeatFlux W gates, but it is not a final forward-v1 admission until
source/property release and coupled heat-ledger scoring are complete.

Runtime guardrails: no CFD mdot, validation temperatures, holdout temperatures,
or per-case realized wallHeatFlux are runtime inputs. `HF3` is retained only as
a leakage upper bound.
