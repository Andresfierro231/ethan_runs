# MF13 Signed Source/Property Heat-Path Release Preflight

MF13 asks whether the signed heat-path quantities needed by MF12 can be promoted from diagnostic evidence to runtime model-form inputs. The answer is a fail closed preflight, not a source/property release.

Three active setup source/sink families have useful sign and magnitude metadata: cooler/cooling_branch, heater/lower_leg, test_section/upcomer. They establish directionality for candidate formulas, with heater and test-section heat positive into the fluid and cooler heat negative from the fluid. However, all active rows remain `runtime_allowed_now=false` and `source_property_released_now=false`, so MF12 may use them only to motivate a hypothesis, not to execute or score a runtime formula.

The passive/downcomer family remains more restricted: runtime_allowed_now_true;source_property_released_now_true;independent_source_basis;setup_q_magnitude_range;passive_area_material_ambient_insulation_basis. That prevents treating the H2 global passive sensitivity as an admitted physics repair or as a fitted multiplier.

Release-ready source/property families in this preflight: 0 of 4. All release gates report `release_allowed=false`; validation, holdout, and external-test rows are metadata-only and were not scored.

The next rigorous step is same-QOI TP projection uncertainty: even a physically plausible signed source term cannot be evaluated as a predictive TP model until the TP projection itself has a runtime-legality and uncertainty boundary.
