# Predictive Hydraulic Gate

Task: `TODO-PRED-HYDRAULIC-GATE`

This package gates pressure-rooted mdot predictivity before any thermal-fit claim. It reads the AGENT-262 pressure-only mesh-family package, the AGENT-284 Closure-QOI GCI package, and the TODO-PRED-FORWARD-V0 imposed-cooler fast-scan package. No native CFD solver outputs or external Fluid files are modified.

## Start Here

Why this exists: forward-v0 improved heater-only CFD Tmean error, but still overpredicted mdot. This gate prevents that thermal-looking improvement from hiding pressure-rooted hydraulic failure.

Files to open first:

- `hydraulic_gate_decisions.csv` for the admission decision.
- `hydraulic_fit_safety_gate.csv` for fit-safe pressure/friction rows.
- `forward_v0_hydraulic_residuals.csv` for case-level mdot and pressure residual evidence.
- `summary.json` for machine-readable counts and source paths.

Trusted packages: AGENT-262 Salt2 pressure-only mesh-family comparison, AGENT-284 Salt2 Closure-QOI mesh GCI, and TODO-PRED-FORWARD-V0 imposed-cooler fast-scan.

Active board row: `TODO-PRED-HYDRAULIC-GATE`.

Next task sequence: run a broader hydraulic-term fit using only fit-safe rows, then collect or stage minor-loss/profile evidence, then rerun forward scoring before any thermal correction fit.

Output contract: keep raw pressure-gradient, momentum-corrected, forward-mdot, and thermal-blocker evidence in separate files and fields.

Do-not-do guardrails: do not mutate native CFD outputs, do not edit external Fluid here, do not train thermal UA/HTC/Nu parameters from this package, and do not treat pressure-recovery/noise rows as training rows.

Unresolved blockers: no publication-ready Closure-QOI GCI rows, full `solve_case` forward run not rerun here, no broadened minor-loss/profile extraction, and thermal mesh/GCI remains blocked.

## Key Findings

- Raw pressure-gradient fit-safe rows: `left_lower_leg, left_upper_leg`.
- Momentum-corrected fit-safe diagnostic rows: `left_lower_leg, left_upper_leg, lower_leg, right_leg, test_section_span, upper_leg`.
- `F0_current_fluid_sources` mean mdot error vs CFD: `0.008082 kg/s` (`53.96%`).
- `F1_heater_only` mean mdot error vs CFD: `0.005478 kg/s` (`36.37%`).
- Both forward-v0 variants overpredict mdot for every Salt row, even where pressure residuals are small.
- Pressure/friction evidence supports a dedicated hydraulic tuning lane for friction, minor-loss, and profile terms before thermal fitting. Training must stay restricted to fit-safe rows; pressure-recovery/noise rows remain diagnostic.
- Thermal closure remains blocked; this package admits no thermal UA/HTC/Nu claim.

## Outputs

- `hydraulic_fit_safety_gate.csv`
- `forward_v0_hydraulic_residuals.csv`
- `hydraulic_gate_decisions.csv`
- `summary.json`

## Reproduce

```bash
python3 tools/analyze/build_predictive_hydraulic_gate.py
python3 -m unittest tools.analyze.test_predictive_hydraulic_gate
```

## Interpretation Boundary

This is a hydraulic gate. It separates pressure residual, friction fit safety, and mdot error from thermal source/sink parameters. The heater-only forward-v0 thermal improvement remains blocked from thermal-fit interpretation until mdot predictivity and thermal mesh/GCI blockers are resolved.
