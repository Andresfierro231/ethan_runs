# AGENT-110 Raw Journal

## 2026-06-23T10:48:40-05:00

### Observed output

- The existing analysis stack already preserves:
  - `p_wall_area_avg_pa`
  - `p_rgh_wall_area_avg_pa`
  - `rho_bulk_kg_m3`
  - `bulk_velocity_m_s`
- The preserved per-case package roots listed in
  `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/package_index.csv`
  all had readable `major_loss_cumulative_timeseries.csv` files.
- No existing report package in this workspace already published a dedicated
  legwise `q_dyn(s)` figure.
- Built the additive package
  `reports/2026-06-23_ethan_dynamic_pressure_profiles/` with:
  - `dynamic_pressure_profile_rows.csv`
  - `dynamic_pressure_profile_summary.csv`
  - `figure_index.csv`
  - `summary.json`
  - `README.md`
  - `13` per-case figure triplets (`png` / `svg` / `pdf`)

### Interpretation

- The answer to the scientific terminology question is "no":
  hydrostatic-corrected pressure `p_rgh` is not true dynamic pressure.
- The workspace does have the inputs needed to derive true dynamic pressure in
  the current reduced framework, because the preserved streamwise bins already
  carry `rho_bulk_kg_m3` and `bulk_velocity_m_s`.
- The new package therefore makes the distinction explicit and publishes the
  requested distance-resolved legwise `q_dyn(s)` curves without reopening the
  heavy extractor path.

### Validation

- `python -m py_compile tools/analyze/build_ethan_dynamic_pressure_profiles.py`
- `python tools/analyze/build_ethan_dynamic_pressure_profiles.py`
