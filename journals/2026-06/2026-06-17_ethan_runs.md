# Ethan Runs Update

Date: 2026-06-17

## Goal For Today

Build a first dashboard and quick-spec package for the Ethan CFD runs that can
support later reduced-order correlation work for water and salt separately.
The immediate questions were:

- what are the starting conditions?
- how do insulation and other thermal boundary settings differ across runs?
- what are the late-window average temperatures in the loop legs / branches?
- what lower-dimensional control variables are already available before the
  separate friction-factor and minor-loss work is folded back in?

## Observed Outputs

- Added a new bounded builder:
  [tools/analyze/build_ethan_nondimensional_dashboard_package.py](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/analyze/build_ethan_nondimensional_dashboard_package.py:1)
- Built the durable dashboard/spec package:
  [reports/2026-06-17_ethan_nondimensional_dashboard_package/README.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-17_ethan_nondimensional_dashboard_package/README.md:1)
- Published machine-readable dashboards:
  - [salt_dashboard.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-17_ethan_nondimensional_dashboard_package/salt_dashboard.csv:1)
  - [water_dashboard.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-17_ethan_nondimensional_dashboard_package/water_dashboard.csv:1)
- Published candidate-input tables:
  - [salt_candidate_correlation_inputs.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-17_ethan_nondimensional_dashboard_package/salt_candidate_correlation_inputs.csv:1)
  - [water_candidate_correlation_inputs.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-17_ethan_nondimensional_dashboard_package/water_candidate_correlation_inputs.csv:1)
- Wrote the provenance manifest:
  [imports/2026-06-17_ethan_nondimensional_dashboard_package.json](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/imports/2026-06-17_ethan_nondimensional_dashboard_package.json:1)
- Package coverage is complete for the currently comparable Ethan CFD set:
  - `13` dashboard rows total
  - `9` salt
  - `4` water
  - `0` missing case-analysis roots in the final package summary

## Theory And Approach

- Water and salt are treated as separate screening families. The immediate goal
  is not to force a single collapsed correlation, but to inventory the control
  knobs and observed late-window states cleanly enough that a later
  nondimensionalization can be argued rather than guessed.
- Effective friction factor is not treated as a primitive model input. It is a
  later derived loop- or leg-level indicator from CFD support data.
- Effective HTC / `UA'` / `R_th'` are also not treated as intrinsic local
  closure coefficients. They remain support-gated effective transport
  indicators, consistent with the June 10 and June 15 methodology boundaries:
  [journals/2026-06/2026-06-10_ethan_runs.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/journals/2026-06/2026-06-10_ethan_runs.md:1),
  [journals/2026-06/2026-06-15_ethan_runs.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/journals/2026-06/2026-06-15_ethan_runs.md:1)
- The dashboard therefore focuses on setup descriptors and state descriptors
  that are already well supported:
  - initial temperature
  - heater / cooler operating-point metadata
  - insulation thickness and wall-loss modeling descriptors
  - late-window branch and span bulk temperatures
  - late-window heat-partition fractions
  - late-window circulation strength

## Assumptions

- The metadata package is the authoritative source for starting-condition and
  setup descriptors unless the June 15 boundary-modeling report says a quantity
  is only nominal:
  [reports/2026-06-15_ethan_boundary_modeling_report/README.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-15_ethan_boundary_modeling_report/README.md:1)
- The late-window thermal state should be represented by retained-window means,
  not by a single last timestep.
- Branch temperatures are derived from retained cut-plane bulk-temperature bins
  using `bulk_temp_flow_weighted_k` when available and area-average fallback
  otherwise.
- Positive aligned mass flux is the preferred weight for bulk-temperature
  aggregation; cross-section area is the fallback when a cut plane does not
  publish a usable positive-flow value.
- No clean initial hydraulic state is published in the canonical metadata
  index, so the dashboard records that gap explicitly rather than inventing one.
- The nominal metadata field `cooler_h_W_m2K` is preserved because it can still
  help screen cases, but it is not treated as the literal governing 3D
  cooler-side coefficient because the readable `0/T` evidence shows fixed-`Q`
  cooler sink patches instead.

## Result Snapshot

- Salt-family outer insulation spans `1.40-1.65 in`; water stays at `0.40 in`.
- Salt-family late-window max branch bulk-temperature spread is about
  `7.36-8.45 K`; water is much tighter at about `1.22-1.45 K`.
- Salt-family ambient-proxy fraction is about `0.703-0.724` of heater power;
  water is about `0.448-0.462`.
- The dashboard makes the Salt 2 validation continuation stand out cleanly as a
  thicker-insulation, hotter-start case inside the salt family.

## Contradictions / Caveats

- This package does not yet publish final nondimensional groups or a final
  effective-friction scalar across all runs.
- The user’s separate friction/minor-loss work is still the gating input before
  a stronger reduced-order closure spec can be justified.
- The dashboard preserves the cooler-`h` mismatch explicitly rather than
  smoothing it away; this is an important interpretation boundary, not just a
  bookkeeping nuisance.

## Suggested Next Actions

- Join the user’s legwise/featurewise friction outputs back into the current
  dashboard rows rather than starting a second disconnected screening table.
- Decide whether the next extension should compute late-temperature fluid
  property snapshots so salt and water each get a clean Reynolds/Prandtl-style
  follow-on table.
- Keep the next correlation step family-separated unless a later audit shows a
  defensible common nondimensional collapse.

## Transport Scrutiny Gate

### Observed Outputs

- Added a new bounded scrutiny builder:
  [tools/analyze/build_ethan_transport_scrutiny_package.py](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/analyze/build_ethan_transport_scrutiny_package.py:1)
- Built the durable scrutiny package:
  [reports/2026-06-17_ethan_transport_scrutiny_package/README.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-17_ethan_transport_scrutiny_package/README.md:1)
- Wrote the provenance manifest:
  [imports/2026-06-17_ethan_transport_scrutiny_package.json](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/imports/2026-06-17_ethan_transport_scrutiny_package.json:1)
- Published the machine-readable trust gate:
  - [transport_claim_matrix.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-17_ethan_transport_scrutiny_package/transport_claim_matrix.csv:1)
  - [transport_contradiction_log.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-17_ethan_transport_scrutiny_package/transport_contradiction_log.csv:1)
  - [paper_safe_asset_map.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-17_ethan_transport_scrutiny_package/paper_safe_asset_map.csv:1)

### Theory And Approach

- This pass intentionally did not reopen extraction. It treated the finished
  June 15/17 per-case and campaign packages as the working source of truth and
  asked a narrower question: which current transport outputs are strong enough
  for manuscript claims, which are only internal diagnostics, and which should
  be blocked until the reduction logic is revisited?
- The scrutiny rubric was kept explicit and machine-enforced:
  - effective thermal ratios require high usable fraction, low warning
    fraction, and a non-collapsed minimum `|T_bulk - T_wall|`
  - hydraulic span claims require directional agreement between the shear-based
    and direct wall-registered reductions
  - boundary-layer landmarks stay context-only even when present
- The point of the package is to stop the paper layer from quietly importing
  unstable or support-limited figures simply because they already exist.

### Result Snapshot

- Effective thermal branch rows do not fail uniformly. The current trust matrix
  reports:
  - `37` branch-thermal rows `paper_safe`
  - `20` branch-thermal rows `internal_only`
  - `34` branch-thermal rows `do_not_promote`
- The first paper-safe Salt branch subset is now explicit rather than
  impressionistic:
  - `left_lower_leg`
  - `test_section_span`
  - `left_upper_leg`
  - `upcomer`
- The current paper asset gate is narrower than the raw campaign package list:
  - Salt-family heat-loss subsets: allowed
  - Salt-family azimuthal subsets: allowed with circ-mean caveat
  - Salt 2 hydraulic mechanism figure: allowed with caveat
  - Salt 2 / Salt-family branch-thermal figures: allowed only as filtered
    safe subsets with QC caveats
  - Salt 2 boundary-layer context: blocked from headline paper use

### Contradictions / Caveats

- The scrutiny package surfaced `2` hydraulic contradiction rows that still
  deserve code-level follow-up before stronger cross-family hydraulic claims:
  - `val_water_test_1_coarse_mesh_laminar / left_lower_leg`
  - `val_water_test_2_coarse_mesh_laminar / left_lower_leg`
- Those rows do not invalidate the current Salt-only paper storyline, but they
  do block any casual “all cases agree on the same hydraulic mechanism”
  phrasing.
- The scrutiny package is a trust gate, not a replacement for the June 17 math
  reference. Formula definitions still live first in:
  [reports/2026-06-17_ethan_streamwise_transport_math_reference/MATH_COMPANION.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-17_ethan_streamwise_transport_math_reference/MATH_COMPANION.md:1)

### Suggested Next Actions

- Open a separate `../papers` task before editing `3d_analysis`, then use
  [paper_safe_asset_map.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-17_ethan_transport_scrutiny_package/paper_safe_asset_map.csv:1)
  as the explicit promotion gate.
- Keep branch-thermal manuscript figures restricted to the currently safe
  branches until the blocked and marginal branches are either explained or
  excluded.
- Investigate the two water `left_lower_leg` hydraulic contradiction rows
  before strengthening any cross-family hydraulic interpretation.
