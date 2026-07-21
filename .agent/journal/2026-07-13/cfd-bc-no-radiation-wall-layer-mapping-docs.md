# CFD BC No-Radiation Wall-Layer Mapping Docs

Task: `AGENT-281`
Date: 2026-07-13
Role: Coordinator / Writer

## Context

AGENT-279 implemented the requested no-radiation fixed-mdot parity package.
The user then asked for the work to be super well documented and for practical
wall-layer/bulk-temperature mapping recommendations.

## Work Performed

Added durable README documentation by patching the README template inside
`tools/analyze/run_cfd_bc_no_radiation_1d_parity.py`, then regenerated the
package. The README now explains table reading order, replay modes, scientific
boundaries, and why the N2 hA/Ta replay is not wall-layer equivalent.

Added:

`work_products/2026-07/2026-07-13/2026-07-13_cfd_bc_no_radiation_1d_parity/wall_layer_bulk_temperature_mapping_recommendations.md`

## Recommendation Summary

The next implementation should not fit external hA directly against 1D bulk
temperature. It should separate:

- `T_mix_signed` for energy-conserving enthalpy balance,
- `T_fwd_bulk` for recirculating local thermal diagnostics,
- `T_path_bulk(s)` for 1D pathwise state comparison,
- `T_wall_inner` for internal effective `h/Nu`,
- `T_wall_shell` for wall-layer external boundary driving temperature,
- and `T_ext_drive = Ta + q_realized/hA` as an inverse diagnostic.

Recommended external hA mapping candidates:

- `E0_bulk`: current baseline, `q_ext = hA * (T_path_bulk - Ta)`.
- `E1_wall_shell`: preferred CFD-parity replay if near-wall samples are robust.
- `E2_low_dimensional_blend`: `T_drive = T_path_bulk + beta_family *
  (T_wall_shell - T_path_bulk)`, with a small number of section-family betas.

## Boundaries Preserved

- No Fluid source files were edited.
- No native CFD solver outputs were mutated.
- No registry or admission changes were made.
- The AGENT-279 numerical tables were regenerated only to refresh README and
  metadata from the durable builder path; results remained the same.

## Validation

- `python -m py_compile tools/analyze/run_cfd_bc_no_radiation_1d_parity.py tools/analyze/test_cfd_bc_no_radiation_1d_parity.py`
- `python tools/analyze/test_cfd_bc_no_radiation_1d_parity.py`
- `python tools/analyze/run_cfd_bc_no_radiation_1d_parity.py --strict`
- `python -m json.tool work_products/2026-07/2026-07-13/2026-07-13_cfd_bc_no_radiation_1d_parity/run_metadata.json`
- `python -m json.tool imports/2026-07-13_cfd_bc_no_radiation_wall_layer_mapping_docs.json`
