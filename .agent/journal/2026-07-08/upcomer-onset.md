# Upcomer Onset

Date: `2026-07-08`
Task: `TODO-UPCOMER-ONSET`
Role: Writer / Implementer
Owner: codex

## Observed Facts

- `work_products/2026-07-08_upcomer_onset/` now exists.
- It consumes AGENT-196 upcomer dataset and fit outputs.
- All admitted Salt 2/3/4 points are classified as recirculation-cell observed.
- Mesh uncertainty and corrected-Salt perturbation conclusions are explicitly
  left as work in progress.

## Inferred Interpretation

The upcomer onset figure is useful for communication, but the onset threshold
is still an extrapolated bracket rather than a calibrated closure.

## Blockers

- Three points only.
- No mesh/GCI.
- No admitted non-recirculating upcomer point.

## Files Used

- `work_products/2026-07-07_upcomer_correlation_v2/upcomer_dataset.csv`
- `work_products/2026-07-07_upcomer_correlation_v2/upcomer_correlation_fit.csv`
- `tools/analyze/build_upcomer_onset_regime_table.py`
- `tools/analyze/test_upcomer_onset_regime_table.py`
- `work_products/2026-07-08_upcomer_onset/**`

## Recommended Next Action

Design or admit operating points near the extrapolated onset band before using
the upcomer onset as a predictive regime switch.
