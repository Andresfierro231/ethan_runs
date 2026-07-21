---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/canonical_final_predictive_split_policy.csv
  - operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md
tags: [journal, AGENT-481, split-policy, salt-cfd]
related:
  - .agent/status/2026-07-17_AGENT-481.md
  - imports/2026-07-17_canonical_final_predictive_split_policy.json
task: AGENT-481
date: 2026-07-17
role: Coordinator/Writer
type: journal
status: complete
---
# Canonical Final Predictive Split Policy

The user corrected the canonical final predictive split. I recorded the new
policy as a dated table and updated the living maps: final training spans Salt1,
Salt2, Salt3, and Salt4 nominal rows; holdout/testing comes from Salt2 +/-5Q,
val_salt2 after external-test admission, selected +/-10Q after terminal harvest,
and future new CFD rows.

The old Salt2-train / Salt3-validation / Salt4-holdout split remains historical
method-development context only. It is no longer the final thesis predictive
split.

I added four board TODOs with explicit instructions for the work needed before
those rows can support final scoring.

