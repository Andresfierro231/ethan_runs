---
provenance:
  - .agent/BOARD.md
  - .agent/BLOCKERS.md
  - operational_notes/07-26/13/2026-07-13_TOMORROW_START_HERE.md
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/Outline.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_parallel_execution_coordination/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/comparison_summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_h1_proxy_rerun/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_salt2_coarse_thermal_repair_smoke/README.md
tags: [thesis-dossier, weekly-presentation, thesis-source, forward-model, hydraulic-guardrail, mesh-gci, cfd-postprocess, blocker-audit]
related:
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/Outline.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/mesh-gci-and-uncertainty.md
  - operational_notes/maps/pressure-and-momentum-budget.md
  - .agent/journal/2026-07-14/thesis-presentation-live-results-update.md
task: AGENT-311
date: 2026-07-14
role: Writer
type: report
status: complete
supersedes: []
superseded_by:
---
# Thesis / Presentation Update - 2026-07-14

Purpose: concise human-facing update after the landed July 13 predictive and
overnight postprocess wave. This note only uses landed evidence available to
AGENT-311. Active July 14 lanes `AGENT-309` and `AGENT-310` were still running
when this was written, so their results are pending and not promoted here.

## What Changed

- Full Fluid `solve_case` confirmation for forward-v0 passed `6/6` comparison
  rows. The package states solve-case rows are authoritative; `fast_scan` remains
  a screening proxy where deltas stay inside documented bands.
- H1 hydraulic proxy screening landed. The fixed aggregate Salt2 train
  `K_local` proxy moved mean mdot error versus CFD from `0.0029775 kg/s`
  (`F0_current_fluid_sources_H1_proxy`) to `0.0021442 kg/s`
  (`F1_heater_only_H1_proxy`). This is directionally useful but is not a
  faithful localized H1 implementation.
- Salt2 coarse thermal repair-smoke completed cleanly: reconstructed `T`,
  section temperature sampling, and segment thermal extraction passed. The
  package explicitly keeps closure admission behind sign, heat-balance, and
  mesh gates.
- Corrected Salt-Q job `3293924` was still running at the read-only scheduler
  heartbeat on `2026-07-14T11:08-05:00` with elapsed `18:04:29` on `c318-016`.
  No corrected-Q terminal harvest or admission result is available yet.
- Board state is ahead of generated `.agent/STATE.md`: `AGENT-309` is refreshing
  the thermal/closure mesh gate, and `AGENT-310` is building the H1 hydraulic
  scorecard. Do not fold their expected outcomes into the story until their
  packages/status files land.

## Trust Boundary

| Evidence class | Current statement | Presentation wording |
| --- | --- | --- |
| Predictive model execution | `solve_case` forward-v0 confirmation passed and is now the authoritative execution path for those rows. | "The model can run end-to-end for the current forward-v0 setup, but this is not final forward-v1 readiness." |
| CFD-informed replay / proxy | Imposed cooler duty and H1 fixed-K proxy show which submodels matter, but both use diagnostic information or downgraded controls. | "These screens identify the dominant error lanes; they are not thesis-strength predictive closures." |
| Hydraulic evidence | H1 proxy improves mdot directionally but still needs the AGENT-310 scorecard and faithful localized loss/reset support. | "Hydraulic correction is the next gate before thermal fitting." |
| Thermal mesh evidence | Coarse repair-smoke closes a missing input path, not admission. | "Thermal UA/HTC/Nu stays diagnostic until mesh/sign/heat-balance gates admit rows." |
| CFD live runs | Corrected Salt-Q remains live; terminal harvest is pending. | "Salt-Q perturbation evidence is not admitted from runtime status alone." |
| Blockers | Use `.agent/BLOCKERS.md`; do not re-open OF13 reconstruction, no-mesh-for-GCI, or no-radiation blockers. | "The real blockers are quality/admission/API/model-form gates, not missing mesh or absent radiation." |

## What Remains Blocked

- Final forward-v1 score: blocked until H1 hydraulic scoring shows enough mdot
  improvement, sensor exclusions remain explicit, and thermal/API gates are
  resolved.
- Thermal closure fitting: blocked by mesh/sign/heat-balance/downcomer policy
  gates, despite the coarse thermal repair-smoke passing.
- Corrected Salt-Q closure use: blocked until job `3293924` exits and a terminal
  harvest/admission review admits row-specific evidence.
- External boundary/wall-layer predictive implementation: still needs a writable
  Fluid-side implementation lane for first-class dictionaries.
- Upcomer onset and friction correction remain model-form/data-sparsity
  blockers per `.agent/BLOCKERS.md`.

## Next Meeting Story

Show this as a disciplined transition, not as a finished predictive model:

1. The forward model now has a verified full `solve_case` execution path for
   forward-v0 rows.
2. The dominant current failure is hydraulic mdot overprediction; H1 proxy
   evidence improves directionally, and the live AGENT-310 scorecard decides
   whether it is enough to reopen forward-v1 scoring.
3. Thermal results are improving operationally because the Salt2 coarse repair
   smoke completed, but no thermal closure row is admitted from smoke alone.
4. Corrected Salt-Q remains live and should be shown only as an in-progress CFD
   run, not as admitted sensitivity evidence.
5. The thesis claim should stay methodological: branchwise closure ledger,
   provenance-controlled admission, and explicit separation of predictive
   inputs from CFD-informed diagnostics.

## Suggested Slide Adjustments

- Add one slide or callout: "Execution path verified: solve_case forward-v0
  passes 6/6 comparison rows."
- Replace any "hydraulic correction selected" wording with "H1 proxy improved
  mdot directionally; localized scorecard pending."
- Keep the thermal slide in the diagnostic lane: coarse repair smoke passed,
  but mesh/sign/heat-balance admission is pending.
- Keep the blocker slide short: real blockers only; resolved/superseded
  blockers should stay off the slide.
