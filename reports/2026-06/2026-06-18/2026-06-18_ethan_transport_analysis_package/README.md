# Ethan Transport Analysis Package

Generated: `2026-06-18T11:25:45-05:00`

This package performs the all-runs interpretive pass that sits between
the June 17 scrutiny gate and any later manuscript promotion. It does
not reopen extraction; it classifies the current outputs into stable
family-level results, support-limited results, and contradiction-driven
follow-up items.

## Canonical Inputs

- scrutiny gate: `reports/2026-06-17_ethan_transport_scrutiny_package`
- representative Salt 2 package: `reports/2026-06-15_ethan_representative_transport_comparison`
- Salt-family campaign: `reports/2026-06-15_ethan_field_transport_campaign`
- all-runs campaign: `reports/2026-06-15_ethan_all_runs_field_transport_campaign`
- math reference: `reports/2026-06-17_ethan_streamwise_transport_math_reference/MATH_COMPANION.md`
- interpretation reference: `reports/2026-06-17_ethan_transport_interpretation_package/README.md`

## Interpretation Snapshot

- established results: `3` grouped rows
- Salt-only results: `27` grouped rows
- Water-only results: `6` grouped rows
- family-only results: `135` grouped rows
- support-limited rows: `11` grouped rows
- contradictory rows: `258` grouped rows
- blocked-from-paper rows: `0` grouped rows

## Current Promotion Candidates

- `salt_family_heat_loss_campaign` -> `04_salt_family_results` with scope `Salt 2 and Salt 4 subsets already paper-side regenerated`
- `salt_family_azimuthal_campaign` -> `04_salt_family_results` with scope `Salt 2 and Salt 4 subsets; avoid reading this as a full circumferential resolution claim`
- `salt_family_branch_thermal_campaign` -> `04_salt_family_results` with scope `left_lower_leg, test_section_span, left_upper_leg, upcomer`
- `salt_family_branch_thermal_qc_campaign` -> `04_salt_family_results` with scope `All branches; this is a support figure, not a headline result`
- `salt2_hydraulic_mechanism` -> `05_salt2_mechanism_results` with scope `Narrate broad redistribution only; do not anchor claims on blocked spans if any appear`
- `salt2_effective_thermal_mechanism` -> `05_salt2_mechanism_results` with scope `left_lower_leg, test_section_span, left_upper_leg, upcomer`
- `salt2_branch_thermal_mechanism` -> `05_salt2_mechanism_results` with scope `left_lower_leg, test_section_span, left_upper_leg, upcomer`

## Highest-Priority Contradictions

- priority `1`: `Water 1 / left_lower_leg` -> Shear-based and direct wall-registered reductions disagree on the pressure-drop direction.
- priority `1`: `Water 2 / left_lower_leg` -> Shear-based and direct wall-registered reductions disagree on the pressure-drop direction.
- priority `2`: `Salt 2 val / lower_leg` -> The branch remains interpretable internally, but one support metric is too marginal for paper promotion.
- priority `2`: `Salt 2 val / right_leg` -> Too much of the branch is masked or support-limited for a stable effective ratio claim.
- priority `2`: `Salt 2 val / upper_leg` -> Shear-based and direct wall-registered reductions share the sign but disagree materially in magnitude.
- priority `2`: `Salt 2 val / upper_leg` -> The thermal driving temperature difference approaches zero, so HTC-style ratios become unstable by design.

## Salt Paper Boundary

- This package is all-runs by design, but it does not itself promote
  assets into `../papers/3d_analysis`.
- The next stage should use the Salt-paper handoff package to stage only
  the scrutiny-cleared Salt subset and its required caveats.
