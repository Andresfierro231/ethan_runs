---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_scoring_readiness/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_fluid_api_implementation/summary.json
  - work_products/2026-07/2026-07-18/2026-07-18_blocker_research_path_next_step_synthesis/README.md
tags: [umx1, scoring-readiness, forward-predictive, start-here]
related:
  - .agent/status/2026-07-18_AGENT-543.md
  - .agent/journal/2026-07-18/umx1-scoring-readiness.md
  - imports/2026-07-18_umx1_scoring_readiness.json
task: AGENT-543
date: 2026-07-18
role: Forward-pred/Implementer/Tester/Writer
type: operational_note
status: complete
supersedes:
  - AGENT-537 hook-existence conclusion
  - AGENT-539 UMX1 blocked-until-hook statement
superseded_by:
---

# UMX1 Scoring Readiness Start Here

Task: `AGENT-543`

## Why This Exists

AGENT-537 and AGENT-539 treated UMX1 as blocked because Fluid appeared to lack a
real upcomer mixing/stratification hook. AGENT-540 superseded that hook-existence
finding: the current Fluid checkout has a no-op-default UMX1 exchange API and
focused contract tests. AGENT-543 therefore shifts the blocker from API
existence to split-legal scoring readiness.

## Open First

- `work_products/2026-07/2026-07-18/2026-07-18_umx1_scoring_readiness/README.md`
- `work_products/2026-07/2026-07-18/2026-07-18_umx1_scoring_readiness/case_split_contract.csv`
- `work_products/2026-07/2026-07-18/2026-07-18_umx1_scoring_readiness/candidate_grid_contract.csv`
- `work_products/2026-07/2026-07-18/2026-07-18_umx1_scoring_readiness/runtime_input_audit.csv`
- `work_products/2026-07/2026-07-18/2026-07-18_umx1_scoring_readiness/score_gate_contract.csv`

## Trusted Contract

- Training/model selection: Salt1, Salt2, and Salt4 nominal only.
- Holdout: Salt3 nominal, never used to choose multiplier, bounds, roots,
  exclusions, or fallback policy.
- Blind score-only: Salt2 +/-5Q and `val_salt2` after adapters and release gates
  exist.
- Candidate grid: one scalar, `upcomer_exchange_multiplier`, with disabled `0.0`
  baseline and bounded positive values declared before scoring.
- Runtime audit: measured TP/TW, measured mdot, measured cooler duty, realized
  CFD wallHeatFlux, and holdout/blind residuals are forbidden runtime inputs.
- Scoring order: runtime legality, accepted roots, conservation residual, train
  score, Salt3 holdout, probe localization, blind release, admission review.

## Remaining Blockers

No Fluid API blocker remains for UMX1. The next blocker is execution authority
and output-root ownership for a tiny Fluid smoke row. That future row must claim
Fluid execution paths, generate scenario configs from this package, and run on
appropriate compute resources.

## Do Not Do

- Do not run Fluid under AGENT-543.
- Do not update registry/admission state from this dry package.
- Do not combine UMX1 with TSWFC2 until independent UMX1 smoke evidence exists
  or UMX1 fails cleanly.
