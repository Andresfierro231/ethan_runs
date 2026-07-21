# 2026-07-20 maximum analysis advance frontier

Task: `AGENT-564`

## Context

The source/property policy integration completed and the final scorecard shell
now blocks all current fit and model-selection rows. The user asked for the
blockers, next steps, and the way to maximally advance analysis, then asked to
implement that plan.

## Implemented

Created a task-owned handoff package at
`work_products/2026-07/2026-07-20/2026-07-20_max_analysis_advance_frontier/`.
The package converts the planning answer into durable CSV/JSON/README artifacts
for the next agent.

## Findings

The near-term final scorecard remains blocked because there are zero
source/property-strict fit or model-selection rows. PM10 no longer looks like a
high-leverage unblocker for ordinary/onset anchors: the current parsed evidence
is diagnostic or incomplete. The high-heat Salt4 no-recirculation jobs are the
best remaining evidence-producing path; read-only scheduler inspection showed
`3299610` and `3299620` still running.

## Next Useful Action

Claim a high-heat terminal monitor/harvest row. If the jobs are still running,
close as monitor-only. If terminal successful, harvest staged-copy outputs and
gate same-window reverse flow, regime coordinates, wall/bulk thermal drive,
pressure terms, heat ledger fields, and same-QOI uncertainty.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
Fluid source, tools, fit/model-selection state, score outputs, blocker register,
or scientific admission state were changed.
