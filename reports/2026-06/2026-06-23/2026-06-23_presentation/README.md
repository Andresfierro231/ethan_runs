# Presentation

Date: `2026-06-23`

## Purpose

This report is a presentation-facing summary of the major Ethan-run results and
workflow advances completed between `2026-06-09` and `2026-06-23`, with
special emphasis on the last week (`2026-06-16` through `2026-06-23`).

It is not a new analysis package. It is a provenance-backed map of what is now
finished, what those finished results support scientifically, and what
boundaries still need to stay explicit in today’s presentation.

For the presentation-local 1D scorecards in this package, `energy error`
means heater-normalized total-loss mismatch against frozen CFD:

`energy_error_w = (qhx_total_W + qambient_total_W) - (cfd_removed_w + cfd_ambient_w)`

`energy_error_pct_of_heater = 100 * abs(energy_error_w) / abs(cfd_heater_w)`

## Fast stale note

- `AGENT-104` closed after this presentation summary was first drafted. The
  correct current straight-section citation is now
  `reports/2026-06-22_ethan_salt_straight_hydraulic_sensitivity_refresh/`,
  and the frozen-state package has been refreshed to consume that June 22
  successor instead of the June 19 straight package.
- `AGENT-102` remains active. The readable external `Fluid` replay is still a
  stale reference surface because it consumes the June 19
  `ethan_cfd_informed_salt_v1` bundle and no refresh producer exists yet in
  the external repo.
- Since the earlier same-day draft, the presentation package now also stages a
  local figure pack at `reports/2026-06-23_presentation/figures/` and uses the
  completed June 23 bakeoff / redevelopment outputs directly. Slide 10 is no
  longer a placeholder for a missing local bakeoff task.
- The figure pack now also includes a presentation-local backup figure
  `D_salt1to4_metric_cards` built from the defended full-coverage June 23
  case-level bakeoff CSV. It uses the readable `Jin` progression so all four
  Salt numbers appear on one consistent scored scenario.
- This package now also includes a focused presentation-local 1D section:
  - `1d_model_slide_sequence.md`
  - `1d_model_results_tables.md`
  - `1d_model_setup_documentation.md`
  These are grounded in the current published June 23 local bakeoff and
  validation stack while the exact latest-window refresh remains in flight.

## Executive Overview

Over the last two weeks, the workspace moved from scattered case-by-case
analysis into a more coherent stack with five durable layers:

1. a canonical all-run monitor-first campaign for all `13` registered Ethan
   CFD cases
2. a reusable Salt-family field-transport workflow with streamwise, azimuthal,
   and heat-loss outputs
3. a transport scrutiny and manuscript-handoff layer that filters which CFD
   outputs are actually safe to promote into paper or presentation claims
4. a closure-to-modeling handoff that defines what the first Salt-informed 1D
   model should and should not assume
5. a stricter continuation / DOE staging discipline built around retained late
   windows and explicit heat-balance bookkeeping

The strongest current presentation-safe story is:

- the repo now has a canonical `13`-run comparison backbone
- the Salt-family postprocessing path now goes beyond monitor-only outputs and
  supports detailed streamwise and circumferential transport interpretation
- the first defensible 1D-model path is now much better bounded than it was a
  week ago
- the current continuation and bracket waves are no longer being staged as
  ad hoc relaunches; they are being managed under explicit retained-window and
  heat-balance rules

## What Changed In The Last Week

### 1. Salt results moved from package outputs into paper-ready staging

On `2026-06-16`, the core Salt transport figures and first paper tables were
promoted into the manuscript workspace without reopening extraction. The main
result was that the paper stopped being just a scaffold and gained real
evidence-carrying assets with a declared provenance hierarchy.

Primary provenance:

- `journals/2026-06/2026-06-16_ethan_runs.md`
- `reports/2026-06-15_ethan_field_transport_campaign/`
- `reports/2026-06-15_ethan_representative_transport_comparison/`
- `reports/2026-06-15_ethan_postprocessing_campaign_paper_handoff/`

### 2. We published a defendable dashboard and transport trust gate

On `2026-06-17`, the repo gained a durable nondimensional dashboard and a
separate transport scrutiny gate. The dashboard consolidated the currently
comparable Ethan set into `13` rows (`9` salt, `4` water). The scrutiny gate
separated transport outputs into promotion classes instead of treating every
available figure as equally trustworthy.

Key quantitative outcomes:

- dashboard coverage: `13` rows total, `0` missing comparable case-analysis
  roots
- branch-thermal scrutiny counts:
  - `37` `paper_safe`
  - `20` `internal_only`
  - `34` `do_not_promote`
- first paper-safe Salt thermal branch subset:
  - `left_lower_leg`
  - `test_section_span`
  - `left_upper_leg`
  - `upcomer`

Primary provenance:

- `journals/2026-06/2026-06-17_ethan_runs.md`
- `reports/2026-06-17_ethan_nondimensional_dashboard_package/`
- `reports/2026-06-17_ethan_transport_scrutiny_package/`

### 3. We tightened the interpretation layer before promoting more claims

On `2026-06-18`, several follow-on packages turned the June 17 scrutiny into a
more explicit interpretation and handoff surface. This resolved the two
priority-one Water hydraulic contradiction rows into bounded exclusions rather
than leaving them as unresolved ambiguities, and it created explicit Water and
Salt hydraulic evidence subsets for later use.

The scientific effect was not “everything is now admitted.” The effect was the
opposite: the repo now says more clearly which branches are safe, contextual,
or excluded.

Primary provenance:

- `journals/2026-06/2026-06-18_ethan_runs.md`
- `reports/2026-06-18_ethan_transport_interpretation_closure/`
- `reports/2026-06-18_ethan_water_hydraulic_evidence_subset/`
- `reports/2026-06-18_ethan_salt_hydraulic_evidence_subset/`
- `reports/2026-06-18_ethan_salt_paper_handoff_package/`

### 4. The closure-to-1D-model handoff became concrete

On `2026-06-19`, the repo added a bounded handoff from the current 3D evidence
stack into the first Salt-informed 1D model. The key result was not one new
fit. It was a clearer modeling policy:

- do not treat fully developed values as automatic defaults
- keep Salt and Water as separate fitting families
- use defended direct closures only where the current CFD evidence actually
  supports them
- keep `UA'(x)` as the primary admitted thermal surface
- keep direct fitted `Nu(Re)` narrow and branch-bounded

Primary provenance:

- `journals/2026-06/2026-06-19_ethan_runs.md`
- `reports/2026-06-19_ethan_litrev_to_1d_modeling_handoff/`
- `reports/2026-06-19_ethan_closure_to_modeling_handoff/`
- `reports/2026-06-19_ethan_blocker_report_and_followon_wave/`

### 5. The frozen-state and feature-path hardening passes landed

On `2026-06-22`, the repo completed an important hardening pass around the
current Salt closure set.

Key outcomes:

- the feature-path decomposition proved the preserved patch extractor already
  contains an exact retained-time endpoint `p` vs `p_rgh` decomposition for
  the current Salt feature rows
- the path-to-proxy residuals were exact:
  - `max_path_vs_proxy_delta_p_residual_pa = 0.0`
  - `max_path_vs_proxy_delta_p_rgh_residual_pa = 0.0`
- the refreshed feature hardening reopened `21` of `45` feature case rows
- the Salt dependency package v4 now carries:
  - straight friction: `provisional_defended`
  - feature `K_eff`: `provisional_defended`
  - Salt `Nu`: `provisional_defended`
- the frozen-state results package now uses the retained late-window mean as
  the primary pseudo-steady surface and the latest retained time as the drift
  overlay

Primary provenance:

- `journals/2026-06/2026-06-22_ethan_runs.md`
- `reports/2026-06-22_ethan_feature_path_hydro_decomposition/`
- `reports/2026-06-22_ethan_salt_feature_path_hydraulic_hardening_v2/`
- `reports/2026-06-22_ethan_salt_model_dependency_package_v4/`
- `reports/2026-06-22_ethan_frozen_state_results/`
- `reports/2026-06-22_ethan_frozen_state_roadmap/`
- `.agent/status/2026-06-22_AGENT-100.md`

### 6. Continuation and DOE staging is now governed by a stricter heat-balance contract

Also on `2026-06-22`, the repo documented and applied a stricter Salt scenario
staging rule. The readable Salt 3D cases were recorded as fixed-`Q` /
mixed-contract cases rather than a clean cooler-`h` DOE, and the follow-on
Salt brackets were rebuilt around explicit residual-balanced cooling sinks.

Key outcomes:

- the future bookkeeping rule is now explicit:
  `Q_in - Q_lost = 0`, with `Q_lost = Q_removed + Q_ambient`
- six unbalanced bracket relaunches and one insulation-only optimum wave were
  canceled after failing the strict parent-reference heat gate
- the six bracket cases were rebuilt in balanced form and repacked into:
  - `3251883` `ethan_salt_hiqbal3`
  - `3251884` `ethan_salt_loqbal3`

Primary provenance:

- `journals/2026-06/2026-06-22_ethan_runs.md`
- `reports/2026-06-22_ethan_heat_balance_contract/`
- `reports/2026-06-22_ethan_balanced_salt_scenario_wave/`
- `reports/2026-06-22_ethan_packed_continuation_and_salt_wave/`
- `.agent/status/2026-06-22_AGENT-103.md`
- `.agent/status/2026-06-22_AGENT-105.md`
- `.agent/status/2026-06-22_AGENT-097.md`

### 7. Today’s queue cutover preserved the active follow-on lanes

On `2026-06-23`, the Water continuation pack and the high-Q balanced Salt pack
were migrated onto dependency-safe `normal`-queue follow-ons.

Key outcomes:

- submitted:
  - `3253879` `ethan_water_cont_nq`
  - `3253880` `ethan_salt_hiqb3_nq`
- canceled the live dedicated jobs so those follow-ons could activate
- confirmed both jobs cleared dependency hold and moved to ordinary `Priority`
  pending state

Primary provenance:

- `journals/2026-06/2026-06-23_ethan_runs.md`
- `.agent/status/2026-06-23_AGENT-106.md`
- `.agent/status/2026-06-23_AGENT-107.md`

## Two-Week Provenance Map

### June 9: Cross-case heat accounting became quantitative

The repo published the first cross-case heat-flow audit over all `13`
registered CFD cases. The main durable result was the salt-versus-water split
in ambient-loss mismatch:

- salt rows under-shot the Ethan-linked ambient-loss reference by about
  `52.78 W` on average
- water rows under-shot by only about `2.52 W`

Primary provenance:

- `journals/2026-06/2026-06-09_ethan_runs.md`
- `reports/2026-06-09_ethan_steady_state_heat_flow_audit/`

### June 10 to June 11: Salt 2 hydraulics were repaired and then disciplined

The Salt 2 case-analysis path was repaired around anchored streamwise geometry,
direct-versus-shear pressure comparison, and package provenance reuse. The
package then went through rigor and rollout gates so the repo stopped confusing
“no quarantine spans” with “fully clean scientific output.”

Primary provenance:

- `journals/2026-06/2026-06-10_ethan_runs.md`
- `journals/2026-06/2026-06-11_ethan_runs.md`
- `reports/2026-06-10_ethan_salt2_case_analysis_package/`
- `reports/2026-06-11_salt2_rigor_repair_methods_note/`

### June 12: The repo gained a canonical all-run campaign

The monitor-first Ethan postprocessing path became a reproducible canonical
campaign in the cross-model publication repo. This is still one of the most
important structural advances in the last two weeks because it established the
common evidence spine for per-run and cross-run reporting.

Key outcomes:

- `13` per-run packages
- campaign-level `run_index.csv`, `readiness_matrix.csv`, and
  `cross_run_summary.csv`
- campaign-level executive, technical, and methodology reports

Primary provenance:

- `journals/2026-06/2026-06-12_ethan_runs.md`
- `../cfd-modeling-tools/cross_model_comparison/campaigns/2026-06-12_ethan_postprocessing_all_runs_v1/`
- `reports/2026-06-15_ethan_postprocessing_campaign_paper_handoff/`

### June 15: Salt field transport became a reusable workflow

By `2026-06-15`, the repo moved beyond one-case transport experiments.

Key outcomes:

- the matched Salt 2 trio had review-clean field transport outputs on the
  corrected workflow
- the remaining Salt-family wave cleared the same availability gates
- the Salt-family field-transport campaign package was built as a reusable
  family-level product
- the all-run campaign also received a paper-facing handoff package

Primary provenance:

- `journals/2026-06/2026-06-15_ethan_runs.md`
- `reports/2026-06-15_ethan_representative_transport_comparison/`
- `reports/2026-06-15_ethan_field_transport_campaign/`
- `reports/2026-06-15_ethan_postprocessing_campaign_paper_handoff/`

### June 15 to June 22: ParaView support moved from ad hoc rendering to durable assets and operator guidance

The field-figure support layer also improved materially over the same period.

Key completed items:

- representative movie statuses: `16/16` rendered in `frames_only` mode
- representative branch-arrow statuses: `32/32` rendered
- the repo now documents the accepted handling of post-write ParaView
  `ExitCode=11`
- the repo now documents how to download reconstructed cases to a laptop for
  local ParaView inspection

Primary provenance:

- `tools/extract/2026-06-15_paraview_field_render_workflow.md`
- `operational_notes/2026-06-22_paraview_download_and_slurm_accounting.md`
- `.agent/status/2026-06-15_AGENT-075.md`
- `.agent/status/2026-06-22_AGENT-098.md`

## Presentation-Safe Takeaways

If the presentation needs a compact defended story, the following points are
the safest current backbone:

1. The repo now has one canonical, review-clean monitor-first campaign for all
   `13` Ethan CFD cases.
2. The Salt-family now also has a richer phase-2 field-transport layer with
   streamwise heat-loss, parasitic-loss, azimuthal transport, and first-pass
   boundary-layer outputs.
3. The paper/presentation layer is no longer just “whatever figures exist.”
   The repo now carries an explicit scrutiny gate and paper handoff path that
   separates safe, contextual, and excluded outputs.
4. The first Salt-informed 1D model now has a more explicit closure menu and
   should be development-aware and family-aware rather than assuming fully
   developed friction or heat transfer everywhere.
5. The current continuation and Salt scenario waves are being staged under
   explicit retained-window and heat-balance rules, not just by resubmitting
   visible case mutations.

## Assumptions For Today’s Deck

- Keep the current `10`-slide technical structure plus backups rather than
  compressing the main story.
- Stage figures locally inside the presentation package so deck assembly does
  not require browsing several report roots during the talk.
- Use only completed-package evidence for the main deck. The still-active
  external replay lane is kept explicit as a boundary rather than treated as a
  finished result.
- Use the rebuilt
  `reports/2026-06-23_ethan_1d_closure_bakeoff/baseline_full_surface/**`
  figures for Slides `8-9`, and use a new presentation-local summary figure
  for Slide `10` built from current bakeoff CSV truth.
- Keep `Salt 2 Kirst` as the representative case for both the `p_rgh` versus
  `q_dyn` explanation and the redevelopment backup so the mechanism story stays
  consistent.
- Keep the completed June 15 Salt-family streamwise heat-loss figure on Slide
  `2` until the still-active Salt heat-loss breakout lane lands and clears
  review.

## Figures To Show This Week

The presentation-local figure pack now lives at:

- `reports/2026-06-23_presentation/figures/`

The exact staged asset map, canonical source paths, and assumption notes now
live at:

- `reports/2026-06-23_presentation/figures/figure_manifest.csv`

Main-slide staged figures:

1. `01_title_salt_dashboard_overview`
2. `02_loop_heat_loss_comparison`
3. `03_bounded_pressure_closure`
4. `04_prgh_vs_qdyn_salt2_kirst`
5. `05_salt_hydraulic_agreement`
6. `06_salt_branch_usability`
7. `07_salt_heat_loss_partition`
8. `08_primary_scenario_metric_heatmap`
9. `09_primary_branch_development`
10. `10_current_1d_gap_summary`

Backups staged locally:

- `A_representative_friction_and_pressure`
- `B_primary_best_sensor_parity`
- `C_salt2_kirst_redevelopment_followon`

If only four figures fit, the best compact local set is:

- `01_title_salt_dashboard_overview`
- `02_loop_heat_loss_comparison`
- `04_prgh_vs_qdyn_salt2_kirst`
- `08_primary_scenario_metric_heatmap`

These four together show:

- the current Salt operating envelope
- the loopwise Salt heat-loss picture
- the `p_rgh` versus `q_dyn` interpretation boundary
- the main negative 1D predictiveness result

Primary provenance:

- `reports/2026-06-17_ethan_nondimensional_dashboard_package/`
- `reports/2026-06-15_ethan_field_transport_campaign/`
- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/`
- `reports/2026-06-18_ethan_salt_closure_correlation_package/`
- `reports/2026-06-23_ethan_prgh_vs_dynamic_profiles/`
- `reports/2026-06-23_ethan_1d_closure_bakeoff/`
- `reports/2026-06-23_ethan_salt_redevelopment_followon/`

## How Well Current Predictions Do

There are two separate “prediction” layers in the repo right now, and they
should not be blended in presentation language.

### 1. Finished CFD-versus-experiment comparison backbone

From the canonical all-run campaign and its paper handoff:

- Water family mean wall-temperature RMSE: `2.22 K`
- Salt family mean wall-temperature RMSE: `9.30 K`
- Water family mean external-loss absolute error: `5.95%`
- Salt family mean external-loss absolute error: `21.06%`

Campaign extrema:

- best wall-temperature RMSE:
  `val_water_test_1_coarse_mesh_laminar` at about `1.67 K`
- worst wall-temperature RMSE:
  `viscosity_screening_salt_test_1_jin_coarse_mesh` at about `17.80 K`
- best external-loss absolute error:
  `val_water_test_4_coarse_mesh_laminar` at about `4.63%`
- worst external-loss absolute error:
  `viscosity_screening_salt_test_1_jin_coarse_mesh` at about `27.36%`

The clean presentation line is:

- Water remains the stronger direct-validation family.
- Salt still carries a materially larger wall-temperature and external-loss
  mismatch even where workflow maturity is stronger.

Primary provenance:

- `../cfd-modeling-tools/cross_model_comparison/campaigns/2026-06-12_ethan_postprocessing_all_runs_v1/data/cross_run_summary.csv`
- `reports/2026-06-15_ethan_postprocessing_campaign_paper_handoff/README.md`

### 2. Readable 1D prediction surface

The best current repo-readable 1D reference numbers are still the stale
pre-refresh rows carried into the frozen-state package:

- Salt 1 best readable row:
  air-outlet error `-14.01 K`, mass-flow error `-0.50%`
- Salt 2 best readable row:
  air-outlet error `-8.69 K`, mass-flow error `+15.91%`
- Salt 3 best readable row:
  air-outlet error `-22.75 K`, mass-flow error `+8.91%`
- Salt 4 best readable row:
  air-outlet error `-26.37 K`, mass-flow error `+9.79%`

This is useful as a baseline only. It is not the current defended 1D replay.
The frozen-state package is explicit that this readable `Fluid` surface predates
the June 22 feature-path reopening and remains a stale reference until
`AGENT-102` lands the refreshed replay.

We now also have two bounded local June 23 packages that use the June 22
frozen-state Salt contract as the CFD reference surface without claiming a
refreshed external rerun:

- `reports/2026-06-23_ethan_frozen_state_1d_validation/`
- `reports/2026-06-23_ethan_1d_closure_bakeoff/`

Their main result is negative but useful:

- best full-coverage readable scenario on the primary frozen set:
  `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`
- mean primary-set errors for that row:
  - energy-loss mismatch: `11.27%` of heater
  - wall-temperature RMSE: `62.79 K`
  - centerline-temperature RMSE: `62.69 K`
  - mass-flow error: `26.69%`
- Salt 1 primary reference (`Salt 1 Kirst`) is the only case where the current
  hybrid/profile-descriptor row wins overall, and even there the remaining
  temperature miss is still large.
- Salt 2 primary references (`Salt 2 Kirst`, `Salt 2 Val`) both still prefer
  the baseline `1.0 in` / radiation-on readable row overall.
- The current hybrid/profile-descriptor family remains under-covered on the
  primary frozen set with only `3` comparison rows, so it still cannot be
  defended as the global winner over the full baseline family.
- The refreshed bakeoff package also makes one setup boundary explicit:
  the defended winner is still the baseline `1.0 in` / radiation-on member,
  while no readable global `1.4 in` Salt scenario is currently published.
  If the target CFD setup is globally `1.4 in`, treat the present winner as a
  bounded surrogate rather than a final closure verdict.

The largest frozen-CFD-vs-readable-1D misses in the current best full-coverage
row remain concentrated in the upper-side and loop-start probes:

- TP worst examples: `TP3`, `TP4`, `TP5`
- TW worst examples: `TW9`, `TW10`, `TW6`

That pattern is consistent with the current branch-boundary story:
`left_lower_leg` is the best direct thermal evidence lane, while the
upper-side/upcomer/right-side portions still need different closure handling.

Case-level breakdown for the current defended full-coverage row
`ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`:

| Frozen case | Energy error [% heater] | TW RMSE [K] | TP RMSE [K] | Mass-flow error [% vs CFD] |
| --- | ---: | ---: | ---: | ---: |
| `Salt 1 Kirst` | `16.01` | `65.31` | `65.24` | `25.45` |
| `Salt 2 Kirst` | `8.92` | `64.65` | `64.78` | `34.41` |
| `Salt 2 Val` | `8.89` | `58.40` | `58.05` | `20.21` |

This split matters for presentation:

- `Salt 1 Kirst` is the worst energy-balance row.
- `Salt 2 Kirst` is the worst mass-flow row.
- `Salt 2 Val` is the least-bad overall row, but it is still far from a
  predictive 1D replay.
- The defended mean is therefore not hiding one pathological outlier; the miss
  is broad across all three current primary Salt references.

Primary provenance:

- `reports/2026-06-22_ethan_frozen_state_results/README.md`
- `reports/2026-06-22_ethan_frozen_state_results/one_d_best_readable_rows.csv`
- `reports/2026-06-22_ethan_frozen_state_results/one_d_readable_status.csv`
- `reports/2026-06-23_ethan_frozen_state_1d_validation/README.md`
- `reports/2026-06-23_ethan_frozen_state_1d_validation/scenario_ranking.csv`
- `reports/2026-06-23_ethan_frozen_state_1d_validation/best_case_scenarios.csv`
- `reports/2026-06-23_ethan_1d_closure_bakeoff/README.md`
- `reports/2026-06-23_ethan_1d_closure_bakeoff/surface_summary.csv`
- `reports/2026-06-23_ethan_1d_closure_bakeoff/scenario_shadow_summary.csv`

## Current Correlation Inventory

The current closure and correlation authority is the June 19 handoff plus the
June 22 dependency refresh.

### Admitted now

- explicit salt material properties by branch:
  `rho(T)`, `mu(T)`, `cp(T)`, `k(T)`
- baseline straight-section Darcy reference:
  `f_D = 64 / Re`
  as a baseline or comparison surface, not as the default truth everywhere
- defended Salt straight-friction fit:
  `log(f_D) = 5.2316378122 - 0.9477837868 log(Re) + 2.9210668439 I[test_section_span]`
  with defended range about `80 <= Re <= 174`
- direct Salt `Nu(Re)` on `left_lower_leg` only:
  `log(Nu) = -3.0042709988 + 0.9607621733 log(Re)`
  with defended range about `76 <= Re <= 166`
- primary thermal surface:
  `UA'(x)` on `left_lower_leg`, `test_section_span`, `left_upper_leg`,
  `upcomer`
- secondary thermal surface:
  `HTC(x)` on the same safe subset
- readable fixed cooler sink `Q`

### Comparison or sensitivity only

- fully developed laminar circular `Nu` reference values:
  `Nu = 3.657` and `Nu = 4.364`
- Shah apparent-friction redevelopment framework
- Muzychka / Yovanovich entry-`Nu` framework
- explicit local-loss placeholder terms for contractions, expansions, elbows,
  reducers, and fittings

### Reopened but still provisional

- feature `K_eff`:
  reopened to `provisional_defended`
  on a stable patch-endpoint basis for:
  - `corner_upper_right`
  - `test_section_complex`

### Still not admitted

- Water-family dependency fits
- direct fitted `Nu` on `right_leg`
- direct fitted `Nu` on derived `upcomer`
- live cooler-side `h`
- fully defended feature-volume-integral `K_eff`

Primary provenance:

- `reports/2026-06-19_ethan_litrev_to_1d_modeling_handoff/correlation_registry.csv`
- `reports/2026-06-19_ethan_blocker_report_and_followon_wave/one_d_implementation_spec.md`
- `reports/2026-06-22_ethan_salt_model_dependency_package_v4/README.md`
- `reports/2026-06-22_ethan_salt_model_dependency_package_v4/salt_friction_fit_results.json`
- `reports/2026-06-22_ethan_salt_model_dependency_package_v4/salt_nu_fit_results.json`
- `reports/2026-06-22_ethan_salt_model_dependency_package_v4/salt_feature_keff_fit_results.json`

## Next 1D And Correlation Evaluation Lane

The bounded local scorecard and bakeoff are now in hand, so the next concrete
analysis lane is no longer “finish a local 1D comparison.” It is to replace
the stale June 19 external replay surface and then rerun the same scorecard
against the refreshed 1D bundle before reopening broader correlation hunting.

### Lane A: refresh the external replay against the current June 22 closure surface

This should answer, case by case and family by family:

- whether the refreshed readable replay still keeps
  `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1` as the best
  full-coverage row
- whether the hybrid/profile-descriptor family expands beyond its current
  `3` primary readable rows
- whether the present large misses shrink materially once the readable replay
  consumes the current straight/feature closure refresh instead of the stale
  June 19 bundle
- whether the remaining dominant miss pattern still sits on the
  upper-side/upcomer/right-side lane after the replay refresh

The next external rerun that should land first is still:

- `AGENT-102` for the refreshed 1D replay against the June 22 frozen-state
  Salt contract

### Lane B: expand the candidate correlation menu cautiously

Once Lane A lands the refreshed replay, the next step is not to replace
everything at once. It is to compare a bounded set of alternatives:

- friction:
  - current Salt straight fit
  - fully developed `64 / Re` baseline
  - Shah redevelopment sensitivity where a reset is physically credible
- thermal:
  - current primary `UA'(x)` surface library
  - current secondary `HTC(x)` surface library
  - direct `Nu(Re)` only on `left_lower_leg`
  - entry / developing-flow `Nu` sensitivities gated by `Gz`, `Pr`, and
    `Ri = Gr / Re^2`
- features:
  - current residual bucket
  - provisional reopened feature `K_eff` on the stable subset only

The right output of that lane is a scored comparison table, not a new fit by
default. We should quantify:

- prediction error by case
- prediction error by observable
- which closure changes help Salt 2, Salt 3, Salt 4, or Salt 1 separately
- which changes improve one metric while worsening another

### Concrete deliverables to open next

1. one refreshed 1D replay scorecard package comparing the external replay against the
   frozen-state Salt contract
2. one correlation bakeoff package comparing:
   - baseline friction versus fitted friction
   - `UA'` versus `HTC` versus direct `Nu` where admitted
   - optional developing-flow sensitivity flags using `Gz` and `Ri`
3. one summary table for presentation/manuscript use with:
   - best case per observable
   - worst case per observable
   - median and family-level errors
   - explicit admitted / provisional / blocked status by closure family

## Slide Outline

A slide-ready outline for today’s talk now lives at:

- `reports/2026-06-23_presentation/slide_outline.md`

That outline now does three things that this longer README does not:

- tags each proposed slide as `done` or `partial` based on current evidence
- points every slide to a staged local asset inside
  `reports/2026-06-23_presentation/figures/`
- keeps the remaining missing work focused on the external replay and later
  correlation bakeoff rather than on a missing local 1D comparison package

## Boundaries That Should Stay Explicit

- Do not present the June 12 all-run campaign as a pressure-validation
  campaign. Pressure remains an explicit boundary in that monitor-first layer.
- Do not present direct `Nu(Re)` as broadly defended across the loop. The best
  current direct internal-HTC / direct-`Nu` evidence remains narrow.
- Do not collapse Salt and Water into one closure family in presentation
  language. The current model-form and evidence stacks are still family-aware.
- Do not present the reopened feature `K_eff` basis as final. The current state
  is `provisional_defended`, not fully settled.
- Do not treat the completed local bakeoff as a refreshed external replay.
  The current local negative result is real, but it still sits on top of a
  stale June 19 readable `Fluid` bundle.
- Do not use the still-active Salt heat-loss breakout lane as if it were a
  completed deck dependency. Slide `2` intentionally stays on the completed
  June 15 campaign figure until that breakout lane lands and clears review.
- Do not count the still-active external replay lane as a completed result:
  - `AGENT-102` external Fluid replay against the frozen-state Salt contract

## Most Useful Source Roots For Today

- all-run campaign backbone:
  `../cfd-modeling-tools/cross_model_comparison/campaigns/2026-06-12_ethan_postprocessing_all_runs_v1/`
- campaign-to-paper summary:
  `reports/2026-06-15_ethan_postprocessing_campaign_paper_handoff/`
- Salt field-transport campaign:
  `reports/2026-06-15_ethan_field_transport_campaign/`
- dashboard and transport trust gate:
  `reports/2026-06-17_ethan_nondimensional_dashboard_package/`
  and `reports/2026-06-17_ethan_transport_scrutiny_package/`
- Salt paper handoff and closure subset logic:
  `reports/2026-06-18_ethan_salt_paper_handoff_package/`
  and `reports/2026-06-18_ethan_transport_interpretation_closure/`
- closure-to-modeling and 1D handoff:
  `reports/2026-06-19_ethan_litrev_to_1d_modeling_handoff/`
- frozen-state and feature-path hardening:
  `reports/2026-06-22_ethan_frozen_state_results/`
  and `reports/2026-06-22_ethan_salt_model_dependency_package_v4/`
- new June 23 pressure / bakeoff / redevelopment additions:
  `reports/2026-06-23_ethan_prgh_vs_dynamic_profiles/`,
  `reports/2026-06-23_ethan_1d_closure_bakeoff/`,
  and `reports/2026-06-23_ethan_salt_redevelopment_followon/`
- current scenario-wave and queue discipline:
  `reports/2026-06-22_ethan_heat_balance_contract/`,
  `reports/2026-06-22_ethan_balanced_salt_scenario_wave/`,
  and `reports/2026-06-22_ethan_packed_continuation_and_salt_wave/`

## Bottom Line

The last two weeks did not produce one single “final answer” package. They
produced a much more usable stack:

- a canonical all-run evidence backbone
- a richer Salt transport-analysis layer
- a cleaner trust gate for what is safe to claim
- a clearer closure handoff into 1D modeling
- a stricter staging discipline for the next continuation and DOE waves

That is enough to present a coherent status update today without pretending the
remaining active 1D replay and straight-sensitivity refresh tasks are already
finished.
