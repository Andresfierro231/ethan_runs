---
provenance:
  generated_by: codex
  task_id: TODO-HOLDOUT-SPLIT-FREEZE-CASE-FAMILY-POLICY-2026-07-22
  date: 2026-07-22
tags:
  - holdout
  - split-policy
  - predictive-model
related:
  - work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy
---

# TODO-HOLDOUT-SPLIT-FREEZE-CASE-FAMILY-POLICY-2026-07-22

## Objective

Freeze the legal split/scoring sequence for the fastest holdout route before any
model lane can score protected rows.

## Outcome

Completed. The split law is now package-frozen as a governance artifact:
Salt2 +/-5Q is first primary holdout after candidate freeze, `val_salt2` is
external score-only after freeze, Salt4 +/-5Q is secondary sensitivity, PM10 is
future score-only with total-Q caveat, and Salt1 +/-10Q remains excluded support.
No model was admitted, frozen, scored, or selected.

## Changes Made

- `tools/analyze/build_holdout_split_freeze_case_family_policy.py`
- `tools/analyze/test_holdout_split_freeze_case_family_policy.py`
- `work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/README.md`
- `work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/summary.json`
- `work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/frozen_case_family_policy.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/split_freeze_case_family_policy.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/score_release_law.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/score_law_after_freeze.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/holdout_score_order.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/model_lane_consumption_contract.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/model_lane_next_actions.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/blocker_unblock_ledger.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/publication_claim_boundaries.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/no_leakage_claim_boundaries.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/executable_unlock_sequence.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/thesis_figure_table_ledger.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/source_manifest.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/no_mutation_guardrails.csv`
- `.agent/status/2026-07-22_TODO-HOLDOUT-SPLIT-FREEZE-CASE-FAMILY-POLICY-2026-07-22.md`
- `.agent/journal/2026-07-22/holdout-split-freeze-case-family-policy.md`
- `imports/2026-07-22_holdout_split_freeze_case_family_policy.json`
- `work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/build_package.py`
- `work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/validate_package.py`

## Validation

- `python3.11 -m unittest tools.analyze.test_holdout_split_freeze_case_family_policy`
- `python3.11 tools/analyze/build_holdout_split_freeze_case_family_policy.py`
- `python3.11 work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy/validate_package.py`
- `python3.11 tools/agent/manifest_check.py imports/2026-07-22_holdout_split_freeze_case_family_policy.json --check-paths`
- `python3.11 tools/agent/finish_task.py --task-id TODO-HOLDOUT-SPLIT-FREEZE-CASE-FAMILY-POLICY-2026-07-22`
- `git -C /scratch/09748/andresfierro231/projects_scratch/ethan_runs diff --check -- .agent/BOARD.md .agent/status/2026-07-22_TODO-HOLDOUT-SPLIT-FREEZE-CASE-FAMILY-POLICY-2026-07-22.md .agent/journal/2026-07-22/holdout-split-freeze-case-family-policy.md imports/2026-07-22_holdout_split_freeze_case_family_policy.json tools/analyze/build_holdout_split_freeze_case_family_policy.py tools/analyze/test_holdout_split_freeze_case_family_policy.py work_products/2026-07/2026-07-22/2026-07-22_holdout_split_freeze_case_family_policy`

## Guardrails

No native solver output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler/harvest/UQ launch, Fluid/external edit, thesis
current/LaTeX edit, protected/final scoring, fitting/tuning/model selection,
source/property/Qwall/numeric release, coefficient admission, candidate freeze,
split-role relaxation, or runtime-leakage relaxation occurred.
