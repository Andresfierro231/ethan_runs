# Predictive Hydraulic Gate

Task: TODO-PRED-HYDRAULIC-GATE

Role: Implementer / Reviewer

## Context

The TODO-PRED-FORWARD-V0 imposed-cooler fast-scan package showed that the `F1_heater_only` variant reduced mean absolute CFD Tmean error to `4.609 K`, but still overpredicted mdot vs CFD by `+0.005477 kg/s`. This task gates pressure-rooted mdot predictivity before allowing any thermal-fit interpretation.

Inputs used:

- `work_products/2026-07/2026-07-13/2026-07-13_salt2_pressure_only_mesh_family_comparison/`
- `work_products/2026-07/2026-07-13/2026-07-13_salt2_closure_qoi_mesh_gci/`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/`

No native CFD solver outputs, external Fluid files, registry state, or wall-layer mapping outputs were modified.

## Work

Added `tools/analyze/build_predictive_hydraulic_gate.py`, which emits:

- fit-safety gate rows joined to AGENT-284 GCI admission state;
- forward-v0 hydraulic residual rows with mdot error percentages;
- explicit gate decisions separating pressure-gradient, momentum-corrected, forward-mdot, hydraulic tuning, and thermal-blocker evidence.

Added `tools/analyze/test_predictive_hydraulic_gate.py` to verify that fit-safe rows remain separated from diagnostic rows and that mdot overprediction blocks thermal claims.

## Observed Evidence

Raw pressure-gradient fit-safe rows are only:

- `left_lower_leg`
- `left_upper_leg`

Momentum-corrected rows are positive and medium/fine-consistent for all six spans, but remain a debuoyed/profile diagnostic lane rather than a replacement for raw pressure-gradient friction:

- `left_lower_leg`
- `left_upper_leg`
- `lower_leg`
- `right_leg`
- `test_section_span`
- `upper_leg`

Forward-v0 mdot evidence:

- `F0_current_fluid_sources`: mean mdot error vs CFD `+0.008082 kg/s` (`+53.96%`), max abs pressure residual `1.592 Pa`.
- `F1_heater_only`: mean mdot error vs CFD `+0.005478 kg/s` (`+36.37%`), max abs pressure residual `2.017 Pa`.
- All six Salt rows overpredict mdot.

## Interpretation

The hydraulic gate fails for thermal predictivity: the heater-only Tmean improvement cannot be used as a thermal-fit claim while pressure-rooted mdot remains high. The evidence supports tuning hydraulic friction, minor-loss, and profile terms before fitting thermal parameters, but training must use only fit-safe rows. Pressure-recovery/noise rows remain diagnostic.

Thermal closure remains blocked by the AGENT-262 reconstructed-T boundary and AGENT-284 missing/failed Closure-QOI GCI state. This package does not admit UA, HTC, Nu, or thermal correction fits.

## Validation

- `python3 tools/analyze/test_predictive_hydraulic_gate.py`
- `python3 -m py_compile tools/analyze/build_predictive_hydraulic_gate.py tools/analyze/test_predictive_hydraulic_gate.py`
- `python3 tools/analyze/build_predictive_hydraulic_gate.py`

All completed successfully.
