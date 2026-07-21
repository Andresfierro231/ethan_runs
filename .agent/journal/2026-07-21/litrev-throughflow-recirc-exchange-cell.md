---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/model_form_candidates.csv
  - work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/hybrid_1d_model_contract.csv
  - reports/thesis_dossier/Chapters_and_sections/current/04_upcomer_recirculation_modeling.md
  - reports/thesis_dossier/Chapters_and_sections/current/13_two_tap_recirc_section_effective_pressure_model.md
tags: [journal, recirculation, exchange-cell, reduced-model, litrev-synthesis]
related:
  - .agent/status/2026-07-21_TODO-LITREV-THROUGHFLOW-RECIRC-EXCHANGE-CELL.md
  - imports/2026-07-21_litrev_throughflow_recirc_exchange_cell.json
task: TODO-LITREV-THROUGHFLOW-RECIRC-EXCHANGE-CELL
date: 2026-07-21
role: Thermal-modeling/Hydraulics/Implementer/Writer
type: journal
status: complete
---
# LitRev Throughflow Recirculation Exchange Cell

## Attempted

Converted the July 21 LitRev model-form candidates, the AGENT-467 hybrid
contract, current upcomer recirculation section, and two-tap recirculating
pressure model into a dry reduced-model design. The requested interface fields
were made explicit and tied to switching rules.

## Observed

MF-03 is the signed-flow junction-network candidate and applies only when a
discrete modeled branch/path changes net flow sign or a one-node junction cannot
reproduce path pressure reversal. MF-04 is the throughflow-plus-recirculation
exchange-cell candidate and applies when local reverse area/mass or a coherent
exchange volume invalidates one bulk state while the modeled branch still has
net throughflow.

AGENT-467 already blocks ordinary single-stream `Nu`, `f_D`, and component `K`
labels for current material-recirculation rows. The current two-tap pressure
section likewise keeps `corner_lower_right` rows diagnostic/section-effective
and separates `Delta_p_resid` from ordinary component `K`.

## Inferred

The reduced model should not choose between one-stream and exchange-cell modes
from a universal literature threshold. It should expose a switching interface
and leave TAMU-specific threshold calibration to a separate task. The clean
division is:

- one-stream when topology is stable and local reverse-flow metrics are below
  calibrated tolerances;
- signed network when a discrete branch/path reverses net mass flow;
- exchange cell when the branch net flow exists but local exchange creates a
  second thermodynamic state.

## Contradictions Or Caveats

The current recirculation evidence is strong enough to reject ordinary
single-stream coefficient labels, but not enough to admit `V_recirc`,
`mdot_exchange`, `T_recirc`, a pressure penalty, an energy penalty, or switching
thresholds. Current dry rows therefore remain interface and residual targets
only.

## Next Useful Actions

- Run `TODO-LITREV-RECIRCULATION-SWITCHING-CALIBRATION` to define the
  unresolved tolerance placeholders without importing universal thresholds.
- Run a CFD extraction/schema task for coherent `V_recirc`, conservative
  `mdot_exchange`, and same-window `T_recirc`.
- Hand the interface to a later exact-file Fluid/API row only after the dry
  field contract is accepted.

## Files

- `.agent/status/2026-07-21_TODO-LITREV-THROUGHFLOW-RECIRC-EXCHANGE-CELL.md`
- `imports/2026-07-21_litrev_throughflow_recirc_exchange_cell.json`
- `work_products/2026-07/2026-07-21/2026-07-21_litrev_throughflow_recirc_exchange_cell/`
