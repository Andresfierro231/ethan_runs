# Sensor Policy Gate Opening And Hydraulic Node Run

Date: 2026-07-15

Task: AGENT-405

## Result

The three safe AGENT-373 diagnostic stages were run directly on compute node
`c318-008` into this package:

- `test_section_complex_raw_two_tap`: 3 preflight rows landed.
- `f6_ready_to_run_gate`: 4 gate rows landed.
- `fluid_reset_k_diagnostic_sweep`: 128 diagnostic rows landed.

Only the reset-K/localized-K component-separation sweep is admitted, and only
as diagnostic implementation evidence. Raw two-tap pressure extraction is not
admitted because the available extractor would mutate OpenFOAM case state.
F6 is not admitted because PM5 matched-pressure/upcomer evidence is incomplete.

## PM5 Evidence

AGENT-404 repaired the parser and recovered 3/12 PM5 rows for Salt2-lo5q
pressure/onset review. The other 9 rows require scratch-case resampling with
`rho/Re/Pr/Ri/Gr/Ra`; all 12 rows lack wallHeatFlux, so internal-Nu remains
blocked.

The previous PM5 scratch run failed to reconstruct full fields for the
incomplete cases because `controlDict` still included a disabled/missing
`system/functions` file. Do not call final F6 or internal-Nu admission until
that scratch resampling path is repaired and rerun.

## Residual Attribution

`final_hydraulic_residual_attribution.csv` is provisional. It documents where
the hydraulic residual can currently be assigned and where it remains blocked:

- test-section complex pressure drop: blocked pending staged raw two-tap.
- reset/development K separation: diagnostic-supported, not fit-admitted.
- PM5 upcomer recirculation/onset: partial Salt2-lo5q evidence only.
- F6 Re/phi closure: blocked.
- final hydraulic residual: not final.

## Guardrails

No native CFD solver outputs, registry/admission state, generated indexes, or
external `../cfd-modeling-tools` files were mutated. AGENT-405 did not launch
OpenFOAM solver or postprocessing; it consumed AGENT-404 PM5 evidence and ran
repo-local diagnostics only.
