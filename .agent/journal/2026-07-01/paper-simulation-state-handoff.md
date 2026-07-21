# Paper Simulation State Handoff

Date: `2026-07-01`  
Task: `AGENT-172`  
Role: `Coordinator / Writer`

## Purpose

Document the current state well enough that this Codex instance can be closed,
then start a paper-facing internal state package that identifies simulation
evidence ready, nearly ready, or not ready for the manuscript.

## Scope

Edited only AGENT-172-owned coordination files:

- `.agent/BOARD.md` own AGENT-172 row
- `.agent/status/2026-07-01_AGENT-172.md`
- `.agent/journal/2026-07-01/paper-simulation-state-handoff.md`
- `reports/2026-07/2026-07-01/2026-07-01_paper_simulation_state_handoff/**`

Read-only sources included existing reports, journals, operational notes, and
the external paper repository `../papers/3d_analysis`.

## Observed Context

At `2026-07-01T17:53:03-0500`, `squeue -u andresfierro231` showed four
production NuclearEnergy jobs running for about two days and one dev job
running for about eight hours:

- `3265969` `ethan_s34mid_ne5d` on `c318-012`
- `3265970` `ethan_w1234_ne5d` on `c318-013`
- `3265971` `ethan_s41lo2mid_ne5d` on `c318-014`
- `3265972` `ethan_s123hi_ne5d` on `c318-017`
- `3269598` `idv89401` on `c318-008`

No convergence claim was made from queue state alone.

## Main Findings

The current paper-grade CFD subset is the Jin Salt family. Continuation
artifacts should be surfaced first. Kirst runs should remain historical
provenance unless re-admitted by a later dated note. Perturbation runs should
remain sensitivity or correlation-support evidence, not nominal baseline cases.

The current paper repository appears to be built around older June 15-22
evidence packages. The June 29, June 30, and July 1 readiness packages are not
yet integrated into the paper.

The strongest paper-facing updates are:

- June 29 case inventory and run-classification policy.
- June 29 reduction-contract audit.
- June 30 3D-to-1D field-reduction methods.
- Mesh-derived geometry/station provenance from AGENT-162 and July 1 readiness
  work.
- Salt 2/3/4 Jin OF13 thermal closure values, with GCI and property caveats.
- Upcomer recirculation evidence as a mechanism and closure trust boundary.

The July 1 ROM model-form fit package is useful for internal comparison and
meeting figures. It should not be promoted as final predictive ROM evidence.
The best compact fit drove `k90=0`, which is an identifiability warning in an
mdot-only compact fit, not a physical no-bend-loss conclusion.

## Package Written

Created:

- `reports/2026-07/2026-07-01/2026-07-01_paper_simulation_state_handoff/README.md`
- `reports/2026-07/2026-07-01/2026-07-01_paper_simulation_state_handoff/paper_ready_not_yet_in_paper.csv`
- `reports/2026-07/2026-07-01/2026-07-01_paper_simulation_state_handoff/simulation_state_for_paper.csv`
- `reports/2026-07/2026-07-01/2026-07-01_paper_simulation_state_handoff/tomorrow_next_steps.csv`
- `reports/2026-07/2026-07-01/2026-07-01_paper_simulation_state_handoff/source_review_index.csv`

The source review index explicitly marks current anchors as reviewed and older
June journals/reports as inventoried but not fully audited. That boundary is
intentional: older evidence should be re-read claim-by-claim before being
promoted into the paper.

## Next Steps For Tomorrow

1. Check `squeue` and all active agent statuses, especially AGENT-164,
   AGENT-170, and AGENT-171.
2. Assess the four long CFD jobs for residuals, heat balance, mass-flow
   stability, and latest-window quality.
3. Open a separate paper-edit task before modifying `../papers/3d_analysis`.
4. Use `paper_ready_not_yet_in_paper.csv` as the first paper-integration queue.
5. Keep scaling postponed and preserve the note that no scaling jobs were
   submitted in this cycle; one planned scaling job from yesterday should be
   resubmitted when scaling resumes.

## Remaining Risks

- No mesh GCI bound is available yet.
- Variable-density buoyancy decomposition is not implemented.
- Full dense ROM search has not been run.
- Experimental validation remains future work.
- Long CFD jobs need real convergence checks before any new paper claims.
