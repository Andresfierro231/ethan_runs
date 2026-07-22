---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampler_manifest_refresh_from_seeded_proxy/sampler_proxy_manifest.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampler_manifest_refresh_from_seeded_proxy/production_input_gate_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampler_manifest_refresh_from_seeded_proxy/downstream_gate.csv
tags: [journal, s13, upcomer-exchange, sampler-manifest, diagnostic-proxy]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-SAMPLER-MANIFEST-REFRESH-FROM-SEEDED-PROXY-2026-07-21.md
  - imports/2026-07-21_s13_upcomer_exchange_sampler_manifest_refresh_from_seeded_proxy.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampler_manifest_refresh_from_seeded_proxy/README.md
task: TODO-S13-UPCOMER-EXCHANGE-SAMPLER-MANIFEST-REFRESH-FROM-SEEDED-PROXY-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Reviewer / Tester / Writer
type: journal
status: complete
---
# S13 Upcomer Exchange Sampler Manifest Refresh From Seeded Proxy

Observed: the diagnostic average package gives Salt2/Salt3/Salt4 finite proxy
rows for seeded volume, average `U/T/rho`, source/sink context, positive outward
exchange mass-flux proxy, `tau_recirc_proxy`, and `hA_source_side_proxy`.

Observed: the sampled-field/Qwall contract is a global gate table, not a
per-case table. It opens only limited field extraction and keeps production
sampler refresh blocked.

Attempted: joined per-case diagnostic average rows with the global contract
gates and wrote a manifest that explicitly separates `sampler_proxy_ready` from
`production_sampler_ready`.

Observed: `3/3` cases are proxy-ready and `0/3` are production sampler-ready.
The production input gate matrix still blocks on pressure, viscosity, wall heat
flux/`Q_wall_W`, `cp`, same-QOI UQ, production harvest, and coefficient
admission.

Inferred: S13 now has a durable nonproduction sampler proxy handoff for thesis
and S12 diagnostic reasoning, but it still cannot support production exchange
flux admission, coefficient admission, or S11/S15/S6 triggers.

Caveat: the proxy rows use average reductions and source-side thermal context.
They are not sampled wall/interface production QOIs and must not be relabeled as
sampler harvest evidence.

Next useful action: continue the already active limited sampled-field scheduler
extraction row for interface `U/T/rho` and wall/core `T`. That is the next
strictly documented step toward production S13, while `Q_wall_W`, pressure/cp,
same-QOI UQ, harvest, and admission remain blocked.
