# Shortest Next Evidence Action

S6 is blocked until one runtime-legal frozen candidate is predeclared and the release gates permit scoring.

1. complete_terminal_monitor_then_claim_exact harvest row if CFD lands successfully
   - Reason: latest CFD and pressure anchor are terminal-gated
   - Source paths: `work_products/2026-07/2026-07-21/2026-07-21_litrev_latest_cfd_schema_promotion/README.md;work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/README.md`
2. resolve row-specific source envelopes before any fit or model-selection release
   - Reason: S5 has zero fit/model-selection release rows
   - Source paths: `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s5_source_property_split_release/release_blocker_table.csv`
3. predeclare one runtime-legal frozen candidate after gates pass
   - Reason: S6 cannot score FINAL_FREEZE_TBD placeholders
   - Source paths: `work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/prediction_join_shell.csv`

No final accuracy, fit, model selection, or admission claim is made by this shell.
