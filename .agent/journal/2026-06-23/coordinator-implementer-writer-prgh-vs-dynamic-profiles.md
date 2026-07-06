# AGENT-112 Raw Journal

## 2026-06-23T11:05:55-05:00

### Observed output

- The preserved case-analysis bins already carry:
  - `p_rgh_wall_area_avg_pa`
  - `p_wall_area_avg_pa`
  - `rho_bulk_kg_m3`
  - `bulk_velocity_m_s`
- No prior local package published the direct overlay of `p_rgh(s)` and
  `q_dyn(s)` for every case and leg.
- Built the additive package
  `reports/2026-06-23_ethan_prgh_vs_dynamic_profiles/` with:
  - `prgh_vs_dynamic_profile_rows.csv`
  - `prgh_vs_dynamic_profile_summary.csv`
  - `figure_index.csv`
  - `summary.json`
  - `README.md`
  - `13` per-case figure triplets (`png` / `svg` / `pdf`)

### Interpretation

- The terminology correction is now explicit in the package:
  `p_rgh` is hydrostatic-corrected pressure, not dynamic pressure.
- The new package keeps both curves on the same pressure scale so the local
  streamwise drop shape and the local kinetic scale can be compared visually.
- The README records the main development caveat: bends, corners, transitions,
  and the test section can trigger redevelopment, so these overlays should be
  read together with the existing direct/shear friction and boundary-layer
  products rather than as a standalone friction law.

### Validation

- `python -m py_compile tools/analyze/build_ethan_prgh_vs_dynamic_profiles.py`
- `python tools/analyze/build_ethan_prgh_vs_dynamic_profiles.py`
