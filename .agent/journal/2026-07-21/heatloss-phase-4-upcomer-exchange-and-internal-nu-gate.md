---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_throughflow_recirc_exchange_cell/model_interface_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_matched_plane_recirc_field_harvest/matched_plane_recirc_field_harvest.csv
  - work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/hybrid_1d_model_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/README.md
tags: [journal, thermal-modeling, heat-loss, upcomer, recirculation, internal-nu]
related:
  - .agent/status/2026-07-21_TODO-HEATLOSS-PHASE-4-UPCOMER-EXCHANGE-AND-INTERNAL-NU-GATE.md
  - imports/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate.json
task: TODO-HEATLOSS-PHASE-4-UPCOMER-EXCHANGE-AND-INTERNAL-NU-GATE
date: 2026-07-21
role: Thermal-modeling/Hydraulics/Forward-pred/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Heat-Loss Phase 4 Upcomer Exchange And Internal-Nu Gate

## Attempted

Built a reproducible Phase 4 gate package from existing evidence only. The
package joins the MF-04 exchange-cell dry interface, matched-plane
recirculation harvest, AGENT-467 hybrid contract, ordinary single-stream
precheck rows, Phase 2 upcomer residual ownership, and Phase 3 handoff gates.

## Observed

The `42` exchange-readiness rows include current mainline upcomer rows with
strong reverse-flow diagnostics, and the Salt2 +/-5Q hybrid rows preserve
additional wall/bulk drive proxies. The ordinary single-stream table has `90`
reopening candidates but all remain blocked or precheck-only. The MF-04
interface fields that would make a predictive exchange cell calibratable are
still absent: `V_recirc`, `mdot_exchange`, `T_recirc`, residence time,
same-window pressure residual, and same-QOI uncertainty.

## Inferred

The scientifically honest interpretation is not "fit a better Nu." Current
evidence should be used to exclude ordinary single-stream labels and to define
the next exchange-cell extraction. The residual must remain a named pressure or
energy residual target; it cannot be absorbed into internal `Nu`, F6,
component `K`, or a global multiplier.

## Contradictions Or Caveats

The aggregate exchange-cell table is a gate, not a calibration dataset. It
summarizes mainline Salt2/3/4 upcomer reverse-flow maxima but does not supply
volume masks or conservative exchange fluxes. Existing future-anchor and
terminal-gated rows remain in the detailed readiness table as diagnostic or
blocked evidence, not as fit candidates.

## Next Useful Actions

1. Run a separately claimed terminal/scoped sampler for the upcomer/test-section
   exchange lane.
2. Emit `V_recirc`, `mdot_exchange`, `T_recirc`, wall/core or wall/bulk
   temperatures, pressure residual, energy residual, and same-QOI uncertainty
   on the same retained window.
3. Keep Phase 5 trigger-gated until either a runtime-legal heat-loss candidate
   or an internal-`Nu` reopening candidate passes all gates.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
Fluid source, external repo files, staged-copy/postprocessing jobs,
fitting/tuning/model selection, blocker register, or scientific admission state
were changed.
