---
provenance:
  - result_status_matrix.csv
  - claim_boundary_ledger.csv
  - figure_table_target_ledger.csv
tags: [thesis, external-writer, ch7, ch8, results, negative-evidence]
task: TODO-THESIS-LATEX-EVIDENCE-PACKET-CH7-CH8-RESULTS-2026-07-22
date: 2026-07-22
role: Writer/Reviewer
status: current
---
# External Writer Brief: Ch7/Ch8 Results And Negative Evidence

This packet gives thesis-facing facts, not final prose.

## Core Result Shape

Chapter 7 can already report important scientific findings even without a final
predictive score:

- Pressure: lower-right/F6 work is a negative result for ordinary component-K
  admission.  It is section-effective pressure evidence, not a negative loss
  coefficient and not admitted F6/component-K closure.
- Thermal: S12 residual-owner work was attempted rigorously.  S12-HIAX1 is a
  plausible physical residual-owner hypothesis for TW5/TW6, but no S12
  candidate can be frozen or admitted.
- Upcomer: limited sampled-field evidence and matched velocity visuals support
  a recirculation-aware model form.  They do not admit exchange-cell,
  ordinary-pipe, Qwall, or final predictive coefficients.
- Predictive scorecard: no frozen runtime-legal candidate exists.  The final
  score table remains a blocked shell with protected rows untouched.

## Numbers The Writer May Use

- S12: `5` candidate-disposition rows, `5` train-only metric rows, `8`
  no-freeze blockers, `0` candidate-reviewable rows, `0` protected
  validation/holdout/external scored rows, `0` final score values.
- S13: `3` Salt cases synthesized, `3` finite exchange rows, `15`
  diagnostic-ready gate rows, `0` production-ready gate rows, `15` blocked
  production gate rows.
- S13 same-QOI UQ but no mesh/GCI:
  - `Q_wall_W`: temporal UQ max abs `0.0010252426 W`, max relative
    `0.00364554244946 percent`, accepted same-label GCI rows `0`.
  - exchange mdot proxy: temporal UQ max abs `6.157475194e-07 kg/s`, max
    relative `0.803956787612 percent`, accepted same-label GCI rows `0`.
  - residence-time proxy: temporal UQ max abs `6.38606992 s`, max relative
    `0.808752828051 percent`, accepted same-label GCI rows `0`.
  - wall/core/bulk contrast: temporal UQ max abs `0.000209096863 K`, max
    relative `0.122613775443 percent`, accepted same-label GCI rows `0`.
- Upcomer visuals: shared signed y-velocity range
  `[-0.07702504843473434, 0.07702504843473434] m/s`; shared resultant
  magnitude range `[0.0, 0.07704159866519554] m/s`; rendered maximum downward
  `U_y` values for Salt1-Salt4 are approximately `0.068`, `0.069`, `0.072`,
  and `0.077 m/s`.

## Suggested Placement

- Ch7 pressure subsection: pressure claim-boundary table and lower-right
  negative-result classification.
- Ch7 thermal subsection: S12 residual-owner waterfall and candidate
  disposition/no-freeze table.
- Ch7 upcomer subsection: matched Salt1-Salt4 side-Z velocity visuals and S13
  sampled-field gate matrix.
- Ch8 predictive assessment: blocked scorecard logic, runtime legality matrix,
  S13 mesh/GCI gate, and next-study queue.

## Non-Negotiable Guardrails

- CFD is high-fidelity computational reference evidence, not experimental
  validation.
- Diagnostic CFD evidence can support model-form selection, negative results,
  limitations, and study design.
- Diagnostic CFD evidence must not be promoted to admitted predictive closure.
- Predictive runtime claims must not use CFD mass flow, realized CFD
  `wallHeatFlux`, imposed CFD cooler duty, validation temperatures, holdout
  rows, or external-test rows as hidden inputs.
- Do not report final prediction scores until a frozen runtime-legal candidate
  is released by a separate source/property/split/uncertainty gate.
