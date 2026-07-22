---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_mf17_same_qoi_wall_core_exchange_uq_execution/README.md
tags: [operational-note, mf17, same-qoi, uq]
related:
  - operational_notes/07-26/22/2026-07-22_MF15_RUNTIME_WALL_PROFILE_BASIS_GATE.md
task: TODO-MF17-SAME-QOI-WALL-CORE-EXCHANGE-UQ-EXECUTION-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / Uncertainty / Forward-pred / Implementer / Tester / Writer / Reviewer
type: operational_note
status: complete
---
# MF17 Same-QOI Wall/Core Exchange UQ Execution

Open `work_products/2026-07/2026-07-22/2026-07-22_mf17_same_qoi_wall_core_exchange_uq_execution/`.

Decision: `same_qoi_wall_core_exchange_temporal_uq_executed_no_admission`.

Executed temporal UQ QOIs:

- `Q_wall_W`
- `mdot_exchange_positive_outward_proxy_kg_s`
- `tau_recirc_proxy_s`
- `wall_core_bulk_temperature_contrast_K`

Next blockers: same-label mesh/GCI, source/property release, and same-mask
exchange control-volume energy residual.
