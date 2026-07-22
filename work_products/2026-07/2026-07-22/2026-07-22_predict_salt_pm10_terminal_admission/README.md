# TODO-PREDICT-SALT-PM10-TERMINAL-ADMISSION

Generated: 2026-07-22T14:41:37.546585+00:00

This package closes the pre-terminal ambiguity for the Salt2/Salt4 +/-10Q
PM10 rows using read-only evidence. `3293924` is terminal as `TIMEOUT`, the
dependent harvester `3295438` is `COMPLETED`, and the local terminal drift
classification reports four passing case gates.

## Disposition

- `salt2_lo10q`, `salt2_hi10q`, `salt4_lo10q`, and `salt4_hi10q` have terminal
  evidence available and pass the existing strict terminal drift/log gate.
- They are not admitted for fitting, model selection, runtime inputs, source
  release, or current final scorecard scoring.
- They are future blind-holdout candidates that may be scored only after an
  independently frozen predictive candidate exists.
- Upcomer evidence classifies all four as strong recirculation diagnostics.
  Ordinary upcomer `Nu`, `f_D`, or component-`K` fitting remains forbidden.
- Representative mdot and temperature windows are finite. `total_Q` remains
  drifting in the representative steady-window table, so it is diagnostic
  context only and cannot release a source/property correction.

## Outputs

- `scheduler_terminal_evidence.csv`
- `pm10_case_terminal_gate.csv`
- `pm10_steadiness_metric_context.csv`
- `pm10_split_use_decision.csv`
- `pm10_recirc_onset_summary.csv`
- `pm10_heat_pressure_evidence_inventory.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `summary.json`

## Next Executable Work

1. Build the pressure ladder and streamwise pressure-map packet from the
   admitted terminal PM10 evidence without fitting to protected rows.
2. Build a heat-loss/source ledger that keeps wallHeatFlux and total_Q as
   diagnostics until an independent source/property release row is claimed.
3. Use the PM10 recirculation metrics as blocked-ordinary-closure evidence in
   the thesis recirculation/onset packet, not as an ordinary pipe anchor.
