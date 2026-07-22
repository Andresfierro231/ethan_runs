# Methodology And Assumptions

This packet reconciles completed evidence packages only. It does not compute new
CFD fields, launch Fluid, fit coefficients, score protected rows, release
source/property values, or admit a closure.

Method:

1. Read the completed predictive blocker burndown as the prior blocker ranking.
2. Replace stale blocker states with later completed evidence where available:
   S13 candidate coarse/medium/fine reconciliation, S13 bulk-integral heat
   partition, S13 residual-complete open-CV contract, PASSIVE-H2 corrected
   operator packet, source/property exact-field recovery, train-only setup-UQ
   terminal harvest, and pressure/F6 ordinary-basis failure packet.
3. Preserve fail-closed semantics: a row is treated as unlocked only when the
   upstream package explicitly reports release/admission/freeze readiness.
4. Separate diagnostic numerical signal from predictive admissibility. Stable
   `Q_wall_W`/`F_wall` evidence can guide model form, but it is not a coefficient
   release or GCI admission.
5. Keep protected split discipline intact: validation/holdout/external scoring
   remains closed until exactly one runtime-legal candidate has a frozen manifest.

Core assumptions:

- Runtime inputs may include setup geometry, source/boundary-condition metadata,
  released property labels, and model-solved state. They may not include realized
  CFD wallHeatFlux, CFD mdot, imposed CFD cooler duty, observed validation
  temperatures, or hidden global multipliers.
- Averaged S13 values are allowed as diagnostic model-form evidence only. They
  are not substitutes for residual-complete energy balance terms.
- Current-coarse S13 rows are reference candidates only because the completed
  coarse-equivalence contract admits zero current-coarse rows.
- Pressure lower-right/two-tap rows remain material-reverse-flow/section-effective
  diagnostics, not ordinary component-K or F6 evidence.
