# AGENT-149 Raw Journal

## 2026-06-29

- Claimed the additive June 29 Track D upcomer-recirculation evidence lane.
- Read the June 29 relay plan plus the completed paper-case inventory and
  reduction-contract audit so this task reuses the frozen paper-grade Salt
  subset and the current mixed-provenance package roots.
- Confirmed the available reusable inputs under each case package:
  `branch_thermal_summary.csv`, `branch_thermal_profiles.csv`,
  `major_loss_summary.csv`, `bulk_cross_section_temperature_samples.csv`,
  `boundary_layer_landmark_summary.csv`, and
  `raw_extraction/azimuthal_wall_transport_{summary,timeseries}.csv`.
- Implemented `tools/analyze/build_ethan_upcomer_recirculation_evidence.py`
  and a matching unit test file that:
  - reuses the AGENT-148 `source_contract_map.csv` and `branch_map.csv`
  - computes upcomer streamwise wall-shear reversal fractions from the reused
    azimuthal wall-transport summaries
  - contrasts the derived `upcomer` branch against the zero-reversal
    `right_leg` control branch
  - renders a dependency-free SVG figure candidate so the task does not depend
    on `matplotlib`
- Ran:
  - `python3.11 -m unittest tools.analyze.test_ethan_upcomer_recirculation_evidence`
  - `python3.11 tools/analyze/build_ethan_upcomer_recirculation_evidence.py`
- Published package roots:
  - `reports/2026-06/2026-06-29/2026-06-29_ethan_upcomer_recirculation_evidence/`
  - `work_products/2026-06-29_ethan_upcomer_recirculation_evidence/`
- Headline retained-time result from the new case summary:
  - `Salt 1 Jin`: upcomer reversed-area fraction `0.607`
  - `Salt 2 Jin`: upcomer reversed-area fraction `0.625`
  - `Salt 3 Jin`: upcomer reversed-area fraction `0.663`
  - `Salt 4 Jin`: upcomer reversed-area fraction `0.680`
  - `right_leg` control stayed at `0.000` reversed-area fraction for all four
    paper-grade Salt Jin cases
- Boundary preserved in the README and machine-readable outputs:
  - this is a wall-shear reversal proxy for recirculation, not a full
    cross-section volumetric reverse-flow fraction
  - `Re` and `Gr/Re^2` were not available in the reused June 17 dashboard CSV,
    so the predictor screen only covers the currently published heater, cooler,
    and branch-temperature observables
