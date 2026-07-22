# F6 Endpoint Pair Same-QOI UQ Preflight

This package performs the available endpoint-pair pressure-delta preflight for the non-upcomer F6 branch candidates.

- Endpoint pair rows: `6`
- Pressure-delta rows computed: `10`
- Diagnostic mesh-spread rows: `2`
- Time-UQ pass rows: `0`
- F6 fit/admission: `none`

The useful result is that the endpoint-definition blocker is narrowed to concrete clean station pairs: `right_leg__s03->right_leg__s01` and `test_section_span__s03->test_section_span__s01`.
The remaining blockers are raw reverse-flow metrics and same-QOI time-window UQ; Salt2 mesh spread is diagnostic only until GCI provenance is declared.
