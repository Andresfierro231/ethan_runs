---
provenance:
  - operational_notes/07-26/17/2026-07-17_COOLER_MODEL_COMPREHENSIVE_TEST_PLAN.md
  - work_products/2026-07/2026-07-15/2026-07-15_setup_only_hx_cooler_scorecard_unlock/setup_only_hx_boundary_scorecard.csv
  - work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/m3ts_coupled_scorecard.csv
tags: [journal, cooler, hx, setup-only, test-plan]
related:
  - .agent/status/2026-07-17_AGENT-480.md
  - TODO-PREDICT-COOLER-REMOVAL
task: AGENT-480
date: 2026-07-17
role: Coordinator/Writer/Tester
type: journal
status: complete
---
# Cooler Model Comprehensive Test Plan Journal

## Files Inspected

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `.agent/BLOCKERS.md`
- `.agent/DOC_FRONTMATTER_SCHEMA.md`
- `operational_notes/07-26/16/2026-07-16_FLUID_WALLS_TOMORROW_HANDOFF.md`
- `operational_notes/maps/forward-predictive-model.md`
- `operational_notes/maps/thermal-boundary-and-radiation.md`
- `work_products/2026-07/2026-07-15/2026-07-15_setup_only_hx_cooler_scorecard_unlock/README.md`
- `work_products/2026-07/2026-07-15/2026-07-15_setup_only_hx_cooler_scorecard_unlock/setup_only_hx_boundary_scorecard.csv`
- `work_products/2026-07/2026-07-15/2026-07-15_setup_only_hx_cooler_scorecard_unlock/hx_candidate_gate_decision.csv`
- `work_products/2026-07/2026-07-16/2026-07-16_predictive_boundary_submodel_admission/README.md`
- `work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/README.md`
- `work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/m3ts_coupled_scorecard.csv`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`

## Files Changed

- `.agent/BOARD.md`
- `.agent/status/2026-07-17_AGENT-480.md`
- `.agent/journal/2026-07-17/cooler-model-comprehensive-test-plan.md`
- `imports/2026-07-17_cooler_model_comprehensive_test_plan.json`
- `operational_notes/07-26/17/2026-07-17_COOLER_MODEL_COMPREHENSIVE_TEST_PLAN.md`
- `operational_notes/maps/forward-predictive-model.md`
- generated docs index files after `tools/docs/build_repo_index.py`

## Observations

- The current preferred setup-legal cooler lane is
  `salt2_fit_constant_UA_bulk_drive`.
- Its held-out duty errors are already low: Salt3 `2.869104004 W`, Salt4
  `7.502618613 W`.
- Fluid already has an epsilon/NTU active-HX implementation and
  `hx_ua_multiplier`, so the first model is an implementation/scorecard
  hardening path, not new physics.
- The useful next comparison is whether segmented distributed-UA improves
  spatial heat placement and coupled TP/TW scores after total duty is already
  reasonable.

## Commands Run

- `pwd`
- `cat AGENTS.md`
- `cat .agent/BOARD.md`
- `cat .agent/FILE_OWNERSHIP.md`
- `cat .agent/ROLES.md`
- `find operational_notes -name AGENTS.override.md -o -name README.md -o -name TODO.md`
- `find .agent -maxdepth 2 -name AGENTS.override.md -o -name README.md -o -name TODO.md`
- `rg -n ...` over blocker, map, HX, and Fluid files
- `sed -n ...` for source/scorecard excerpts
- `mkdir -p .agent/journal/2026-07-17 operational_notes/07-26/17`
- `python3 tools/docs/build_repo_index.py`
- `python3 tools/docs/build_repo_index.py --check`

## Incomplete Lines

- No implementation was performed.
- No coupled Fluid rerun was performed.
- The plan assumes the next implementer will choose whether segmented-UA can be
  implemented repo-locally first or needs an external Fluid patch.

## Next Steps

Claim `TODO-PREDICT-COOLER-REMOVAL`, then implement the package described in
`operational_notes/07-26/17/2026-07-17_COOLER_MODEL_COMPREHENSIVE_TEST_PLAN.md`.
