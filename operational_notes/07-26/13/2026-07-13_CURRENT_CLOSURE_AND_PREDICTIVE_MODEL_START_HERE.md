# Current Closure and Predictive Model Start Here

Date: 2026-07-13  
Task anchor: `AGENT-292`  
Purpose: compact continuity note for picking up the lit-rev-to-predictive-model
chain without reading chat history.

## Open These Files First

1. `.agent/BOARD.md` for live ownership, especially `AGENT-291`, `AGENT-290`,
   `TODO-PRED-WALL-LAYER`, and the predictive rows.
2. `work_products/2026-07/2026-07-13/2026-07-13_litrev_todo_campaign_index/README.md`
   for the five completed lit-rev gate packages and their reading order.
3. `operational_notes/07-26/13/2026-07-13_litrev_synthesis_start_here.md`
   and `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/README.md`
   for lessons, model forms, and literature-derived research pathways.
4. `work_products/2026-07/2026-07-13/2026-07-13_forward_predictive_model_research_plan/research_plan.md`
   and `operational_notes/07-26/13/2026-07-13_forward_predictive_model_research_plan.md`
   for the predictive modeling sequence.
5. `operational_notes/07-26/13/2026-07-13_external_report_research_index_and_blocker_audit.md`
   for the connected research index and stale-versus-real blocker audit.
6. `work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/README.md`
   and `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/README.md`
   for the current predictive input contract and first imposed-cooler forward
   run.

## Trust These Packages

- Lit-rev source envelope:
  `work_products/2026-07/2026-07-13/2026-07-13_litrev_source_envelope/`
- Lit-rev property sensitivity:
  `work_products/2026-07/2026-07-13/2026-07-13_litrev_property_sensitivity/`
- Lit-rev reset/named losses:
  `work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/`
- Lit-rev heat-loss calibration:
  `work_products/2026-07/2026-07-13/2026-07-13_litrev_heat_loss_calibration/`
- Lit-rev CFD validity diagnostics:
  `work_products/2026-07/2026-07-13/2026-07-13_litrev_cfd_validity_diagnostics/`
- Forward predictive research plan:
  `work_products/2026-07/2026-07-13/2026-07-13_forward_predictive_model_research_plan/`
- External research index and blocker audit:
  `operational_notes/07-26/13/2026-07-13_external_report_research_index_and_blocker_audit.md`

These are durable coordination artifacts. Native solver outputs remain
read-only evidence and should not be edited.

## Current Blockers

- Exact reverse-flow area fraction, reverse mass fraction, and secondary
  velocity fraction are still bounded diagnostics unless a later extraction row
  stages those plane-wise quantities.
- Property lane choice is not yet propagated through a full 1D rerun; do not
  fit friction or heat residuals until the selected property mode is explicit.
- Named pressure losses are separated conceptually, but no global friction
  multiplier should be introduced to hide fittings, redevelopment, cluster
  loss, or branch-apparent loss.
- Heat-loss admission is separated, but radiation is embedded in CFD
  `rcExternalTemperature` wall heat flux and no separate `qr` term is available
  in current exported ledgers.
- Wall/storage and heater/test-section transfer terms remain unresolved
  predictive blockers.
- Salt2 fine reconstructed-T repair is active under `AGENT-291`; corrected
  Salt-Q time-precision rerun is active under `AGENT-290`.

## Next Task Sequence

1. Keep `TODO-PRED-INPUT-CONTRACT` current with the five lit-rev gate outputs:
   source envelope, property mode lane, named-loss table, heat-loss admission,
   and CFD coefficient naming limits.
2. Before any `TODO-PRED-FORWARD-V0` scoring, require explicit references to
   those five gates and fail strict scoring if the references are missing.
3. Treat `TODO-PRED-WALL-LAYER` as a completed input package for E0 drive
   mapping and as the blocker record for E1/E2 near-wall shell extraction.
4. Then continue the predictive chain in this order unless the board changes:
   `TODO-PRED-HX-FIT`, `TODO-PRED-HEATER-TEST-CONTRACT`,
   `TODO-PRED-HYDRAULIC-GATE`, `TODO-PRED-THERMAL-MESH-GATE`,
   `TODO-PRED-SENSOR-MAP`, `TODO-PRED-VALIDATION-SPLIT`, and
   `TODO-PRED-ENDTOEND-SCORE`.

## New Avenue Protocol

For any clearly new research avenue, both Claude and Codex must use the same
shape:

1. Add or claim a board row with role, owner, edit paths, read-only context,
   objective, acceptance signal, and status.
2. Create a dated start-here or package README with: why this exists, open-first
   files, trusted evidence, blockers, next sequence, output contract, and
   do-not-do guardrails.
3. Cross-link the new note from the nearest current start-here file or package
   README.
4. Preserve provenance by author/title for literature ideas and exact file path
   for repo evidence.
5. Close with a status file, journal entry, and import manifest when an artifact
   is created or updated.
