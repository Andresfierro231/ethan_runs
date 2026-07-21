# Ethan Upcomer Recirculation Evidence

Generated: `2026-06-29T18:02:11-05:00`

## Scope

- Paper-grade Salt subset only: `Salt 1 Jin`, `Salt 2 Jin`, `Salt 3 Jin`, `Salt 4 Jin`.
- Reused reduced outputs only: no new extraction wave, no new staged runtime copy, and no edits to the earlier case-analysis package roots.
- Metric contract: quantify retained-time upcomer recirculation with streamwise wall-shear reversal fractions on the derived `upcomer` branch (`left_lower_leg + test_section_span + left_upper_leg`) and contrast that against the `right_leg` control branch plus a zero-reversal textbook baseline.

## Main findings

- `Salt 1 Jin`: upcomer reversed-area fraction `0.607`, reversed abs-shear fraction `0.865`, reversed abs-heat fraction `0.591`, right-leg control `0.000`.
- `Salt 2 Jin`: upcomer reversed-area fraction `0.625`, reversed abs-shear fraction `0.848`, reversed abs-heat fraction `0.661`, right-leg control `0.000`.
- `Salt 3 Jin`: upcomer reversed-area fraction `0.663`, reversed abs-shear fraction `0.852`, reversed abs-heat fraction `0.692`, right-leg control `0.000`.
- `Salt 4 Jin`: upcomer reversed-area fraction `0.680`, reversed abs-shear fraction `0.854`, reversed abs-heat fraction `0.699`, right-leg control `0.000`.

- The current reduced stack shows a strong qualitative split: the upcomer carries broad negative streamwise wall-shear coverage while the `right_leg` control branch remains at `0.0` reversed-area fraction in every paper-grade case.
- Strongest available screen in this reused-stack pass: `Heater power` (`Spearman 1.000`, `Pearson 0.981`).

## Artifacts

- Case summary CSV: `work_products/2026-06-29_ethan_upcomer_recirculation_evidence/upcomer_recirculation_case_summary.csv`
- Predictor screen CSV: `work_products/2026-06-29_ethan_upcomer_recirculation_evidence/upcomer_recirculation_predictor_screen.csv`
- Figure-ready SVG: `reports/2026-06/2026-06-29/2026-06-29_ethan_upcomer_recirculation_evidence/figures/svg/upcomer_reverse_shear_fraction_profile.svg`

## Predictor screen

- `Re`: unavailable in the reused June 17 dashboard / case-summary stack.
- `Gr/Re^2`: unavailable in the reused June 17 dashboard / case-summary stack.
- `Heater power` via `heater_power_W`: Spearman `1.000`, Pearson `0.981`.
- `Cooler h` via `cooler_h_W_m2K`: Spearman `-0.800`, Pearson `-0.756`.
- `Mean upcomer bulk temperature` via `temp_upcomer_bulk_k`: Spearman `1.000`, Pearson `0.975`.
- `Heater-to-cooler bulk delta` via `heater_to_cooler_bulk_delta_k`: Spearman `1.000`, Pearson `0.885`.
- `Downcomer-to-upcomer bulk delta` via `downcomer_to_upcomer_bulk_delta_k`: Spearman `1.000`, Pearson `0.895`.

## Boundaries

- This package uses wall-shear reversal as a retained-time recirculation proxy, not a full volumetric recirculation fraction derived from the entire cross-section velocity field.
- Mixed provenance remains explicit: `Salt 1 Jin` still points at the latest readable June 23 latest-window root while `Salt 2-4 Jin` still reuse the June 15 reduced package roots named in the June 29 reduction-contract audit.
- `Re` and `Gr/Re^2` are not present in the reused June 17 salt dashboard CSV, so this first additive pass can only screen the currently published heater, cooler, and branch-temperature predictors.
