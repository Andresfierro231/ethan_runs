---
provenance:
  - tools/analyze/build_1d_model_hierarchy_ablation_ladder_packet.py
  - work_products/2026-07/2026-07-22/2026-07-22_1d_model_hierarchy_ablation_ladder_packet/summary.json
task: TODO-1D-MODEL-HIERARCHY-ABLATION-LADDER-PACKET-2026-07-22
date: 2026-07-22
role: Forward-pred / Writer / Reviewer / Tester
type: journal
status: complete
tags: [journal, model-hierarchy, ablation, thesis, protected-split]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_model_hierarchy_ablation_ladder_packet
---

# 1D model hierarchy and ablation ladder

## Attempted

Claimed the open hierarchy/ablation TODO and consumed existing evidence packets:
master model-form scoreboard, setup-only UQ, S12 thermal residual disposition,
pressure-basis ladder, recirculation/onset, PM10 terminal admission, TP/TW
sensor projection, and AMX1 Fluid API handoff. Built a reproducible synthesis
packet and tests.

## Observed

Every major path has useful evidence, but none satisfies freeze conditions:

- setup-only UQ is a legal runtime contract, not a scored candidate.
- pressure/F6 evidence remains thesis-only with no admitted F6/component-K row.
- S12 thermal residual ownership is rigorous negative evidence; no candidate
  freezes.
- recirculation/onset evidence disables ordinary upcomer closures but does not
  admit exchange-cell coefficients.
- TP/TW projection supports a TP-first thermal-development path, but no
  bulk-to-TP correction is released.
- AMX1 has smoke/root-ledger support but no expansion/freeze-ready form.
- PM10 is terminal evidence for future holdout planning, not current protected
  scoring.

## Inferred

The thesis should present the model-form program as a staged ladder rather than
as a prematurely frozen final candidate. Negative results are productive here:
they define the runtime legality boundary, prevent source/property leakage, and
explain why the protected split remains intact.

## Contradictions or Caveats

The existence of diagnostic improvements, such as TP projection improvement or
terminal PM10 drift gates, does not imply release. These rows remain useful only
inside the guardrails recorded in the source packages.

## Next Useful Actions

Pursue a narrow executable unlock: either pressure ladder/streamwise pressure
maps from terminal evidence, or a physical/source-bounded bulk-to-TP offset
proof. Do not score validation, holdout, or external-test rows until an
independently frozen candidate exists.
