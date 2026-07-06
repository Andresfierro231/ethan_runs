# Ethan Salt Paper Handoff Package

Generated: `2026-06-18T15:01:44-05:00`

This package stages only the Salt-focused assets that remain eligible
for `../papers/3d_analysis` after the June 17 scrutiny gate, the
June 18 all-runs transport analysis pass, and the narrower June 18
interpretation-closure package. It does not edit the paper repo
directly; it maps assets into manuscript sections and preserves the
caveats required for later drafting.

## Current Science Gate

- Current closure authority: `reports/2026-06-18_ethan_transport_interpretation_closure/README.md`
- Cross-family hydraulic status: `blocked_by_excluded_hydraulic_branch`
- Headline-eligible branch-variable rows: `60`
- This handoff remains Salt-only even after the closure pass. The closure package
  narrows the scientific gate; it does not authorize cross-family manuscript claims.

## Staged Asset Summary

- `salt2_family_heat_loss` -> `04_salt_family_results` (`main_text`), scope `Salt 2 family subset only`
- `salt4_family_heat_loss` -> `04_salt_family_results` (`main_text`), scope `Salt 4 family subset only`
- `salt2_family_azimuthal_means` -> `04_salt_family_results` (`main_text_with_caveat`), scope `Salt 2 circumferential means only`
- `salt4_family_azimuthal_means` -> `04_salt_family_results` (`main_text_with_caveat`), scope `Salt 4 circumferential means only`
- `salt2_hydraulic_mechanism` -> `05_salt2_mechanism_results` (`main_text_with_caveat`), scope `Salt 2 broad redistribution only`
- `salt2_effective_thermal_mechanism` -> `05_salt2_mechanism_results` (`main_text_with_caveat`), scope `Safe Salt 2 thermal regions only`
- `salt2_branch_thermal_safe_subset` -> `05_salt2_mechanism_results` (`candidate_main_text`), scope `left_lower_leg, test_section_span, left_upper_leg, upcomer`
- `salt_family_branch_thermal_safe_subset` -> `04_salt_family_results` (`candidate_main_text`), scope `Salt 2 and Salt 4, safe branches only`
- `salt_family_branch_trust_heatmap` -> `appendix_support` (`appendix_support`), scope `All Salt branches, trust-only diagnostic`
- `salt_family_branch_support_qc` -> `appendix_support` (`appendix_support`), scope `Safe Salt branches only`
- `salt_family_branch_thermal_table` -> `04_salt_family_results` (`table_candidate`), scope `Safe-branch subset can be filtered from the staged CSV`
- `salt2_branch_thermal_table` -> `05_salt2_mechanism_results` (`table_candidate`), scope `Safe Salt 2 branches only`

## Hard Promotion Boundaries

- Salt 2 boundary-layer figures remain blocked from headline use.
- Cross-family all-runs assets stay internal; this handoff is Salt-only.
- Branch thermal promotion is limited to `left_lower_leg`, `test_section_span`, `left_upper_leg`, and `upcomer`.
- The Salt 2 hydraulic figure is staged with the scrutiny caveat that mechanism claims must stay above local direct-vs-shear disagreement spikes.
- The June 18 closure package supersedes the earlier all-runs analysis package as the final science gate for manuscript promotion decisions.
