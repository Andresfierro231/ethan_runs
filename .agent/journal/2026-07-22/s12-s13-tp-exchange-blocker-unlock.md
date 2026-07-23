---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s12_s13_tp_exchange_blocker_unlock/source_manifest.csv
tags: [journal, s12, s13, blocker-unlock, upcomer-exchange]
related:
  - .agent/status/2026-07-22_TODO-S12-S13-TP-EXCHANGE-BLOCKER-UNLOCK-2026-07-22.md
  - imports/2026-07-22_s12_s13_tp_exchange_blocker_unlock.json
task: TODO-S12-S13-TP-EXCHANGE-BLOCKER-UNLOCK-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Hydraulics / Forward-pred / Writer / Reviewer / Tester
type: journal
status: complete
---
# S12/S13 TP Exchange Blocker Unlock

## Attempted

Started from the generated blocker register and live board. The initially active
S12/S13 row claimed `tools/analyze/`, but preflight found that this conflicted
with the open trigger-gated S11 source/property row. I narrowed the S12/S13
claim to the board row, closeout docs, import manifest, and a new package-local
work product, then built a synthesis packet from already-landed evidence.

## Observed

S12 has a good thesis-negative-result surface: train-only metrics and residual
ownership are documented, but no candidate is reviewable for freeze.

S13 has made real progress. The endpoint-mask derivation wrote six candidate
masks, and the medium/fine exact-label rerun produced finite rows for
`Q_wall_W`, `mdot_exchange_positive_outward_proxy_kg_s`,
`tau_recirc_proxy_s`, and `wall_core_bulk_temperature_contrast_K`. The strongest
positive diagnostic is `Q_wall_W`, whose maximum medium/fine spread versus fine
is about `0.503%`. The other exchange-cell QOIs remain too mesh-sensitive for
admission.

The open-CV residual equation is now defined elsewhere, but the same-basis
residual still cannot be released because cp/property labels, throughflow
enthalpy endpoints, storage or named-loss bounds, same-label mesh/GCI, and
source/property-Qwall release are not simultaneously available.

Pressure/F6 remains adjacent context. The current inventory still has zero
ordinary F6 fit-ready rows, and CAND001 was not endpoint-ready at the last
terminal gate.

## Inferred

The best current route is not another attempt to fit or admit from the current
diagnostic rows. Progress should move through release-grade endpoint geometry,
same-basis source/property labels, strict same-label coarse or an explicit
equivalence gate, and axial mixing/upcomer stratification. That sequence is the
shortest path to a legal TP/exchange residual table and to a fair test of the
hybrid upcomer route.

## Contradictions Or Caveats

The same-day S13 evidence is useful, but it is not release-ready. Low diagnostic
spread in `Q_wall_W` does not authorize Qwall release or exchange coefficient
fitting, because the formal same-label coarse/GCI gate and source/property
release gate still fail closed.

The pressure two-tap negative result remains valid evidence for why a hybrid
pressure model is needed. It is still not a component-K or F6 fit basis.

## Next Useful Actions

1. Claim `TODO-S13-ENDPOINT-GEOMETRY-ENRICHMENT-REGENERATION-CONTRACT-2026-07-22`
   to produce release-grade throughflow endpoint masks.
2. Claim `TODO-S13-SAME-BASIS-CP-PROPERTY-OPEN-CV-PREFLIGHT-2026-07-22`
   to decide whether S13 same-basis enthalpy residual inputs can be released.
3. Claim `TODO-S13-STRICT-SAME-LABEL-COARSE-OR-EQUIVALENCE-GATE-2026-07-22`
   before any formal GCI or production harvest claim.
4. Claim `TODO-WALL-TS-AXIAL-MIXING-UPCOMER-STRATIFICATION-PREFLIGHT-2026-07-22`
   for the predictive wall/test-section blocker.
5. Claim `TODO-PRESSURE-CAND001-TERMINAL-MONITOR-READONLY-2026-07-22` only as a
   monitor row, not as a duplicate job or sampler launch.
