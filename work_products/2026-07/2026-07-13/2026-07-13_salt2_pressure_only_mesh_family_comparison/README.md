# Salt2 Pressure-Only Mesh-Family Comparison

Task: `AGENT-262`

This package compares the AGENT-248 medium/fine pressure-only outputs for Salt2.
It uses existing section-pressure, segment-friction, and momentum-budget CSVs
only; no OpenFOAM extraction or solver-output mutation is performed.

## Findings

- Section-pressure sampling is present for `30` matched
  medium/fine stations across the six major spans.
- Pressure-gradient friction sign review admits only
  `left_lower_leg, left_upper_leg` as fit-safe pressure/friction rows. These rows
  are positive-loss in both medium and fine meshes with medium/fine apparent
  Darcy-friction changes below 10%.
- The pressure-gradient rows for `lower_leg, right_leg, test_section_span, upper_leg` are not fit-safe because
  AGENT-248 flags pressure recovery or sign/noise behavior.
- Momentum-corrected friction is positive and medium/fine-consistent for
  `left_lower_leg, left_upper_leg, lower_leg, right_leg, test_section_span, upper_leg`. These are fit-safe for a momentum-corrected lane,
  but the rows with strong buoyancy correction should not be conflated with raw
  pressure-gradient friction.
- Thermal closure remains blocked by reconstructed-T corruption; AGENT-262 uses pressure/friction/momentum outputs only.

## Outputs

- `pressure_station_comparison.csv`
- `friction_mesh_comparison.csv`
- `momentum_mesh_comparison.csv`
- `fit_safety_summary.csv`
- `summary.json`

## Reproduce

```bash
python3.11 tools/analyze/build_salt2_pressure_mesh_family_comparison.py
python3.11 -m unittest tools.analyze.test_salt2_pressure_mesh_family_comparison
```

## Interpretation Boundary

This is a pressure-only fit-safety review. It does not repair reconstructed `T`,
does not admit thermal UA/HTC/Nu rows, and does not make a closure-observation
table admission change.
