# Salt2 Pressure-Only Mesh-Family Comparison

Date: 2026-07-13
Role: Implementer / Writer
Task: AGENT-262

## Files Inspected

- `work_products/2026-07/2026-07-10/2026-07-10_salt2_refined_pressure_smoke_and_8pm_batch/README.md`
- `.agent/status/2026-07-10_AGENT-248.md`
- `.agent/journal/2026-07-10/salt2-refined-pressure-smoke-and-8pm-batch.md`
- `work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_diagnosis/README.md`
- AGENT-248 medium/fine section-pressure, segment-friction, and momentum-budget CSVs

## Files Changed

- `tools/analyze/build_salt2_pressure_mesh_family_comparison.py`
- `tools/analyze/test_salt2_pressure_mesh_family_comparison.py`
- `work_products/2026-07/2026-07-13/2026-07-13_salt2_pressure_only_mesh_family_comparison/**`
- `imports/2026-07-13_salt2_pressure_only_mesh_family_comparison.json`
- `.agent/status/2026-07-13_AGENT-262.md`
- `.agent/journal/2026-07-13/salt2-pressure-only-mesh-family-comparison.md`
- `.agent/BOARD.md` own AGENT-262 row

## Commands Run

```bash
python3.11 -m py_compile tools/analyze/build_salt2_pressure_mesh_family_comparison.py tools/analyze/test_salt2_pressure_mesh_family_comparison.py
python3.11 -m unittest tools.analyze.test_salt2_pressure_mesh_family_comparison
python3.11 tools/analyze/build_salt2_pressure_mesh_family_comparison.py
```

## Observations

The pressure-only comparison is internally consistent across medium/fine. Raw
pressure-gradient friction is fit-safe only for `left_lower_leg` and
`left_upper_leg`; four other spans are sign/pressure-recovery flagged despite
close medium/fine agreement. Momentum-corrected friction is positive in all six
spans, with strong-buoyancy cautions for `lower_leg` and `upper_leg`.

Thermal closure remains explicitly blocked by reconstructed-`T` corruption.
No OpenFOAM extraction, scheduler action, native-output mutation, registry edit,
or admission change was performed.
