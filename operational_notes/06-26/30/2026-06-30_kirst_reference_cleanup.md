# 2026-06-30 Kirst Reference Cleanup

## Scope

This pass implements the June 30 run-classification policy where it is safe to
edit without colliding with active agents:

- Continuation/Jin artifacts are the current mainline path when present.
- Kirst rows are not current mainline evidence.
- Perturbation/sensitivity rows stay useful, but separate from the mainline.

## Direct Cleanup Applied

The following operational notes were updated in place because they carried
policy-like instructions that could steer future work incorrectly:

- `operational_notes/06-26/01/2026-06-01_modern_runs_first_batch_extraction_summary.md`
- `operational_notes/06-26/01/2026-06-01_publish_handoff_gate.md`
- `operational_notes/06-26/01/2026-06-01_todo.md`
- `operational_notes/06-26/02/2026-06-02_todo.md`

Each now has explicit June 30 supersession language. The edits preserve the
historical extraction and publish-gate observations, but remove the older
Kirst-as-mainline or Kirst-as-publish-ready framing.

## Remaining Kirst References

These are not cleaned in this pass because they are historical logs, generated
report packages, or active/report roots owned by other board rows:

- `journals/2026-06/2026-06-02_ethan_runs.md`: contains the strongest old
  Kirst publish-ready language. Leave historical, but do not use it as current
  policy.
- `reports/2026-06/2026-06-23/2026-06-23_presentation/**`: still uses Salt 1
  Kirst and Salt 2 Kirst as representative presentation/reference rows. This
  should be refreshed before any new external-facing deck is used.
- `reports/2026-06/2026-06-23/2026-06-23_ethan_1d_closure_bakeoff/**`: still
  contains Kirst rows in readable validation/bakeoff surfaces. Treat as stale
  support evidence until the latest-window continuation refresh lands.
- `reports/2026-06/2026-06-18/2026-06-18_ethan_salt_model_dependency_package/**`
  and related June 18 closure packages: many Kirst rows remain in model
  dependency handoff tables. Treat as historical closure-development evidence,
  not current paper mainline input.
- `reports/2026-06/2026-06-15/*field_transport_campaign*/README.md`: lists
  Kirst case roots as part of all-runs field transport campaigns. Keep as
  historical all-runs provenance unless a report refresh is opened.
- `.agent/journal/**` and `journals/**`: preserve as raw/history records, not
  targets for wording cleanup.

## Cleanup Boundary

No report packages were edited in this pass because broad `reports/**` cleanup
is already claimed by `AGENT-127`, and several current analysis/report roots are
owned by active June 29 tasks. The safest next cleanup is a new package-specific
refresh task for the June 23 presentation and 1D validation/bakeoff packages
after the latest-window continuation chain finishes.

## Current Rule To Apply

When writing new summaries or editing existing report prose, classify rows as:

- `mainline_continuation`: current Jin continuation/latest-window evidence.
- `perturbation_correlation_support`: sensitivity runs that can inform trends.
- `historical_excluded_kirst`: Kirst evidence preserved for provenance only.
