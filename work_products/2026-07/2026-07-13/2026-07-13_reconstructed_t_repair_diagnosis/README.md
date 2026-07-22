# Reconstructed T Repair Diagnosis

Task: `AGENT-265`

This package diagnoses the AGENT-245 thermal blocker without mutating native
solver outputs or launching a new OpenFOAM job.

## Finding

AGENT-248 already showed the native/decomposed Salt2 refined source `T` files
have zero nonfinite tokens in both medium and fine cases. The AGENT-245 serial
reconstructed medium `T` is different: it contains `-nan` tokens and implausible
finite values, and OpenFOAM fails at the first `-nan` token while reading the
field for `foamPostProcess`.

Thermal UA/HTC/Nu remains blocked. The next repair should prove a clean
reconstructed `T`, or a validated decomposed-field sampling path, before any
thermal closure claim is regenerated.

## Outputs

- `diagnosis.json`
- `field_quality_summary.csv`
