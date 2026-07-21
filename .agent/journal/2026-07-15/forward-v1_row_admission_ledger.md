---
task: AGENT-407
date: 2026-07-15
role: Forward-pred/BC-modeling/Internal-Nu/Coordinator/Implementer/Tester/Writer
type: journal
status: complete
tags: [forward-v1, admission, closure-ledger, predictive-1d, thesis-source]
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_forward_v1_row_admission_ledger/README.md
  - tools/analyze/build_forward_v1_row_admission_ledger.py
related:
  - .agent/status/2026-07-15_AGENT-407.md
  - imports/2026-07-15_forward_v1_row_admission_ledger.json
  - operational_notes/maps/forward-predictive-model.md
---
# Forward-v1 Row Admission Ledger

Implemented the requested row-admission ledger for forward-v1 thermal,
HX/cooler, and internal-Nu evidence.

The work intentionally does not make a final forward-v1 admission. Instead, it
turns the current evidence into row-level classes:

- `predictive_candidate`: setup-legal HX/cooler rows fit on Salt2 and scored on
  Salt3 validation plus Salt4 holdout without refit or runtime use of realized
  CFD cooler duty.
- `diagnostic_replay`: realized `wallHeatFlux` and negative-source
  test-section rows used only for residual localization and source-form
  compatibility.
- `diagnostic_upper_bound`: imposed-CFD-cooler rows that show the best possible
  correction if CFD cooler duty is already known.
- `blocked_empty_fit_set`: internal-Nu fit rows, with `0` admitted rows.

The selected current setup-legal HX lane is
`salt2_fit_constant_UA_bulk_drive`. It has all-non-Salt1 RMSE `4.63756559107 W`
in the consumed AGENT-391 cooler bakeoff and remains a candidate only until the
terminal hydraulic/cfd-pp/internal gates admit a final scorecard. The AGENT-392
`F1_heater_only + HX1_global_qhx_multiplier_on_fluid_airside` lane remains a
secondary reconciliation candidate; it has Salt4 holdout abs error
`17.5108674223 W` in the generated reconciliation table.

Internal Nu remains blocked for scientific reasons, not because the table was
omitted. AGENT-319 reports `0` fit-eligible rows; AGENT-330 reports that current
upcomer evidence is recirculating and lacks wall-bulk/Gz/onset anchors; AGENT-404
still reports `wallHeatFlux_rows=0`.

No scheduler jobs, OpenFOAM jobs, native CFD outputs, registry/admission state,
generated indexes, or external Fluid files were changed.

Validation passed with:

```bash
python3.11 tools/analyze/build_forward_v1_row_admission_ledger.py
python3.11 -m unittest tools.analyze.test_forward_v1_row_admission_ledger
python3.11 -m py_compile tools/analyze/build_forward_v1_row_admission_ledger.py tools/analyze/test_forward_v1_row_admission_ledger.py
```
