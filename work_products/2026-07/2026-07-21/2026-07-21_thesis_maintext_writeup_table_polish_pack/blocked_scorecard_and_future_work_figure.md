---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s6_blocked_scorecard_shell/blocked_scorecard_visual_table.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s9_upcomer_exchange_evidence/exchange_qoi_figure_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s10_pressure_f6_gate_waterfall/pressure_f6_gate_waterfall.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution/tw5_response_waterfall.csv
tags: [thesis, figure-draft, blocked-scorecard, future-work]
task: TODO-THESIS-MAINTEXT-WRITEUP-TABLE-POLISH-PACK-2026-07-21
date: 2026-07-21
role: Writer/Reviewer/Figures
type: work_product
status: complete
---
# Figure Draft: Blocked Scorecard And Future-Work Release Path

```mermaid
flowchart LR
    A[Current CFD evidence] --> B[Admission gates]
    B --> C{Runtime-legal candidate named?}
    C -- No --> D[Blocked scorecard shell: 0 final scores]
    C -- Yes --> E[S11 source/property refresh]
    E --> F[S15 freeze/release decision]
    F --> G[S6 final scorecard]

    H[S13 exchange harvest + same-QOI UQ] --> C
    I[Passive heat-loss physical basis] --> C
    J[Right-leg/test-section pressure anchors] --> C
```

Caption draft: The final scorecard is intentionally blocked until exactly one
runtime-legal candidate passes source/property, split, and uncertainty gates.
The next release paths are not broad tuning sweeps: they are S13 exchange
harvest/UQ, passive heat-loss physical-basis evidence, and ordinary pressure
anchors in `right_leg` or `test_section_span`. No final predictive score is
released from the current evidence.
