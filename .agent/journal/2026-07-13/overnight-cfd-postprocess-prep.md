---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_thermal_sign_enthalpy_review/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_salt2_pressure_only_mesh_family_comparison/README.md
tags: [overnight, cfd-postprocess, thermal-closure, pressure-momentum, enthalpy, sign-convention]
related:
  - .agent/status/2026-07-13_AGENT-305.md
  - operational_notes/07-26/13/2026-07-13_OVERNIGHT_CFD_POSTPROCESS_PREP.md
task: AGENT-305
date: 2026-07-13
role: Coordinator/Implementer/Tester/Writer
type: journal
status: submitted_running
---
# Overnight CFD Postprocess Prep

## Question

The user asked whether there are CFD runs that need postprocessing, either
momentum-pressure or thermal, and whether overnight jobs can be launched. They
also asked for the extraction sbatch, thermal sign/enthalpy review package, and
tomorrow-facing documentation with tags/instructions.

## Observed

Momentum-pressure:

- Salt2 pressure/momentum mesh-family postprocessing is already present in
  `work_products/2026-07/2026-07-13/2026-07-13_salt2_pressure_only_mesh_family_comparison/`.
- Salt2 Closure-QOI mesh/GCI already consumes pressure-gradient and
  momentum-corrected friction triplets. Several momentum-corrected rows remain
  diagnostic because GCI verdicts are oscillatory or divergent, but this is not
  solved by re-running the same extraction tonight.
- Corrected-Q job `3293924` is still running and should be harvested only after
  terminal Slurm state.

Thermal:

- Medium and fine reconstructed-`T` thermal extraction now exist.
- The thermal mesh gate still has no coarse/medium/fine thermal triplet in the
  repaired segment-HTC workflow.
- Existing coarse enthalpy evidence is useful for sign review, but it is not a
  substitute for a same-workflow coarse HTC/UA/Nu segment extraction.

## Built

Added a coarse thermal repair-smoke wrapper:

- `tools/analyze/build_salt2_coarse_thermal_repair_smoke.py`

Added a sign/enthalpy admission-review builder and tests:

- `tools/analyze/build_thermal_sign_enthalpy_review.py`
- `tools/analyze/test_thermal_sign_enthalpy_review.py`

Generated:

- `work_products/2026-07/2026-07-13/2026-07-13_thermal_sign_enthalpy_review/`

Sign/enthalpy result:

- review rows: `3`
- blocker rows: `10`
- fit-admissible rows: `0`
- verdict: `thermal_sign_enthalpy_review_blocks_closure_admission`

Segment interpretation:

- Lower leg: coarse wallHeatFlux and coarse enthalpy both point positive, but
  the repaired segment extraction labels the row as `positive_out_of_fluid_cooled`.
  This is a sign-label conflict to audit before admission.
- Upcomer: coarse wallHeatFlux and enthalpy signs oppose each other, with
  `max_interface_recirc_ratio=0.980419` and large residual fraction. It remains
  diagnostic-only.
- Downcomer: right-leg/downcomer remains policy-blocked and also has high
  recirculation and large wall/enthalpy residual.

## Submitted

Staged and submitted:

- `work_products/2026-07/2026-07-13/2026-07-13_overnight_cfd_postprocess_prep/scripts/run_salt2_coarse_thermal_repair_smoke.sbatch`

Submission command:

```bash
ssh login3 "cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch work_products/2026-07/2026-07-13/2026-07-13_overnight_cfd_postprocess_prep/scripts/run_salt2_coarse_thermal_repair_smoke.sbatch"
```

Slurm job: `3294001`.

Initial state:

```text
3294001      s2_coarse+    RUNNING      0:0   00:00:05        c318-011
3294001.bat+      batch    RUNNING      0:0   00:00:05        c318-011
3294001.0    python3.11    RUNNING      0:0   00:00:05        c318-011
```

## Tomorrow Instructions

1. Harvest `3294001` with `sacct`.
2. If complete, validate the coarse repair-smoke summary and segment CSV.
3. Rebuild the thermal mesh gate so Salt2 thermal QOIs have coarse/medium/fine
   evidence where finite.
4. Do not admit thermal HTC/UA/Nu until:
   - repaired q-sign labels are audited;
   - enthalpy and wall heat duty agree for the segment;
   - downcomer/right-leg policy is resolved;
   - lower-leg Nu availability is resolved;
   - GCI/asymptotic or explicit diagnostic status is reported.
5. Harvest corrected-Q job `3293924` only after terminal state; do not interpret
   while running.
