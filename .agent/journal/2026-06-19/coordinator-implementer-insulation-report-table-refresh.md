# AGENT-092 Raw Journal — Insulation Report Table Refresh

## 2026-06-19

- Opened a bounded follow-on task because the user asked for the existing
  insulation report to show the per-case optimum thicknesses and the current
  CFD thicknesses directly in the human-readable report.
- Reused the already-computed optimizer outputs. No new heavy solve was needed
  because the underlying numerical results were unchanged.

### Implementation

- Updated `tools/analyze/build_ethan_insulation_optimizer_package.py` so future
  rebuilds write:
  - `case_thickness_tables.md`
  - expanded `README.md` tables
- Added helper functions for:
  - markdown table rendering
  - experimental-case thickness rows
  - CFD-run thickness rows
- Patched the existing durable report package to match the new builder output.

### Content added to the report

- Table 1:
  - each experimental Salt/Water case
  - solver optimum thickness
  - legacy solver default thickness
  - whether the fit lands within the propagated uncertainty band
  - the current CFD thicknesses associated with that case
- Table 2:
  - each current CFD run
  - matched experimental case
  - current CFD thickness
  - solver optimum thickness
  - signed `CFD - optimum` thickness difference

### Validation

- Ran:
  - `python -m py_compile tools/analyze/build_ethan_insulation_optimizer_package.py`

### Result

- The report now answers the exact operational question without forcing the
  reader into the CSV files:
  - what thickness the solver wants for each Salt/Water case
  - what thickness the current CFD run is actually using
