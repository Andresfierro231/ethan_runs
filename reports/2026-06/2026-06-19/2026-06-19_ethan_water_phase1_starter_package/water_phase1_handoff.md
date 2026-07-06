# Water Phase-1 Handoff

## Dependency readiness

- `water_branch_hydraulic_pressure`: `partial_candidate_subset_available`
  basis: existing water hydraulic evidence subset plus pressure closure by section
  next: retain current branch exclusions and rebuild from the cleaner right_leg/test_section_span/upper_leg subset first
- `water_straight_section_friction`: `not_ready_for_defended_fit`
  basis: water pressure closure by section shows only test_section_span stays uniformly positive by case
  next: rebuild defended water straight-section rows with branch/section-specific hydro closure gates
- `water_feature_keff`: `not_started_from_closure_gated_method`
  basis: no additive water feature hardening package exists yet
  next: repeat the Salt feature local-boundary-reference and then feature-path closure workflow on water
- `water_htc_nu`: `support_first_not_dependency_ready`
  basis: water section-level thermal support exists, but no defended water closure-gated branch package exists yet
  next: build the water thermal closure package with exact enthalpy/wall-heat gating before any dependency fit