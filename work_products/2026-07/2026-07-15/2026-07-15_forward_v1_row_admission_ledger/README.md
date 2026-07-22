# Forward-v1 Row Admission Ledger

Task: AGENT-407  
Generated: 2026-07-15

## Result

This package creates one canonical row-admission ledger for forward-v1 thermal
and HX evidence. It does not admit final forward-v1. The only predictive lane
kept open is a setup-legal HX/cooler candidate lane; realized wallHeatFlux,
imposed cooler duty, and negative test-section source rows are diagnostic only.
Fitted internal Nu has zero admitted rows.

## Current Classification

- Predictive candidate rows: 6
- Diagnostic replay rows: 18
- Diagnostic upper-bound rows: 6
- Blocked empty-fit rows: 1
- Not-admitted rows: 0

Preferred setup-legal HX candidate:
`salt2_fit_constant_UA_bulk_drive`.

## Method

1. Read AGENT-391 cooler/test-section outputs and AGENT-392 HX/external-BC
   outputs without rerunning Fluid, OpenFOAM, or scheduler jobs.
2. Classify each row using the allowed classes:
   `predictive_candidate`, `diagnostic_replay`, `diagnostic_upper_bound`,
   `blocked_empty_fit_set`, or `not_admitted`.
3. Require predictive HX rows to fit on Salt2 and score Salt3/Salt4 without
   refit or runtime use of realized/imposed CFD cooler duty.
4. Keep realized wallHeatFlux rows as diagnostic replay only because CFD
   `rcExternalTemperature` radiation is inseparable in total wall flux.
5. Keep internal Nu blocked because AGENT-319 reports zero fit-eligible rows,
   AGENT-330 reports recirculating/missing-anchor evidence, and AGENT-404 still
   has `wallHeatFlux_rows=0`.

## Files

- `row_admission_ledger.csv`: canonical row family table requested by the user.
- `final_predictive_hx_closure_rows.csv`: Salt2/Salt3/Salt4 HX candidate rows.
- `hx_candidate_reconciliation.csv`: side-by-side candidate decision table.
- `internal_nu_fit_rows.csv`: explicit zero-admitted internal-Nu blocker row.
- `realized_wallHeatFlux_replay_rows.csv`: leg heat-loss replay diagnostics.
- `imposed_cooler_diagnostic_rows.csv`: upper-bound/leakage rows.
- `test_section_negative_source_rows.csv`: compatibility-screen rows.
- `source_manifest.csv`: exact provenance paths.

## Guardrails

No native CFD solver outputs, scheduler state, registry/admission state, or
external `../cfd-modeling-tools` files were mutated. Repair-smoke, replay, and
leakage rows remain separate from closure admission.
