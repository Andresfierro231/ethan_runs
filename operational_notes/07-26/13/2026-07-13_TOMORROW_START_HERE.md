---
provenance:
  - .agent/BOARD.md
  - operational_notes/07-26/13/2026-07-13_TOMORROW_CORRECTED_SALT_Q_LIVE_JOB_HANDOFF.md
  - work_products/2026-07/2026-07-13/2026-07-13_tomorrow_start_here/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/comparison_summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_correction_candidates/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hx_fit/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/README.md
tags: [tomorrow-handoff, doc-continuity, scheduler-handoff, forward-model, predictive-1d, thesis-source]
related:
  - work_products/2026-07/2026-07-13/2026-07-13_tomorrow_start_here/README.md
  - operational_notes/07-26/13/2026-07-13_TOMORROW_CORRECTED_SALT_Q_LIVE_JOB_HANDOFF.md
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/master_thesis_bullet_outline.md
task: AGENT-307
date: 2026-07-13
role: Coordinator/Writer
type: operational_note
status: complete
supersedes: []
superseded_by:
---
# Tomorrow Start Here

Purpose: give the July 14 agent a single, current entry point without needing
chat history.

## Open First

1. `AGENTS.md`
2. `.agent/BOARD.md`
3. `.agent/STATE.md` and `.agent/BLOCKERS.md`
4. This note.
5. `operational_notes/07-26/13/2026-07-13_TOMORROW_CORRECTED_SALT_Q_LIVE_JOB_HANDOFF.md`
6. `work_products/2026-07/2026-07-13/2026-07-13_tomorrow_start_here/README.md`
7. `reports/thesis_dossier/README.md`
8. `reports/thesis_dossier/master_thesis_bullet_outline.md`

If `.agent/STATE.md` disagrees with `.agent/BOARD.md` or a later package
summary, trust the newer board/status/package evidence. The generated state was
last seen with older active-task counts.

## Current Project State

Observed:

- Corrected Salt-Q job `3293924` (`saltq_sel_cont`) is still running. Latest
  checked state was `RUNNING`, elapsed `00:41:35`, node `c318-016`.
- AGENT-305 submitted Salt2 coarse thermal repair-smoke job `3294001`
  (`s2_coarse_T+`). Later `sacct` check shows `COMPLETED`, exit `0:0`,
  elapsed `00:02:41`, node `c318-011`. Its purpose was to close the missing
  coarse thermal triplet input; it is not a closure admission.
- Existing interactive allocation `3292998` is also running.
- No duplicate corrected-Q job was launched. There is no good reason to
  duplicate corrected-Q while `3293924` is live.
- AGENT-308 is now active for a bounded H1 proxy screen. Treat that as
  screen-only hydraulic evidence unless its own status/package says otherwise.
- Forward-v0 full Fluid `solve_case` confirmation job `3293960` is complete:
  `COMPLETED`, exit `0:0`, elapsed `00:07:19`.
- The solve-case comparison package reports `6/6` pass rows. Treat
  `solve_case` rows as authoritative; `fast_scan` is only a proxy inside the
  documented deltas.
- Predictive HX fit exists as its own campaign. `F1_heater_only` improves proxy
  thermal errors, but mdot remains high.
- Hydraulic correction candidates exist. The next hydraulic candidate is
  `H1_localized_named_loss_and_reset_bundle`; it still needs a bounded forward
  rerun before final scoring.
- Thermal mesh gate has `0` fit-admissible rows and `0` publication-ready
  thermal GCI rows. Repaired reconstructed `T` smoke is not a closure
  admission.
- Sensor map contract has `17` labels mapped, `15` diagnostic-scoreable, and
  `TP2`/`TW10` blocked.

Inferred priority:

1. Monitor or harvest corrected Salt-Q.
2. Apply/test hydraulic H1 before any final forward-v1 score.
3. Keep HX results as guardrailed proxy evidence until mdot guardrail improves.
4. Keep thermal UA/HTC/Nu diagnostic until sign, coarse-triplet, heat-balance,
   and downcomer policy gates pass.
5. Use the thesis dossier for human synthesis and the work-product packages for
   provenance.

## Tomorrow Commands

Corrected Salt-Q first:

```bash
sacct -j 3293924 --format=JobID,JobName,State,ExitCode,Elapsed,Submit,Start,End,NodeList -P
squeue -j 3293924
tail -80 jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/slurm-saltq_sel_cont-3293924.out
tail -80 jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/slurm-saltq_sel_cont-3293924.err
```

Salt2 coarse thermal repair-smoke terminal check:

```bash
sacct -j 3294001 --format=JobID,JobName,State,ExitCode,Elapsed,NodeList%30 -X
```

Forward-v0 confirmation check, only if needed:

```bash
sacct -j 3293960 --format=JobID,JobName,State,ExitCode,Elapsed,NodeList%30 -X
python3.11 -m json.tool work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/comparison_summary.json
```

Documentation check at the end of the next significant session:

```bash
python3 tools/docs/build_repo_index.py --check
```

Regenerate the index only from a task whose board scope includes
`.agent/STATE.md`, `.agent/catalog.json`, `.agent/catalog.csv`, and
`.agent/BLOCKERS.md`.

## Next Task Sequence

1. Claim or continue a corrected-Q terminal harvest row if `3293924` exits.
   Do not admit corrected-Q rows from Slurm completion alone.
2. Claim a hydraulic H1 apply/test row. Use AGENT-300's H1 candidate and score
   mdot movement without thermal fitting.
3. Only after the hydraulic rerun, reopen the end-to-end scorecard row and
   clearly separate train, validation, and holdout rows.
4. Rebuild or extend the thermal mesh gate only in a separate row after reading
   AGENT-305. Its output should classify thermal rows; it should not fit
   UA/HTC/Nu unless sign, coarse-triplet, heat-balance, and downcomer gates
   pass.
5. If direct Fluid implementation is needed, create a separate external Fluid
   edit row for the API/dictionary work. This handoff keeps
   `../cfd-modeling-tools/**` read-only.

## Do Not Do

- Do not mutate native CFD solver outputs.
- Do not launch a duplicate corrected-Q job while `3293924` is live.
- Do not use CFD `mdot`, realized CFD `wallHeatFlux`, or validation
  temperatures as runtime predictive inputs.
- Do not call the current scorecard precursor a final forward-v1 score.
- Do not fit thermal terms while the hydraulic mdot guardrail fails.
- Do not hide component/reset/redevelopment losses inside one global friction
  multiplier.
- Do not double-count radiation. Current CFD `rcExternalTemperature`
  wallHeatFlux includes emissivity/Tsur effects.
- Do not use repaired thermal UA/HTC/Nu rows as fit targets until the thermal
  gate admits them.

## Continuity Rule

For a new research avenue tomorrow, use the continuity protocol already added
to `AGENTS.md` and `CLAUDE.md`: board row first, dated start-here/handoff note,
author/title provenance for literature ideas, exact file paths for repo
evidence, and a status/journal/import closeout.
