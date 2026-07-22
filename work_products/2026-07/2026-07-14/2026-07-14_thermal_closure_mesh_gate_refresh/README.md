# Thermal / Closure Mesh Gate Refresh

Task: `AGENT-309`

Generated: `2026-07-14T11:12:22-05:00`

## Purpose

This package refreshes the mesh gate after the Salt2 coarse thermal repair smoke
landed. It keeps repair-smoke evidence separate from closure admission, carries
forward prior nonthermal closure-QOI decisions, and rebuilds the thermal segment
rows with coarse/medium/fine availability.

## Result

- Unified QOI rows: `25`
- Thermal QOI rows: `7`
- Closure/nonthermal QOI rows carried forward: `18`
- Publication-ready GCI rows: `0`
- Fit-admissible thermal rows: `0`
- Main status: `no_publication_ready_gci_rows`

Classification counts:

```json
{
  "publication-ready GCI": 0,
  "diagnostic-only": 0,
  "blocked-sign-review": 5,
  "blocked-downcomer-policy": 1,
  "blocked-missing-triplet": 5,
  "non-monotone/oscillatory": 14
}
```

## Outputs

- `refreshed_qoi_mesh_gate_status.csv`: unified thermal plus closure QOI table
  with coarse/medium/fine availability, classification, blockers, and exact
  source paths.
- `thermal_mesh_gate_qois.csv`: refreshed thermal-only rows from coarse,
  medium, and fine repair-smoke CSVs.
- `thermal_mesh_gate_evidence.csv`: source package evidence.
- `blocked_or_diagnostic_qois.csv`: every non-publication-ready row.
- `thermal_admission_table.csv`: explicit fit/validation/blocked decision for
  lower-leg, upcomer, and downcomer wallHeatFlux, enthalpy, segment duty,
  HTC, UA', and Nu rows.
- `sign_convention_table.csv`: sign and residual guardrails used by the memo.
- `thermal_admission_memo.md`: human-readable admission decision.
- `summary.json`: machine-readable counts and source paths.

## Interpretation Boundary

No thermal or closure row in this refresh is publication-ready. Repaired
thermal rows are diagnostic until sign/enthalpy review, heat-balance review, and
downcomer policy gates admit them. GCI values are left blank for two-level,
blocked, oscillatory, or divergent rows.
