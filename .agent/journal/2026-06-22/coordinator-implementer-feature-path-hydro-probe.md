# AGENT-093 Raw Journal — Feature-Path Hydro Probe

## 2026-06-22

- Re-read the repo rules and confirmed the new task had to stay additive:
  - no work on AGENT-072-owned shared extractor files
  - no mutation of preserved CFD outputs
- Verified that AGENT-079 through AGENT-087 were already complete from their
  status files and durable outputs, then cleaned the stale `Active` board rows
  before opening the new feature-path task.
- Confirmed that AGENT-089 was already complete on disk as of the June 22
  repair refresh, so the only remaining board work there was removing the stale
  active row.

## Probe design choice

- The blocker request called for a new extractor direction, but the safe bounded
  move in this repo was a fresh report-side probe built from preserved artifacts
  instead of another edit to shared extraction code.
- I used the preserved June 15 live case-analysis packages as the authority:
  - `feature_minor_loss_timeseries.csv`
  - `raw_extraction/leg_wall_face_geometry.csv`
  - `raw_extraction/leg_wall_face_samples.csv`
  - `major_loss_summary.csv`
- Existing June 19 feature hardening outputs were loaded only as comparison
  context, not as a replacement for the new probe.

## Label-mapping decision

- The main uncertainty was how to connect the feature endpoint NCC patch names
  to the preserved wall-face geometry labels.
- The workable rule was:
  - read each major span’s geometry-label chain from
    `leg_wall_face_geometry.csv`
  - use `major_loss_summary.csv` to map the NCC summary start/end patches onto
    the chain endpoints
  - treat those chain endpoints as the boundary labels for the new endpoint
    window probe
- This resolved both direct NCC-labeled boundaries and the Salt-family
  `TP*`/`TW*` connector labels without changing any extractor.

## Window rule

- For each retained feature row:
  - select the unique adjacent start span from the Salt feature input table
  - select the unique adjacent end span from the same table
  - on each side, take the `3` nearest unique `s_span_m` stations to the
    matched boundary
  - compute area-weighted wall means for `p`, `p_rgh`, and `T`
  - form the endpoint-window hydro candidate:
    - `Delta p_wall - Delta p_rgh_wall`
- This is intentionally a wall-window probe, not a defended full-path integral.

## Validation and outputs

- Added:
  - `tools/analyze/build_ethan_feature_path_hydro_probe.py`
  - `tools/analyze/test_ethan_feature_path_hydro_probe.py`
- Validation passed:
  - `python3.11 -m py_compile ...`
  - `python3.11 -m unittest tools.analyze.test_ethan_feature_path_hydro_probe`
  - two-case smoke build into
    `tmp/2026-06-22_ethan_feature_path_hydro_probe_smoke/`
  - full durable build into
    `reports/2026-06-22_ethan_feature_path_hydro_probe/`

## What the probe changed scientifically

- The preserved Salt packages are no longer blocked by missing endpoint-window
  support:
  - `185 / 185` retained-time rows reached `probe_ready`
  - `45 / 45` case-feature rows reached
    `probe_ready_for_downstream_review`
- The blocker therefore narrowed:
  - not “we cannot reconstruct the local endpoint evidence”
  - instead “the reconstructed wall-window hydro candidate still differs
    materially from the existing endpoint proxy and still is not a defended
    full-path integral”
- The biggest persistent mismatch is `corner_upper_right`, where the mean
  case-level gap fraction sits around `2.5`.
- `test_section_complex` also remains materially different from the current
  proxy while carrying the largest absolute hydro candidate scale.

## End state

- Marked AGENT-093 complete and moved it out of `Active`.
- Recorded the durable package and counts in the task status and import
  manifest.
