---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_negative_results_scientific_contribution_section/negative_result_contribution_matrix.csv
tags: [thesis, negative-results, contribution-draft]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_negative_results_scientific_contribution_section/README.md
task: TODO-THESIS-NEGATIVE-RESULTS-SCIENTIFIC-CONTRIBUTION-SECTION-2026-07-21
date: 2026-07-21
role: Writer/Reviewer/Tester
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Negative Results As Scientific Contributions

The thesis contribution is not only the final predictive model path. A central
scientific result is the admission workflow itself: it rejects closure labels
that would make the reduced model look simpler while hiding invalid physics or
data leakage.

- **runtime_and_split_gatekeeping**: The thesis shows that a predictive-model pipeline can be made auditable before prediction, with runtime and split leakage detected as first-class failure modes. Evidence: `checks=8; leakage_failures=0; fit_enabled_final_rows=0`. Boundary: Do not claim final predictive accuracy from S0-S3.
- **recirculation_blocks_ordinary_upcomer**: The thesis rejects tempting ordinary pipe `Nu/f_D/K` closure labels where RAF/RMF/SVF evidence shows materially recirculating flow. Evidence: `ordinary_candidates=90; reverse_flow_rows=45; ordinary_upcomer_admitted=0; exchange_cell_admitted=0`. Boundary: Do not claim ordinary upcomer `Nu/f_D/K` or exchange-cell coefficients.
- **pressure_f6_non_admission**: The thesis replaces clipped K, negative loss, and global multipliers with source-envelope, pressure-basis, recirculation, and same-QOI uncertainty ownership. Evidence: `same_qoi_rows_reviewed=83; pressure_corner_rows_reviewed=3; component_K/F6/clipped_K admissions=0`. Boundary: Do not claim component K, F6 fit, clipped K, negative loss, or global pressure multiplier.
- **source_property_split_blocks_hidden_release**: The thesis demonstrates that source/property labels can prevent hidden training leakage and broad release of protected rows. Evidence: `candidate_rows=1110; missing_labels=0; fit_allowed=0; model_selection_allowed=0`. Boundary: Do not treat label completeness as fit/model-selection release.
- **blocked_frozen_scorecard_is_a_result**: The thesis can show the exact missing evidence between diagnostic model forms and final predictive claims. Evidence: `final_score_values=0; split_rows=16; fit_allowed=0; model_selection_allowed=0`. Boundary: Do not claim final frozen mdot/temperature accuracy.
- **sensor_map_prevents_temperature_leakage**: The thesis separates sensor score interpretation from model construction, making TP/TW residuals secondary diagnostics rather than hidden calibration anchors. Evidence: `sensors=17; mapped=1; bounded=15; excluded=1; runtime_temperature_allowed=0; fit_allowed=0`. Boundary: Do not use TP/TW temperatures as runtime inputs, fit targets, or proof of final predictive accuracy.

These results should be presented as disciplined findings, not apologies. They
show where the final predictive model must add evidence before claiming
runtime-legal mdot and temperature prediction from setup inputs.
