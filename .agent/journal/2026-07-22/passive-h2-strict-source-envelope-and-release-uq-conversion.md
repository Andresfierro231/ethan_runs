# Journal: PASSIVE-H2 strict source-envelope + release-UQ conversion

Date: `2026-07-22`
Role: Implementer / Tester / Writer / Reviewer
Task ID: `TODO-PASSIVE-H2-STRICT-SOURCE-ENVELOPE-AND-RELEASE-UQ-CONVERSION-2026-07-22`

## Context
Codex ran out of credits; all "active" board rows were codex-`COMPLETE` and left
in the live tables. User asked to (1) do board hygiene, (2) plan the pressure-
corner attack, (3) note F6, (4) leave PASSIVE-H2-Salt1 reconciliation, then
convert diagnostic PASSIVE-H2 evidence into a strict source-envelope and
release-grade same-QOI UQ.

## Files inspected (read-only)
- `.agent/STATE.md` (1 active task, 6 open blockers — authoritative)
- `.agent/BOARD.md`, `.agent/FILE_OWNERSHIP.md`
- R4 gate: `.../2026-07-22_passive_h2_r4_predeclared_source_envelope_uq_gate/{r4_source_family_gate_matrix,r4_freeze_gate,README}.csv|md`
- Post-junction gate: `.../2026-07-22_passive_h2_post_junction_source_property_gate/{post_junction_release_gate,post_junction_runtime_evidence,source_manifest,post_junction_next_action_queue}.csv`
- Mesh-area repair: `.../2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight/{mesh_area_backed_operator_candidate,release_preflight_gate,summary.json}`
- Salt1 orig evidence: `.../2026-07-22_salt1_branch_source_envelope_recovery/salt1_branch_source_evidence_matrix.csv`
- Operator contract: `.../2026-07-22_thermal_passive_h2_one_train_repair_preflight/passive_operator_term_contract.csv`
- Setup coverage: `.../2026-07-22_passive_h2_subspan_mapping_release_recovery/all_case_setup_coverage.csv`
- Roster: `.../2026-07-22_passive_h2_salt14_diagnostic_freeze_and_blind_predictions/diagnostic_train_roster.csv`
- `tools/analyze/compute_gci.py` (GCI engine interface)

## Files changed
- `.agent/BOARD.md` — archived 17 complete rows (via `board_archive.py`),
  removed 5 stale duplicates, added my in-progress row (now to be marked COMPLETE).
- `.agent/BOARD_ARCHIVE.md` — received archived rows (via tool).
- NEW `tools/analyze/build_passive_h2_strict_source_envelope_and_release_uq_conversion.py`
- NEW `tools/analyze/test_passive_h2_strict_source_envelope_and_release_uq_conversion.py`
- NEW `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_strict_source_envelope_and_release_uq_conversion/**`
- NEW status, this journal, import manifest, operational_notes handoff.

## Commands run (reproducible)
```
python3.11 tools/agent/board_archive.py --archive-task <task-id> --apply   # x17
python3.11 tools/agent/board_archive.py --check
python3.11 tools/analyze/build_passive_h2_strict_source_envelope_and_release_uq_conversion.py
python3.11 -m pytest tools/analyze/test_passive_h2_strict_source_envelope_and_release_uq_conversion.py -q
```

## Results / observations
- The R4 gate's earlier `strict_source_envelope = 0` PRE-DATES the 17:04 Salt1
  mesh-area provenance repair (R4 built 16:40). Integrating the repair (mesh-
  verified area, `0/T` + polyMesh only, `2.2e-4` rel) with Salt2's setup-native,
  leakage-flag-clean operator yields the first strict rows.
- Strict pass = 8 (Salt1+Salt2 train x 4 retained families). Salt3/Salt4 fail c3
  honestly (per-row props not independently verified; protected/score-only).
- Same-QOI UQ fail-closed: `source_gate` now passes for train, but `mesh_gci_gate`
  and `time_window_gate` fail. Sole freeze blocker = same-QOI 3-mesh GCI triplet
  (medium/fine CFD at Salt2 physical window; S13 found 0 exact native targets).
- No release/freeze/score flipped; 15 guardrails all False; 8 tests pass.

## Incomplete lines of investigation
- Salt3/Salt4 per-row operator props were not extracted (train-only contract);
  a future pass could verify them, but they are protected so it is not on the
  freeze path.
- Junction (5th family) setup-only wall-layer metadata not recovered; R4 stays
  four-family with a bounded, documented omission.
- The GCI triplet itself is a compute task (needs Ethan/NCC medium/fine mesh or a
  scheduled reconstruction); not attempted here (no solver launch permitted).

## Next steps
See status Follow-up: (1) build the Salt2 same-QOI GCI triplet, (2) S11/S15
review of the 8 strict train rows, (3) optional junction/props recovery,
(4) execute the staged pressure-corner + F6 blocker plans.
