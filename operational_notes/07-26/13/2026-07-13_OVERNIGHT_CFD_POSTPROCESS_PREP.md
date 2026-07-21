---
provenance:
  - .agent/journal/2026-07-13/overnight-cfd-postprocess-prep.md
  - work_products/2026-07/2026-07-13/2026-07-13_overnight_cfd_postprocess_prep/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_thermal_sign_enthalpy_review/summary.json
tags: [start-here, overnight, cfd-postprocess, thermal-closure, pressure-momentum]
related:
  - .agent/status/2026-07-13_AGENT-305.md
  - .agent/BOARD.md
task: AGENT-305
date: 2026-07-13
role: Writer/Coordinator
type: operational-note
status: submitted_running
---
# 2026-07-13 Overnight CFD Postprocess Prep

Open this first tomorrow if continuing the CFD postprocess thread.

## What Is Running

Slurm job `3294001`, name `s2_coarse_T+`, was submitted from `login3` and was
initially running on `c318-011`.

Purpose: run Salt2 coarse reconstructed-`T` thermal repair smoke using the same
split reconstruction and thermal segment extraction idea that fixed medium/fine
reconstructed-`T`.

Expected output:

- `work_products/2026-07/2026-07-13/2026-07-13_salt2_coarse_thermal_repair_smoke/`

Harvest:

```bash
sacct -j 3294001 --format=JobID,JobName,State,ExitCode,Elapsed,NodeList
```

## What Was Prepared

- `tools/analyze/build_salt2_coarse_thermal_repair_smoke.py`
- `tools/analyze/build_thermal_sign_enthalpy_review.py`
- `tools/analyze/test_thermal_sign_enthalpy_review.py`
- `work_products/2026-07/2026-07-13/2026-07-13_overnight_cfd_postprocess_prep/`
- `work_products/2026-07/2026-07-13/2026-07-13_thermal_sign_enthalpy_review/`

## Current Scientific State

Pressure/momentum:

- No duplicate Salt2 pressure extraction was launched. Existing Salt2
  pressure/momentum mesh-family postprocessing is already available.
- Corrected-Q job `3293924` is still running; terminal harvest is required
  before corrected-Q pressure or thermal interpretation.

Thermal:

- Reconstructed-`T` corruption is no longer the medium/fine blocker.
- Thermal closure admission remains blocked.
- Sign/enthalpy review has `fit_admissible_count=0`.
- Lower leg likely has a q-sign label convention issue: coarse wallHeatFlux and
  enthalpy agree in direction, but repaired segment extraction calls it
  `positive_out_of_fluid_cooled`.
- Upcomer and downcomer remain diagnostic-only due recirculation and large
  wall/enthalpy residuals.

## Do Not Do

- Do not mutate native CFD solver outputs.
- Do not use repaired HTC/UA/Nu as closure-fit targets tomorrow just because
  coarse extraction finishes.
- Do not relabel upcomer/downcomer as ordinary single-stream thermal closure
  evidence without recirculation-aware review.
- Do not interpret corrected-Q while job `3293924` is still non-terminal.

## Next Best Task

If `3294001` completes successfully, create a narrow follow-up to rebuild the
thermal mesh gate with coarse/medium/fine thermal rows and explicitly classify
each QOI as publication-ready, diagnostic, or blocked.
