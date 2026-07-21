# Phase 2 Report Gap Scan

## Purpose

This pass treats the analytical report packages as the evidence stack behind
the journals. The goal is to identify where interpretation is already clear,
where it is only provisional, and where more analysis is still needed.

## Cluster 1: early validation and mismatch diagnosis

Primary packages:

- `2026-06-02_ethan_1d_model_discrepancy_report`
- `2026-06-02_water_laminar_claim_audit`
- `2026-06-04_ethan_direct_validation`
- `2026-06-04_ethan_essential_steadiness_audit`
- `2026-06-04_ethan_runtime_and_hypothesis_matrix`
- `2026-06-05_ethan_convergence_and_salt1_campaign`

Current interpretation:

- Clear: the repo had enough evidence to stop treating all runs as equally
  mature.
- Clear: Water convergence and Salt runtime maturity were different problems.
- Provisional: early 1D discrepancy interpretation identified real mismatch
  themes, but the later closure stack shows that the branchwise closure basis
  was not yet mature enough for final modeling decisions at that time.

More analysis needed:

- Salt 1 still carries a long shadow from this phase as the least mature Salt
  case family.
- Water should still not be retroactively upgraded just because later package
  infrastructure became stronger.

## Cluster 2: Salt 2 method repair and direct hydraulic/heat accounting

Primary packages:

- `2026-06-09_ethan_streamwise_friction_package`
- `2026-06-09_ethan_dense_streamwise_friction_package`
- `2026-06-09_ethan_steady_state_heat_flow_audit`
- `2026-06-10_ethan_salt2_case_analysis_package`
- `2026-06-11_salt2_internal_technical_report_brief`
- `2026-06-11_salt2_rigor_repair_methods_note`

Current interpretation:

- Clear: June 10 is the turning point where streamwise registration and
  provenance became good enough for later branchwise interpretation.
- Clear: heat-accounting closure can be internally consistent without implying
  that every thermal closure surface is ready for promotion.
- Provisional: the June 9 friction packages are useful precursors, but their
  own notes show they were still stepping stones toward the denser and later
  corrected package logic.

More analysis needed:

- The repo still needs a durable bridge from these Salt 2-local insights into
  later multi-case closure surfaces without assuming every branch behaves like
  the repaired Salt 2 subset.

## Cluster 3: transport rollout and trust gating

Primary packages:

- `2026-06-15_ethan_representative_transport_comparison`
- `2026-06-15_ethan_field_transport_campaign`
- `2026-06-15_ethan_all_runs_field_transport_campaign`
- `2026-06-17_ethan_pressure_htc_boundarylayer_package`
- `2026-06-17_ethan_transport_scrutiny_package`
- `2026-06-18_ethan_transport_analysis_package`
- `2026-06-18_ethan_transport_scientific_interpretation_package`
- `2026-06-18_ethan_transport_interpretation_closure`
- `2026-06-18_ethan_water_hydraulic_evidence_subset`
- `2026-06-18_ethan_salt_hydraulic_evidence_subset`
- `2026-06-18_ethan_cross_family_hydraulic_redesign_screen`

Current interpretation:

- Clear: this is the repo’s most disciplined evidence gate. The contradiction
  and scrutiny files explicitly separate stable rows from internal-only and
  excluded rows.
- Clear: Water `left_lower_leg` issues were not hand-waved away; they were
  tracked through contradiction, closure, and exclusion.
- Clear: right-leg thermal behavior and several upper-leg hydraulic rows stayed
  support-limited or disagreement-heavy.

More analysis needed:

- `transport_contradiction_priority.csv` shows repeated upper-leg direct-vs-shear
  magnitude disagreement across Salt cases.
- Right-leg thermal support stays too weak for stable effective-ratio claims.
- Boundary-layer terms remain contextual only and need a stronger retained-time
  profile contract before they can act as reusable closure inputs.

## Cluster 4: closure hardening and 1D modeling handoff

Primary packages:

- `2026-06-18_ethan_salt_closure_correlation_package`
- `2026-06-18_ethan_salt_model_dependency_package`
- `2026-06-18_ethan_salt_thermal_model_surface_ranking`
- `2026-06-19_ethan_closure_to_modeling_handoff`
- `2026-06-19_ethan_litrev_to_1d_modeling_handoff`
- `2026-06-19_ethan_salt_conclusions_package`
- `2026-06-19_ethan_salt_feature_hydraulic_hardening`
- `2026-06-19_ethan_salt_feature_path_hydraulic_hardening`
- `2026-06-19_ethan_salt_model_dependency_package_v2`
- `2026-06-19_ethan_salt_model_dependency_package_v3`
- `2026-06-19_ethan_salt_straight_hydraulic_sensitivity`
- `2026-06-19_ethan_salt_thermal_closure_hardening`
- `2026-06-19_ethan_salt_thermal_closure_hardening_v3`
- `2026-06-19_ethan_water_feature_hydraulic_readiness`
- `2026-06-19_ethan_water_readiness_handoff`
- `2026-06-19_ethan_water_thermal_closure_readiness`

Current interpretation:

- Clear: this is where the repo adopted the bounded Salt-first 1D bundle as the
  working model strategy.
- Clear: effective `UA'(x)` surfaces outranked broader direct `Nu` fits because
  the latter did not have enough defended rows.
- Clear: Water remained readiness-only by design.

More analysis needed:

- `dependency_status.csv` shows `salt_nu` still had only `2` fit-used rows in
  the final June 19 conclusions layer.
- Feature `K_eff` was still `not_defensible_yet` before the June 22 pathwise
  reopening.
- Water closure readiness is descriptive, not yet promotive; no defended Water
  dependency surface emerges from this stack.

## Cluster 5: blocker reduction, frozen-state contract, and replay boundary

Primary packages:

- `2026-06-19_ethan_blocker_report_and_followon_wave`
- `2026-06-22_ethan_feature_path_hydro_decomposition`
- `2026-06-22_ethan_feature_path_hydro_probe`
- `2026-06-22_ethan_frozen_state_results`
- `2026-06-22_ethan_frozen_state_roadmap`
- `2026-06-22_ethan_fluid_replay_against_frozen_state`
- `2026-06-22_ethan_salt_feature_path_hydraulic_hardening_v2`
- `2026-06-22_ethan_salt_model_dependency_package_v4`
- `2026-06-22_ethan_salt_straight_hydraulic_sensitivity_refresh`
- `2026-06-23_ethan_cfd_freeze_checkpoint`
- `2026-06-23_ethan_frozen_state_1d_validation`
- `2026-06-23_ethan_1d_closure_bakeoff`

Current interpretation:

- Clear: the frozen-state contract is the current best bounded 3D-to-1D
  comparison surface.
- Clear: feature `K_eff` improved materially only after explicit pathwise
  decomposition, not from runtime alone.
- Clear: the local replay/bakeoff surface is useful for ranking and filtering,
  but it is not the same thing as a refreshed external `Fluid` physics bundle.

More analysis needed:

- `data_needs.csv` and `data_needs_for_replay.csv` still identify:
  - full-path retained-time hydro support for feature `K_eff`
  - stronger late-window straight rows
  - broader retained-time thermal closure support
  - development/reset coordinates
  - cooler-loss decomposition
  - cross-family collapse testing after Water hardening
- The checkpoint package preserved a useful analysis window, but Salt 1 still
  fell short of the full `20`-step representative inventory.

## Highest-priority unclear interpretations

- Water cross-family hydraulic comparability remains unproven even after the
  contradiction closures.
- Salt upper-leg direct-vs-shear magnitude disagreement remains a recurring
  internal caution rather than a closed modeling result.
- Feature `K_eff` is better justified than before, but still provisional until
  a retained-time full-path extractor exists.
- The current external replay surface still under-represents the latest local
  closure state.
