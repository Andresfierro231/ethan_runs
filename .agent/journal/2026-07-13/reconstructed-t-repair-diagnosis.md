# Reconstructed T Repair Diagnosis

Task: `AGENT-265`
Role: Coordinator / Implementer / Tester / Writer

## Context

AGENT-245 attempted Salt2 refined closure-QOI extraction with
`--dump-temperature` and failed in medium section sampling. `reconstructPar`
completed under OpenFOAM 13, but `foamPostProcess` failed while reading
`work_products/2026-07/2026-07-09/2026-07-09_salt2_refined_closure_qoi_repair_batch/recon/medium/518/T`.
AGENT-248 later proved pressure-only sampling works when `T` is excluded.

## Observed Evidence

The AGENT-245 `foamPostProcess` log reports:

```text
wrong token type - expected Scalar, found on line 6825807 the punctuation token '-'
```

The AGENT-265 diagnostic package records:

- native/decomposed medium source `T`: `10,410,605` numeric tokens,
  `0` nonfinite;
- native/decomposed fine source `T`: `30,225,749` numeric tokens,
  `0` nonfinite;
- AGENT-245 reconstructed medium serial `T`: `5` nonfinite tokens, first
  `-nan` at line `6825807`;
- the reconstructed snippet immediately before that first `-nan` includes
  extreme finite values such as `1.145113454e+243`, while the source file at
  the same line-number neighborhood contains normal temperatures near
  `455-458 K`.

## Interpretation

This is not evidence that the native Salt2 refined temperature field is
unusable. The immediate blocker is the serial reconstructed `T` artifact used
by `foamPostProcess`: it is syntactically invalid for OpenFOAM's scalar reader
and physically implausible near the failure location.

Thermal UA/HTC/Nu should remain blocked. Pressure-only medium/fine artifacts
from AGENT-248 can remain separate evidence, but they do not repair thermal
closure.

## Recommended Repair Path

1. Create a fresh task-scoped reconstruction directory; do not overwrite native
   source or AGENT-245 artifacts.
2. Reconstruct only `T` under the same OF13 runtime and scan the serial field
   for nonfinite/extreme tokens before any `foamPostProcess`.
3. If OF13 `reconstructPar` reproduces corruption, test a decomposed/collated
   source-field sampling path or alternate version-pinned reconstruction path.
4. Only regenerate thermal closure tables after zero nonfinite reconstructed
   `T` tokens and successful `--dump-temperature` section sampling for both
   medium and fine.

## Artifacts

- `tools/analyze/diagnose_reconstructed_t_corruption.py`
- `work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_diagnosis/diagnosis.json`
- `work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_diagnosis/field_quality_summary.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_diagnosis/README.md`

## Validation

```bash
python3.11 tools/analyze/diagnose_reconstructed_t_corruption.py
```

No native solver output, live job, registry entry, or external Fluid source was
modified.
