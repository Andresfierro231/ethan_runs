# Salt2 Closure-QOI Mesh GCI

Task: `AGENT-284`

Generated: `2026-07-13T14:10:33-05:00`

## Purpose

This is the Salt2-first Closure-QOI mesh GCI package requested after the
terminal-harvest plan. It separates hydraulic pressure-gradient, hydraulic
momentum-corrected, and thermal segment-closure lanes.

## Result

- Numeric complete triplets: `14`.
- Numeric GCI rows computed: `14`.
- Publication-ready Closure-QOI GCI rows: `0`.
- Thermal closure-QOI GCI status: `blocked_missing_fine_thermal_extraction`.

## Outputs

- `closure_qoi_triplets.csv`: coarse/medium/fine QoI values and source gates.
- `closure_qoi_gci_results.csv`: numeric GCI diagnostics where triplets are
  complete.
- `closure_qoi_admission_decisions.csv`: publication/admission decision for
  every triplet candidate.
- `blocked_or_diagnostic_qois.csv`: rows requiring follow-up or diagnostic-only
  interpretation.
- `summary.json`: counts, source paths, and boundary metadata.

## Reproduce

```bash
python3.11 tools/analyze/build_salt2_closure_qoi_mesh_gci.py
python3.11 -m unittest tools.analyze.test_salt2_closure_qoi_mesh_gci
```

## Interpretation Boundary

`publication_ready=yes` requires a finite coarse/medium/fine triplet, admitted
source rows for the lane, monotonic convergence, a valid positive observed
order, and an accepted asymptotic-range GCI check. Thermal rows remain blocked
until Salt2 fine thermal extraction is successfully produced and reconciled.
