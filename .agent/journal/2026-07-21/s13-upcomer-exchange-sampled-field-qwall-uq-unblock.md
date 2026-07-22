---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampled_field_qwall_uq_unblock/production_readiness_table.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampled_field_qwall_uq_unblock/qwall_or_source_side_path_decision.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampled_field_qwall_uq_unblock/same_qoi_uq_prerequisite_table.csv
tags: [journal, s13, upcomer-exchange, qwall, source-side, same-qoi-uq]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-SAMPLED-FIELD-QWALL-UQ-UNBLOCK-2026-07-21.md
  - imports/2026-07-21_s13_upcomer_exchange_sampled_field_qwall_uq_unblock.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampled_field_qwall_uq_unblock/README.md
task: TODO-S13-UPCOMER-EXCHANGE-SAMPLED-FIELD-QWALL-UQ-UNBLOCK-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# S13 Sampled-Field Qwall/UQ Unblock

Observed: limited sampled-field extraction now gives retained-window interface
`U/T/rho`, trusted-wall owner `T`, finite exchange-flow proxy, wall/core/seed
temperature contrasts, and source-side `q_net_W` context for Salt2/Salt3/Salt4.

Observed: `wallHeatFlux` remains absent, so direct `Q_wall_W` integration is
still impossible. Pressure, viscosity, `cp`, same-QOI neighboring windows, and
mesh/GCI evidence also remain absent for production use.

Attempted: built a post-extraction gate that compares the direct `Q_wall_W` path
against a distinct source-side heat-flow QOI path.

Observed: the source-side path is the smaller remaining path because `q_net_W`
and sampled thermal contrasts already exist for all three retained windows.
However, that path is not production-ready: it needs a sign/conservation
contract, source/property release, and same-QOI UQ on exact labels/formula/sign
basis. Direct `Q_wall_W` is longer because wallHeatFlux must first be recovered
or generated on trusted wall faces.

Inferred: S13 can keep advancing through a source-side-equivalent contract/UQ
row, but it still cannot harvest production exchange heat-flow evidence or
admit coefficients.

Caveat: `q_net_W` must not be called `Q_wall_W`. It can only become a separate
source-side heat-flow QOI if the next row explicitly documents the sign,
conservation relationship, source/property provenance, and same-QOI UQ.

Next useful action: claim a narrow source-side heat-flow equivalence contract
plus same-QOI UQ prerequisite row. That row should decide whether the distinct
source-side QOI is sufficient for S13/S12 diagnostic use or whether direct
wallHeatFlux recovery remains mandatory before production harvest.
