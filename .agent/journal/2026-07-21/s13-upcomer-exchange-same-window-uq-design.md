---
provenance:
  generated_by: codex
  generated_at: 2026-07-21
tags:
  - s13
  - upcomer-exchange
  - same-qoi-uq
  - journal
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-SAME-WINDOW-UQ-DESIGN-2026-07-21.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_same_window_uq_design/uq_acceptance_contract.csv
---

# S13 Upcomer Exchange Same-Window UQ Design Journal

Task: `TODO-S13-UPCOMER-EXCHANGE-SAME-WINDOW-UQ-DESIGN-2026-07-21`

Observed: S9 requires same-QOI uncertainty before any exchange-cell admission. Phase A shows retained or proxy windows for exchange-related rows, but neighboring windows remain missing or terminal-gated. Phase B shows no accepted same-QOI mesh/GCI family for the exchange/terminal QOIs. Phase C keeps `V_recirc_mdot_exchange_tau_recirc`, `terminal_source_family_exchange_QOIs`, and `upcomer_exchange_heat_loss_fields` blocked.

Observed: the S13 geometry contract releases only cell VTK paths. It does not release exchange-interface VTK, wall/core VTK, or `Q_wall_W` for Salt2, Salt3, or Salt4.

Inferred: an S11-reviewable S13 exchange candidate cannot be released from retained-time evidence alone. The acceptance gate must require retained same-window value, both neighboring windows, same-QOI mesh/GCI, and released geometry/source inputs for the same QOI label/formula/sign/basis.

Contradiction/caveat: cell VTK readiness is real and useful, but it does not unblock exchange flux, residence time, wall/core thermal contrast, or energy residual harvest without surface/source lanes.

Next useful actions: keep the UQ contract as the S13 gate, complete or fail-close surface disposition, then run sampler manifest preflight. Do not launch production harvest until all manifest rows pass the reusable scaffold validator.
