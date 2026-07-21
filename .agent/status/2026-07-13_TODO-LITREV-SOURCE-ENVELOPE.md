# TODO-LITREV-SOURCE-ENVELOPE Status

Date: `2026-07-13`

Role: `Implementer / Tester / Writer`

## Observed Facts

- Built `work_products/2026-07/2026-07-13/2026-07-13_litrev_source_envelope/`.
- Primary outputs:
  - `branch_source_envelope.csv`: 90 branch/property rows.
  - `source_overlap_flags.csv`: 360 source-overlap rows.
- Chen 2017 is checked against the lit-review audited numeric envelope. Tian
  2024 is held reference-only for laminar TAMU rows. Muzychka/Yovanovich and
  Everts/Meyer remain method/gate sources pending implementation/range details.

## Inferred Interpretation

The source-envelope table should be used as a gate before promoting any
source-bounded heat-transfer or pressure-loss model. Rows marked `outside` or
`unknown` are not active closure evidence.

## Blockers

Reset distance is section-local until the reset/named-loss package maps
upstream hydraulic and thermal resets.

## Files Used

- `tools/analyze/build_litrev_source_envelope_table.py`
- `tools/analyze/test_litrev_source_envelope_table.py`
- `work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_heat_loss_path/control_volume_effective_thermal_table.csv`

## Validation

- `python3.11 tools/analyze/test_litrev_source_envelope_table.py`
- `python3.11 tools/analyze/build_litrev_source_envelope_table.py`

## Recommended Next Action

Use `source_overlap_flags.csv` before any Nu/f/K model promotion; do not promote
`outside` or `unknown` rows beyond reference or sensitivity status.

