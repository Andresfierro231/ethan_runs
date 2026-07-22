---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s12_tp_first_upcomer_exchange_evidence_gate/summary.json
tags: [s12, tp-first, upcomer-exchange, thesis]
related:
  - .agent/status/2026-07-22_TODO-S12-TP-FIRST-UPCOMER-EXCHANGE-EVIDENCE-GATE-2026-07-22.md
task: TODO-S12-TP-FIRST-UPCOMER-EXCHANGE-EVIDENCE-GATE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Hydraulics / Tester / Writer / Reviewer
type: journal
status: complete
---
# S12 TP-First Upcomer Exchange Evidence Gate

## Attempted

Claimed a narrow S12 continuation row after the user clarified that large TP is
more important than large TW. Built a reproducible package that consumes only
existing S12/S13/signed-error outputs and reframes the next useful S12 work
around TP-first exchange/energy evidence.

## Observed

The current M3 signed-error context has lower TP RMSE than TW RMSE across the
three nominal rows:

- Salt2: TP `15.649099124890764 K`, TW `20.954929641690626 K`.
- Salt3: TP `14.060010458550964 K`, TW `19.33158461493911 K`.
- Salt4: TP `13.056066881413242 K`, TW `18.622515470716774 K`.

The TP errors remain cold-biased, so TP is still worth tracking. S12-HIAX1
train-only TP RMSE is much larger: `80.4585733904668 K`.

S13 retained-window exchange evidence has finite diagnostic rows for Salt2,
Salt3, and Salt4, including `mdot_exchange_*_proxy`, `tau_recirc_proxy_s`,
wall/core/seeded control-volume temperatures, and source-side heat-flow
proxies. Exact target-window pressure and `Q_wall_W` have been released by the
S13 exact-pressure/Qwall package, but production harvest remains separate.

## Inferred

S12 should continue, if at all, as a TP-first exchange/energy-state evidence
path. The available exchange proxies are scientifically useful because TP
responds to bulk/core state, exchange residence time, pressure-driven exchange,
and source-side energy balance. They do not yet support a correction release or
candidate freeze.

The earlier TW5/TW6 residual-owner story remains useful as physical localization
evidence, but it should not drive the next S12 execution priority if TP is the
more important thesis QOI.

## Contradictions Or Caveats

- "TP-first" does not mean S12-HIAX1 currently improves TP. It does not have a
  released candidate score, and its train-only TP residual is large.
- Existing S13 exchange rows are retained-window diagnostic proxies, not
  production-harvested, same-QOI-UQ-backed closure rows.
- Exact `Q_wall_W` release exists upstream, but this package does not release a
  new Qwall/source/property lane.

## Next Useful Actions

1. Join retained-window exchange proxies with exact pressure and `Q_wall_W` for
   the same Salt2/Salt3/Salt4 windows.
2. Audit source/property release for cp, property mode, source validity
   envelope, source use category, pressure/enthalpy basis, and energy residual
   equation sign.
3. Only after that, run same-QOI neighbor-window UQ for `mdot_exchange`,
   `tau_recirc`, wall/core temperature contrast, pressure, and energy residual.
4. Revisit S12-HIAX1 freeze only after production harvest, source/property
   release, and same-QOI UQ pass.
