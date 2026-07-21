---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_coupled_admission/README.md
tags: [journal, AGENT-494, wall-circuit, test-section, predictive-1d]
related:
  - .agent/status/2026-07-17_AGENT-494.md
  - imports/2026-07-17_wall_test_section_coupled_admission.json
task: AGENT-494
date: 2026-07-17
role: Implementer/Tester/Writer
type: journal
status: complete
---
# Wall/Test-Section Coupled Admission

## Why This Exists

AGENT-492 removed the short-timeout sub-blocker for cooler scoring and
identified `PB1_total_hA_heater_power_drive_p1` as the best passive-total
thermal-circuit candidate. AGENT-494 promotes PB1 into explicit PB1+cooler
coupled scenario contracts while keeping local test-section evidence separate
from passive-total cancellation.

## Files Changed

- `tools/analyze/build_wall_test_section_coupled_admission.py`
- `tools/analyze/test_wall_test_section_coupled_admission.py`
- `work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_coupled_admission/*`
- `.agent/status/2026-07-17_AGENT-494.md`
- `.agent/journal/2026-07-17/wall-test-section-coupled-admission.md`
- `imports/2026-07-17_wall_test_section_coupled_admission.json`
- additive update to `operational_notes/maps/forward-predictive-model.md`

## Observed Output

The package emits six candidate definitions: four PB1+cooler coupled
candidates and two local test-section diagnostic candidates (`TS6`, `TS7`).
It emits twelve scenario contracts and the completed coupled scorecard.

Final decision:

- PB1 passive-total static gate passes.
- Runtime audit passes.
- 12/12 PB1+HX coupled Fluid rows completed with accepted roots.
- Local TS6/TS7 test-section gates remain diagnostic/nonblocking and fail
  percent thresholds.
- 0/4 PB1+HX candidates are admitted.
- Blocker decision stays `keep_open`.

The coupled failure mode is now specific. All PB1+HX lumped/segmented
candidates improve absolute mdot error vs M3 on Salt3 validation and Salt4
holdout, but all-probe/TW RMSE worsens sharply. Representative all-probe RMSE:
PB1+HX about `53.29 K` on Salt3 and `60.55 K` on Salt4, versus M3 `17.749 K`
and `16.971 K`.

## Scheduler / Fluid Execution

Background job `3300338` is retained as scheduler provenance from the first
submission path. Background job `3300339` completed on `NuclearEnergy-dev` and
produced the final coupled scorecard rows; the package was then refreshed from
the existing coupled scorecard.

No native CFD/OpenFOAM output or external Fluid source file was mutated.

## Commands Run

- `python3 -m unittest tools.analyze.test_wall_test_section_coupled_admission`
- `python3 -m py_compile tools/analyze/build_wall_test_section_coupled_admission.py tools/analyze/test_wall_test_section_coupled_admission.py`
- `python3 tools/analyze/build_wall_test_section_coupled_admission.py`
- Slurm job `3300339`: `python3 tools/analyze/build_wall_test_section_coupled_admission.py --run-fluid --timeout-seconds 273`
- `python3 tools/analyze/build_wall_test_section_coupled_admission.py --reuse-existing-coupled --timeout-seconds 273`
- `python3 -m json.tool imports/2026-07-17_wall_test_section_coupled_admission.json`

## Next Work

Do not spend the next pass on more passive-total hA cancellation. The useful
next candidate needs local wall-temperature, wall-shape, or test-section
distribution physics that fixes the wall/probe RMSE regression while keeping
the mdot improvement. Runtime inputs must remain setup-only: no realized CFD
wallHeatFlux, CFD mdot, imposed cooler duty, realized test-section heat, or
validation/holdout temperatures.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, or external Fluid
source files were mutated. Generated docs index refresh was not run because it
is outside the AGENT-494 scope.
