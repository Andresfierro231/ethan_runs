---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/launch_readiness_gate.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/target_feature_taps.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/summary.json
tags: [pressure-ledger, two-tap, raw-endpoints, blockers, component-k, f6]
related:
  - .agent/status/2026-07-18_TODO-TWO-TAP-BLOCKER-ROADMAP.md
  - .agent/journal/2026-07-18/two-tap-blocker-roadmap.md
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/README.md
task: TODO-TWO-TAP-BLOCKER-ROADMAP
date: 2026-07-18
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# Two-Tap Blocker Roadmap

Generated: `2026-07-18T18:58:31+00:00`

## Decision

This package turns the completed `corner_lower_right` raw endpoint contract into
a blocker matrix, research-path matrix, ordered next-step queue, and admission
decision rules. It is roadmap-only: no sampling job, solver launch, F6 fit, or
component-K admission was performed.

## Outputs

- `blocker_matrix.csv`
- `research_path_matrix.csv`
- `next_step_queue.csv`
- `admission_decision_rules.csv`
- `roadmap_summary.csv`
- `source_manifest.csv`
- `summary.json`

## Counts

- Blocker rows: `7`.
- Blocking rows: `4`.
- Research paths: `6`.
- Next steps: `7`.
- Admission rules: `7`.
- Ordinary admissions: `0`.

## Next Executable Move

Claim a separate staged-copy cfd-pp row before any OpenFOAM sampling. The first
technical task is to sample Salt2/Salt3/Salt4 `corner_lower_right` endpoint
surfaces from `lower_leg__s04` to `right_leg__s00` at `7915/7618/10000`, writing
only into task-owned `tmp/` or `work_products/`.

## Guardrails

Do not overwrite AGENT-530. Do not infer endpoint pressure fields. Do not clip
negative `K_local`. Do not borrow unrelated GCI. Do not fit F6 or admit
component K unless a future raw-output extractor/admission package resolves all
predeclared gates.
