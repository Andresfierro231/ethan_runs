---
provenance:
  generated_by: codex
  task_id: TODO-HOLDOUT-SPLIT-FREEZE-CASE-FAMILY-POLICY-2026-07-22
  date: 2026-07-22
tags:
  - holdout
  - split-policy
  - no-leakage
related:
  - work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/frozen_case_family_policy.csv
---

# Holdout Split-Freeze Case-Family Policy

Task: `TODO-HOLDOUT-SPLIT-FREEZE-CASE-FAMILY-POLICY-2026-07-22`

## Attempted

I converted the readiness audit and final scorecard shell into a durable
split-freeze law. The goal was to remove ambiguity before any H2/D4 candidate
work can generate protected predictions or scores.

## Observed

The target-side evidence is ahead of model readiness. Salt2 +/-5Q and
`val_salt2` are target/ledger-ready, while every current model lane remains
unfrozen. PASSIVE-H2 has active follow-on rows, but current finish evidence
still reports no freeze. S13 endpoint basis improved, but same-window
equivalence still blocks exchange-cell admission.

## Inferred

The fastest legal route is not to search for more holdout rows. It is to hold
the split fixed, finish one model candidate from train-only evidence, emit
frozen predictions, then score exactly once.

## Caveats

This is a policy/freeze-of-split package, not a candidate freeze. It makes
future scoring stricter; it does not release any source/property, Qwall,
coefficient, prediction, or score artifact.

## Next Useful Actions

1. Let the active PASSIVE-H2 R4 source-envelope/UQ row decide freeze eligibility
   or fail closed.
2. Keep Salt1 junction recovery separate from this scoring law.
3. Claim D4 physical successor preflight if H2 cannot release.
4. Only after one candidate is admitted, claim train-only same-QOI UQ and
   immutable freeze.
