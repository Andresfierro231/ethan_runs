---
task: AGENT-560
date: 2026-07-20
role: Hydraulics/cfd-pp/Implementer/Writer
status: complete
---
# F6 Two-Tap Nonrecirculating Staging

Task: `AGENT-560`

I claimed AGENT-560 and ran
`python3.11 tools/agent/preflight_task.py --task-id AGENT-560`; ownership
preflight passed with no conflicts.

I reviewed the AGENT-556 runbook, the completed July 20 two-tap
nonrecirculating anchor plan, current corner-lower-right repair/admission
evidence, and high-heat readiness evidence. The existing plan already selected
`CAND-001` as the preferred conditional same-topology source family, but it
also made the correct no-launch decision.

This AGENT-560 package preserves that decision and sharpens the future sampler
handoff. Current Salt2/Salt3/Salt4 `corner_lower_right` rows stay
diagnostic-only because they fail material reverse-flow, component-isolation,
and same-QOI uncertainty gates. No F6 fit or component-`K` admission is allowed
from them.

The future sampler may proceed only in a separate row that claims staged-copy
cfd-pp scope, verifies terminal high-heat/no-recirculation source cases,
resolves endpoint labels `lower_leg__s04` and `right_leg__s00`, computes finite
raw and derived endpoint fields, checks aggregate `RAF < 0.01` and `RMF < 0.01`
on the same retained window, and emits same-QOI UQ or stays diagnostic.
