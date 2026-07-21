---
provenance:
  generated_by: codex
  generated_at: 2026-07-21
tags:
  - s13
  - upcomer-exchange
  - interface-wall-source
  - journal
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-INTERFACE-WALL-SOURCE-RECOVERY-2026-07-21.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_interface_wall_source_recovery/s13_unblock_decision.csv
---

# S13 Upcomer Exchange Interface/Wall/Source Recovery Journal

Task: `TODO-S13-UPCOMER-EXCHANGE-INTERFACE-WALL-SOURCE-RECOVERY-2026-07-21`

Observed: the three-case cell VTK and volume rows are ready for Salt2, Salt3,
and Salt4. The recirculation segmentation package produced right-leg
reverse-flow diagnostic masks with `136140`, `138382`, and `139994` candidate
cells, but each remains `blocked_fragmented_velocity_topology`.

Observed: the geometry contract, surface VTK disposition, normal provenance,
sampler preflight, same-window UQ design, and candidate geometry recovery all
agree that no trusted exchange interface, wall/core band, normals, wall heat
flow, source-side thermal release, same-window thermal field, or same-QOI UQ row
is sampler-ready.

Inferred: production S13 harvest remains unsafe. The existing masks are useful
for the next topology task, but they cannot be treated as released control
volumes, exchange surfaces, or wall bands.

Contradiction/caveat: the static BC source/sink ledger exists for all three
cases and is useful context, but it is not a `Q_wall_W` measurement over a
released recirculation wall band and cannot release the energy residual lane by
itself.

Next useful actions: do not rerun sampler or launch harvest from this state.
The topology-CV release row has now failed closed with face-connected
diagnostics, so the next unblocker is a new source-bounded segmentation or
geometry definition that can produce all three face-closed right-leg
recirculation CVs. Only after that should an agent derive the exchange
interface, wall/core band, normal convention, and wall/source thermal ledger;
then rerun sampler manifest preflight and launch S13 production harvest only
after all three rows pass.
