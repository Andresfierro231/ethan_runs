# Final Scorecard Source/Property Refresh

Task: `TODO-FINAL-SCORECARD-SOURCE-PROPERTY-REFRESH`

This package converts the AGENT-554 final-scorecard gate findings into a
derived refresh ledger. It does not rewrite the July 17 final predictive
scorecard shell, and it does not change fit, model-selection, scoring, registry,
or scheduler state.

## Outputs

- `refreshed_final_scorecard_source_property_labels.csv`: one conservative label row per final scorecard case row.
- `case_refresh_decision_matrix.csv`: original versus refreshed fit/model-selection policy.
- `source_property_gate_after_refresh.csv`: AGENT-554 gate findings on the refreshed label table.
- `remaining_source_property_todo.csv`: remaining source/property blockers after placeholder removal.
- `source_manifest.csv`: input and output provenance.
- `summary.json`: machine-readable counts.

## Result

- Case rows refreshed: `16`.
- Input AGENT-554 TODO rows: `22`.
- Blank required label rows: `0`.
- Gate findings after refresh: `4`.
- Refresh-required label-content findings after refresh: `0`.
- Admission changes: `{'none': 16}`.

The main progress is that source/property placeholder strings are removed from
the derived case label table and replaced by explicit conservative labels. The
remaining blockers are scientific gate blockers: Salt1 still lacks row-specific
branch source-envelope labels, and Salt2/Salt3/Salt4 nominal rows still carry
mixed/outside envelope plus diagnostic source-use labels.
