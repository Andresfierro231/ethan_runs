# Predictive Heat-Loss Path Package

Task: `AGENT-270`
Date: 2026-07-13
Role: Coordinator / Implementer / Tester / Writer

## Context

The requested scientific path is to move from CFD evidence toward predictive
heat loss without fitting arbitrary per-case patches. The current distinction
must stay explicit:

- OpenFOAM solves the internal velocity/temperature field; effective internal
  `h` and `Nu` are postprocessed from wall heat and bulk/wall temperature.
- The 1D model predicts an internal HTC from a pipe-flow Nu law and combines it
  with wall/insulation conduction, external convection, radiation, and HX/cooler
  resistance.

The July 9 internal-Nu model-form reference and the July 13 patch-role and
`rcExternalTemperature` packages were used as the immediate constraints.

## Work Performed

Added `tools/analyze/build_predictive_heat_loss_path.py` to synthesize the
existing evidence stack into a July 13 package:

- Segment/control-volume CFD effective thermal table from patch-role segment
  reductions, physical-interface enthalpy residuals, and available legacy
  segment HTC/UA rows.
- Cooler/HX duty comparison separating baseline 1D cooler duty from CFD cooler
  duty and fixed-mdot replay error.
- Replay mode scores for the existing P0-P4 fixed-mdot ladder.
- Low-dimensional correction candidate table for HX, external ambient,
  radiation, internal Nu, profile terms, and admission gates.
- Held-out validation readiness scaffold and uncertainty-readiness table.

Added `tools/analyze/test_predictive_heat_loss_path.py` to test sign/error
handling and conservative fit gating.

## Observed Output

Generated package:

`work_products/2026-07/2026-07-13/2026-07-13_predictive_heat_loss_path/`

Key counts:

- `15` control-volume rows.
- `3` cooler/HX duty rows.
- `15` fixed-mdot replay score rows.
- `0` thermal fit-candidate control-volume rows.

Key quantitative result:

- Baseline fixed-mdot mean absolute Tmean error: `63.746 K`.
- CFD cooler-duty-only mean absolute Tmean error: `4.456 K`.
- Mean absolute reduction: `59.290 K` (`93.009%`).

## Inference

The cooler/HX boundary mismatch is currently first-order. A defensible next
modeling step is therefore to fit a low-dimensional cooler/HX UA or
epsilon-NTU parameter before adding internal Nu multipliers or profile terms.
Internal Nu corrections should remain staged behind thermal admission, mesh,
time-window, and held-out validation gates.

## Preserved Blocks

- No thermal closure admission changes were made.
- Current effective `h`/`Nu` rows are validation/diagnostic/blocked, not
  fit-safe.
- Radiation is still inseparable from `rcExternalTemperature` wall heat flux.
- Corrected-Q and low-heat cases require separate row-specific admission before
  use as held-out validation rows.

## Verification

Passed:

- `python3.11 -m py_compile tools/analyze/build_predictive_heat_loss_path.py tools/analyze/test_predictive_heat_loss_path.py`
- `python3.11 tools/analyze/test_predictive_heat_loss_path.py`
- `python3.11 tools/analyze/build_predictive_heat_loss_path.py`
- `python3.11 -m json.tool work_products/2026-07/2026-07-13/2026-07-13_predictive_heat_loss_path/summary.json`
