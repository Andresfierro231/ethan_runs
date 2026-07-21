# Salt2 Closure-QOI Mesh GCI

Date: `2026-07-13`

Task: `AGENT-284`

## Prompt

The user asked for a plan to perform Closure-QOI Mesh GCI and then asked to
implement the plan.

## Work Performed

Added a reusable builder:

`tools/analyze/build_salt2_closure_qoi_mesh_gci.py`

The script consumes:

- July 9 coarse closure observations.
- AGENT-262 Salt2 medium/fine pressure-only comparison outputs.
- AGENT-267 repaired Salt2 medium thermal segment table.

It writes:

`work_products/2026-07/2026-07-13/2026-07-13_salt2_closure_qoi_mesh_gci/`

## Observed Results

The package assembled `25` candidate Closure-QOI rows:

- `14` complete hydraulic triplets with numeric GCI diagnostics.
- `11` blocked rows, mostly thermal or missing coarse/fine triplet values.
- `0` publication-ready Closure-QOI GCI rows.

The hydraulic rows remain diagnostic because computed GCI verdicts are
oscillatory or monotonic-divergent, or because the pressure-gradient source row
is not fit-safe. Thermal closure-QOI GCI remains blocked until fine thermal
extraction and thermal triplet reconciliation are complete.

## Interpretation

Endpoint-monitor GCI readiness remains separate from Closure-QOI GCI. This
package advances the Closure-QOI work by making the blockers explicit and
reproducible, but it does not yet produce a publication-ready Salt2
Closure-QOI GCI table.

## Validation

- `python3.11 -m unittest tools.analyze.test_salt2_closure_qoi_mesh_gci`
- `python3.11 tools/analyze/build_salt2_closure_qoi_mesh_gci.py`
- JSON validation for `summary.json` and the import manifest.
