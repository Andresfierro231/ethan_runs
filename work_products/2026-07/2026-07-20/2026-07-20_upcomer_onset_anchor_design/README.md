# AGENT-559 Upcomer Onset Anchor Design

Task: `AGENT-559`

This package designs the near-onset/non-recirculating upcomer anchor evidence
contract without launching compute. It responds to the AGENT-556 contract and
the AGENT-558 result: UMX1 roots now execute, but the physical stratification
candidate is still not scorecard-ready.

## Decision

`design_complete_no_launch_from_this_row`

No scheduler action, native CFD mutation, solver/postprocessing launch, Fluid
edit, fitting, model selection, admission update, or blocker-register update
was performed.

The current blocker is not absence of a launch matrix. It is absence of
same-window onset evidence. Existing Salt2/Salt3/Salt4 upcomer rows remain
recirculating diagnostics, with `0` ordinary upcomer `Nu`, `f_D`, or
component-`K` rows admitted. A separate matched-plane extraction package is
already active with job `3305547`, and the cited high-heat Salt4 probes
`3299610` and `3299620` are monitor-only until terminal success.

## Priority Order

1. Consume PM10 matched-plane extraction when the active job lands.
2. Monitor high-heat jobs and harvest only after terminal success in a separate
   claimed row.
3. If those landed rows still do not provide a transition or ordinary-like
   anchor, launch only the two Salt3 sentinel cases first.
4. Expand to the nine-row Salt3 Q-by-insulation matrix only after the sentinel
   pair fails to bracket onset.

## Files

- `anchor_case_matrix.csv` names the bounded evidence lanes and launch order.
- `same_window_metrics_contract.csv` defines the required retained-window QOIs.
- `pressure_thermal_extraction_contract.csv` defines upcomer section outputs.
- `mesh_time_uq_contract.csv` separates interim use from closure promotion.
- `admission_gate_contract.csv` records the non-promotion gates.
- `launch_or_no_launch_decision.json` records the explicit no-launch decision.
- `source_manifest.csv` records read-only evidence.
- `summary.json` is the machine-readable closeout.

## Guardrail

Do not mark `upcomer-onset-data-sparsity` resolved, fit ordinary upcomer
coefficients, or run a UMX1 score grid until at least one transition or
ordinary-like anchor and one recirculating-side anchor have same-window reverse
flow, regime coordinates, wall/bulk thermal drive, pressure terms, heat ledger,
and same-QOI uncertainty.
