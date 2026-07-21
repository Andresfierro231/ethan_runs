# CFD Postprocessing Documentation Workflow Hardening

Date: 2026-07-07
Agent: AGENT-197
Role: Coordinator / Writer / Implementer

## Objective

Make the CFD postprocessing scripts and coordination docs easier for independent
workers to use without hidden context. The main deliverable is a modular,
end-to-end workflow note plus additive script docstrings that document workflow
position, inputs, outputs, command-line modifiers, and boundaries.

## Boundaries

- No native solver outputs are edited.
- No active corrected-Salt gate scripts are edited; those remain owned by
  `AGENT-181`.
- Existing dirty worktree content is treated as prior user/agent work and is
  not reverted.
- This pass is documentation hardening only; scientific implementation gaps
  remain on the board as separate rows.

## Observed Need

The script inventory is broad enough to support useful CFD postprocessing today,
but the documentation quality is uneven. Newer scripts already document their
contract well; older heat audit builders, older hydraulic extractors, and the
1D closure-bundle scripts need clearer module-level guidance so a worker can
tell whether a script extracts raw evidence, summarizes already-reduced
products, packages a closure contract, or performs a model-form comparison.

## Actions

- Claimed `AGENT-197` on `.agent/BOARD.md`.
- Added module-level workflow docstrings to older heat-audit, hydraulic
  extraction, minor-loss, 1D closure, and upcomer evidence scripts.
- Added
  `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_workflow_docs.md`
  with an end-to-end run admission -> thermal ledger -> pressure ledger ->
  minor loss -> upcomer/downcomer -> observation table -> model-form bakeoff ->
  mesh uncertainty workflow.
- Documented that short corrected-Salt restarts such as
  `salt1_jin_hi10q_corrected` ending about 254 s past restart must be flagged
  by run-state inventory and downstream postprocessing rather than silently
  treated as steady evidence.

## Validation

`python3.11 -m py_compile` passed for all nine edited scripts.

CLI help smoke passed for:

- `tools/analyze/build_next_1d_model_forms.py`
- `tools/analyze/cfd_closure_bundle.py`
- `tools/analyze/build_ethan_upcomer_recirculation_evidence.py`
- `tools/analyze/build_ethan_1d_closure_bakeoff.py`

The targeted pytest command could not run because this shell does not have
`pytest` installed. Some additional CLI help smoke checks were also blocked by
missing `matplotlib` or `numpy`. No solver outputs or generated scientific data
were modified.

## Handoff

Use
`operational_notes/07-26/07/2026-07-07_cfd_postprocessing_workflow_docs.md`
as the worker-facing workflow map. The board still carries the scientific
implementation work as separate rows: pressure term ledger, observation table
contract, patchwise heat ledger, targeted literature forms, minor-loss two-tap,
model-form bakeoff, upcomer onset, and mesh uncertainty.
