---
provenance:
  - .agent/BLOCKERS.md
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_extraction_plan/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/upcomer_onset_candidate_cases.csv
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_internal_nu_residual_guardrails/README.md
tags: [internal-nu, blockers, admission, coordinator]
related:
  - operational_notes/maps/thermal-closures-and-internal-nu.md
task: AGENT-345
date: 2026-07-14
role: Coordinator/Implementer/Tester/Writer
type: work_product
status: complete
---
# Internal-Nu Blocker Progress Integration

## Current Decision

Internal-Nu fitting remains closed. Current fit-admissible internal-Nu rows remain `0`.

The progress since the zero-fit decision is not a fit reopening. It is a conversion
of vague blockers into executable gates: matched-plane extraction, corrected-Q
terminal harvest, closure-QOI mesh/GCI failed-gate accounting, boundary residual
ownership, Fluid external boundary API work, and hydraulic Re-variation gating.

## What Can Move Now

1. Run or finish compute-node matched upcomer inlet/mid/outlet extraction under the
   active therm-reconstr workflow. Existing postprocessing proxies stay diagnostic.
2. Harvest corrected-Q terminal rows and run admission before using them as onset
   or Nu evidence.
3. Build the closure-QOI mesh/GCI failed-gate matrix; repaired and smoke thermal
   outputs are diagnostic until admitted.
4. Build the boundary-model task matrix so heater, cooler, wall/layer, storage,
   radiation, and branch-mixing residuals are not assigned to Nu.

## Major Blockers

- `closure-qoi-mesh-gci`: mesh families exist, but publication-ready thermal GCI
  and fit-admissible thermal rows do not.
- `thermal-cfd-1d-parity`: parity and wall-adjacent-T residual ownership remain
  unresolved.
- `predictive-heater-cooler-wall-submodels`: setup-side boundary submodels are
  still needed before predictive thermal claims.
- `upcomer-onset-data-sparsity`: all current mainline Salt upcomer points are
  recirculating; onset is not bracketed by admitted non-recirculating evidence.
- `fluid-external-boundary-api-gap`: Fluid needs first-class external boundary
  dictionaries before faithful passive-loss prediction.
- `f6-friction-re-correction`: hydraulic F6 waits for admitted Re-variation rows.

## Assumptions

This package assumes the authoritative blocker ledger is current as of
2026-07-14T14:00:14. It deliberately does not reopen stale blockers:
OF13 reconstruction works, mesh families exist, and CFD `rcExternalTemperature`
wallHeatFlux includes radiation. No separate exported `qr` term exists in the
current evidence stack.

It also assumes that current CFD diagnostics are evidence for admission decisions,
not forward-model runtime inputs. Forward models may use baseline/literature/default
internal Nu behavior today, but not fitted internal Nu from current rows.

## Methods

The builder reads the current blocker ledger and the July 14 internal-Nu,
matched-plane, onset-candidate, residual-guardrail, forward-gate, hydraulic, and
submitted-run packages. It writes:

- `assumptions_methods_process.csv`
- `blocker_progress_matrix.csv`
- `admission_decision_table.csv`
- `next_workstream_actions.csv`
- `source_manifest.csv`
- `summary.json`

No native CFD solver outputs, registry/admission state, scheduler state,
generated repo indexes, or external `../cfd-modeling-tools` files were mutated.
Generated index refresh is intentionally left untouched because active `AGENT-344`
currently owns that scope.

## Process

1. Claimed board row `AGENT-345` before edits.
2. Read current blocker and internal-Nu source packages.
3. Encoded assumptions, blockers, admission decisions, and next actions in a
   reproducible builder.
4. Added focused tests that enforce zero-fit status, diagnostic naming, open
   blocker coverage, radiation semantics, and executable next actions.
5. Wrote dated status, journal, import, and work-product closeout artifacts.

## Reopen Evidence

Internal-Nu fitting can reopen only if a later dated gate admits at least three
single-stream upcomer rows, including an ordinary-pipe non-recirculating anchor
and a near-transition or higher-Re row, with matched reverse-flow, secondary-flow,
wall/bulk, heat-flux, nondimensional, mesh/time, residual-ownership, and
sign/radiation checks passing.
