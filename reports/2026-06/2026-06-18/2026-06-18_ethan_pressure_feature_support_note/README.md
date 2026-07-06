# Pressure / Feature / Water Support Note

Generated: `2026-06-18T16:14:18-05:00`

## Purpose

Reuse the existing June 17 pressure / HTC / boundary-layer package to close three remaining interpretation gaps without rebuilding any additive analysis package:

1. confirm whether feature `K_eff` is ready for any family-specific use;
2. tighten the Water `test_section_span` supporting-only interpretation;
3. describe how far the hydro-corrected straight-section pressure rows can be used without changing readiness status.

## Inputs

- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/README.md`
- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/MATH_COMPANION.md`
- `reports/2026-06-18_ethan_transport_interpretation_closure/README.md`
- `reports/2026-06-18_ethan_transport_interpretation_closure/branch_thermal_interpretation.csv`

## Decisions

- Feature `K_eff`: **not ready**
- Water `test_section_span`: **supporting-only**
- Hydro-corrected straight-section pressure rows: **diagnostic-only**

## Why feature `K_eff` stays blocked

- Salt corner `K_eff` still shows mean warning fraction `0.889` with relative variation `5.365`.
- Water corner `K_eff` still shows mean warning fraction `0.325`.
- The June 17 package explicitly states that the raw package does not retain a dedicated feature-path density integral, so the residual `p_rgh` closure should not be over-read as a defended feature-loss dependency.

## Why Water `test_section_span` is stronger than the rest of Water but still not headline-safe

- Mean signed effective area-ratio HTC across the retained windows is `285.505 W/m^2/K`.
- The per-case retained-window series remains stable enough for internal comparison, but the closure package still classifies Water `test_section_span` as `contextual_only` rather than `headline_eligible`.
- The current defended reason remains the resolved driving-temperature floor, not random plotting noise.

## Pressure / hydro narrative

- Mean straight-section endpoint closure residual by family:
  - Salt: `113.041 Pa`
  - Water: `4073.071 Pa`
- Mean absolute `p_rgh` loop loss by family stays much smaller than the hydro-head proxy range, especially in Water.
- That means the hydro-corrected pressure rows are useful for methods context and sign interpretation, but not yet strong enough to promote as defended direct fitting observables.

## Reproduction

```bash
python tools/analyze/build_ethan_pressure_feature_support_note.py \
  --output-dir reports/2026-06-18_ethan_pressure_feature_support_note
```
