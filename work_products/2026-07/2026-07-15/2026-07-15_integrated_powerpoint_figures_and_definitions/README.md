# Integrated PowerPoint Figures and Definitions

Task: AGENT-434 correction of AGENT-433 figure package
Date: 2026-07-15

This package converts the integrated weekly presentation figure suggestions into standalone advisor-facing SVG figures and explicit terminology/equation tables. AGENT-433 corrected `fig06_heater_cooler_rmse.svg` to state the RMSE reference and model assumptions, and corrected `fig07_steady_state_rms_sem.svg` to avoid overlapping bottom text and repeated-looking small tick labels. AGENT-434 then added Salt4 nominal to `fig07_steady_state_rms_sem.svg` and the matching outline discussion. The figures are presentation artifacts derived from already-landed diagnostic/admission work products; no PowerPoint files are created by this package, and no native CFD solver outputs, registry/admission state, generated indexes, or external Fluid code were changed.

## Up-front definitions to use in the deck

- M1: diagnostic replay using the full CFD segment heat ledger while solving pressure for mdot.
- M1b: full CFD segment heat ledger with fixed CFD mdot; thermal isolation only.
- M2: CFD heater + test-section net + cooler while solving pressure for mdot; best current mdot diagnostic.
- M3: CFD heater + cooler only while solving pressure for mdot; best current TP/TW diagnostic.
- PM5: pressure-matched +/-5Q diagnostic upcomer evidence.
- F6: candidate hydraulic/friction correction scorecard; currently zero fit-admitted rows.
- h_proxy = q''/(T_wall - T_bulk): section-effective diagnostic heat-transfer proxy.
- Nu = hD/k, f_D, and K are not fit-admissible in the current recirculating upcomer evidence.
- SEM = sigma/sqrt(N) for independent samples; use SEM = sigma/sqrt(N_eff) when autocorrelation reduces the effective sample count.

## Figures

- `fig01_loop_schematic`: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig01_loop_schematic.svg` - Loop schematic with named legs, junctions, and measured/model quantities
- `fig02_glossary_equations`: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig02_glossary_equations.svg` - Advisor-facing definitions, assumptions, and equations
- `fig03_boundary_mode_ladder`: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig03_boundary_mode_ladder.svg` - Boundary-condition/model-mode ladder
- `fig04_mode_error_bars`: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig04_mode_error_bars.svg` - M1/M1b/M2/M3 mdot and TP/TW error bars
- `fig05_test_section_tradeoff`: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig05_test_section_tradeoff.svg` - M2 versus M3 mdot/temperature tradeoff by Salt case
- `fig06_heater_cooler_rmse`: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig06_heater_cooler_rmse.svg` - Heater and cooler RMSE model-form comparison
- `fig07_steady_state_rms_sem`: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig07_steady_state_rms_sem.svg` - Salt train/test steady-state RMS and SEM panel
- `fig08_admission_gate_funnel`: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig08_admission_gate_funnel.svg` - Internal-Nu/F6 admission gate funnel
- `fig09_forward_v1_roadmap`: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig09_forward_v1_roadmap.svg` - Forward-v1 roadmap and remaining gates

## Tables

- `term_glossary.csv`: advisor-facing definitions and presentation use.
- `equation_register.csv`: modeling assumptions/equations to define before results.
- `figure_manifest.csv`: stable figure IDs, paths, and captions.
- `source_manifest.csv`: input evidence used by this package.
