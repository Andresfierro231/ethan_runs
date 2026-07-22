---
task: TODO-S13-UPCOMER-EXCHANGE-INTERFACE-WALL-SOURCE-RECOVERY-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete_fail_closed_no_recovery
tags: [upcomer, exchange-cell, interface, wall-core, source, fail-closed]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_cv_release
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampler_manifest_preflight
---
# S13 Interface/Wall/Source Recovery

This package consumes the refreshed topology CV result and decides whether the
S13 exchange interface, recirculation mask, wall/core band, normals, `Q_wall_W`,
and source-side thermal lanes can be recovered from existing evidence.

## Decision

- cases reviewed: `3`
- released recirculation CV rows: `0`
- exchange-interface releases: `0`
- wall/core releases: `0`
- `Q_wall_W` releases: `0`
- sampler-ready rows: `0`
- production harvest allowed: `false`

The topology row released no conservative recirculation control volumes. The
largest face-connected reverse-flow components remain about `53%` of the
candidate masks, have no released right-leg wall faces, and touch unreleased
boundaries. This package therefore does not release an interface, wall/core
band, normal provenance, wall heat integration, source/sink thermal ledger,
sampler rerun, harvest, same-QOI UQ, or S11 review.

## Outputs

- `interface_wall_source_release_gate.csv`
- `interface_wall_source_recovery_decision.csv`
- `q_wall_source_release_gate.csv`
- `downstream_sampler_blocker_chain.csv`
- `s13_unblock_decision.csv`
- `next_unblock_sequence.csv`
- `source_evidence_synthesis.csv`
- `source_manifest.csv`, `no_mutation_guardrails.csv`, and `summary.json`

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state,
surface extraction, sampler/harvest, Fluid/external source, fitting/model
selection, exchange-cell admission, S11/S15/S6 trigger, or residual absorption
into internal `Nu` was changed.
