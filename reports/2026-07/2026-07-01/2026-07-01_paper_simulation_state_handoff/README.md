# Paper Simulation State Handoff

Date: `2026-07-01`  
Task: `AGENT-172`  
Role: `Coordinator / Writer`  
Purpose: make the current CFD, post-processing, and ROM state safe to resume
tomorrow and identify simulation evidence that is ready, or nearly ready, to
pass into the paper.

## Close-Safe State

This instance can be closed after this package, the matching journal entry, and
the AGENT-172 status note are written. No Codex-owned interactive command
session is required to keep work alive.

Observed Slurm state at `2026-07-01T17:53:03-0500`:

- `3265969` `ethan_s34mid_ne5d`, running on `c318-012`, age `2-00:34:37`
- `3265970` `ethan_w1234_ne5d`, running on `c318-013`, age `2-00:34:37`
- `3265971` `ethan_s41lo2mid_ne5d`, running on `c318-014`, age `2-00:34:37`
- `3265972` `ethan_s123hi_ne5d`, running on `c318-017`, age `2-00:34:37`
- `3269598` `idv89401`, running on `c318-008`, age `7:49:14`

Do not infer convergence from this queue state alone. Tomorrow's first action
should be to check the active agent status files and the relevant case logs.

## Current Mainline Understanding

The current paper-grade CFD subset is the Jin Salt family, with continuation
artifacts preferred whenever a continuation exists. Kirst runs are historical
provenance unless a later dated note explicitly re-admits them. Perturbation
runs remain sensitivity or correlation-support data and should not be mixed
with nominal baseline runs.

Paper-grade or near-paper-grade anchors now live in these reports:

- `reports/2026-06/2026-06-29/2026-06-29_ethan_paper_case_inventory/`
- `reports/2026-06/2026-06-29/2026-06-29_ethan_reduction_contract_audit/`
- `reports/2026-06/2026-06-29/2026-06-29_ethan_closure_status_gate/`
- `reports/2026-06/2026-06-29/2026-06-29_ethan_upcomer_recirculation_evidence/`
- `reports/2026-06/2026-06-30/2026-06-30_3d_to_1d_field_reduction_methods/`
- `reports/2026-06/2026-06-30/2026-06-30_claude_closure_results/`
- `reports/2026-07/2026-07-01/2026-07-01_presentation_readiness_and_rom_agenda/`
- `reports/2026-07/2026-07-01/2026-07-01_rom_model_form_fits_and_1p4_boundary/`

The external paper repository `../papers/3d_analysis` was inspected read-only.
It still appears anchored mainly to June 15-22 evidence packages. It has not yet
absorbed the June 29, June 30, or July 1 readiness packages listed above.

## Findings To Carry Forward

Geometry and reduction provenance are now much stronger than the paper's
current evidence map. The ROM and paper should use mesh-derived geometry and
station provenance, not schematic probe CSV endpoints, for loopwise closure
extraction. Endpoint and fitting stations remain excluded from straight-friction
fits.

Pressure post-processing is usable only after role classification. `p_rgh`,
corrected pressure, absolute/total pressure, static-gradient terms, and
buoyancy-contaminated apparent resistance cannot be treated as interchangeable.
The current audit found 36 pressure/friction rows, 6 direct-friction candidates,
and 12 buoyancy-contaminated apparent-resistance rows. Variable-density
buoyancy decomposition is still missing.

Thermal closure values for Salt 2/3/4 Jin are near paper-ready with a mesh-GCI
caveat. The current OF13-reconstructed table gives lower-leg HTC values of
approximately `252`, `269`, and `288 W/m2-K`; lower-leg `UA'` values of
approximately `16.6`, `17.7`, and `18.9 W/m-K`; and upcomer Nu values of
approximately `3.11`, `4.06`, and `4.99`. Treat `UA'` as the primary energy
closure and Nu as a diagnostic or correlation candidate until uncertainty and
property-temperature checks are complete.

The upcomer is not ordinary straight-pipe friction. Current evidence indicates
a buoyancy-driven recirculation or convection cell. Reversed-area fractions in
the June 29 evidence package are about `0.607`, `0.625`, `0.663`, and `0.680`
for Salt 1-4 Jin, while right-leg reversed area is reported as zero in the same
screen. This belongs in the mechanism narrative and in the trust boundary for
1D closure fitting.

The July 1 1D work added the missing `1.4 in` insulation boundary scenario and
compact dense model-form fits. Best compact Salt 2-4 mdot result is
`fit_major_k90_1p4`, with `major_loss_multiplier=2.1`, `k90=0.0`, `k20=0.0`,
mean absolute mdot error `3.103%`, RMSE `3.594%`, and mean energy error
`14.027%`. This is useful for ROM model-form comparison, but it is not a final
physical claim. The `k90=0` result should be interpreted as identifiability and
compensation in an mdot-only compact fit, not as evidence that bend losses
vanish.

The June 23 1D validation bundle remains a diagnostic baseline, not final
predictive proof. The July 1 readiness matrix records best energy error
`11.274%` and mass-flow relative error `26.691%` for that defended scenario.
Future ROM scoring should evaluate mass flow, energy balance, pressure
distribution, and sensor-temperature parity together.

## Paper-Ready Pieces Not Yet In The Paper

The highest-confidence material to move into the paper next is listed in
`paper_ready_not_yet_in_paper.csv`. In short:

- update the case-selection and provenance story using the June 29 inventory
  and run-classification policy;
- replace older source-package anchors with the June 29 reduction contract and
  June 30 3D-to-1D field-reduction methods;
- add mesh-derived geometry/station provenance as the current method;
- add Salt 2/3/4 Jin OF13 thermal closure coefficients with explicit GCI and
  property caveats;
- add the upcomer recirculation evidence as mechanism and trust-boundary
  support;
- carry the July 1 ROM fits as an internal diagnostic and meeting figure source,
  not as a final paper claim.

## Not Paper-Ready Yet

Do not present these as final paper claims without additional work:

- mesh-independence or GCI uncertainty bounds;
- a physically unique bend-loss or minor-loss coefficient from the compact mdot
  fit;
- upcomer straight-pipe friction;
- variable-density buoyancy decomposition;
- experimental validation;
- full dense model-form search;
- any convergence claims for the long running CFD jobs without checking
  residuals, heat balance, flow stability, and latest-window station metrics.

## Tomorrow Agenda

1. Check `.agent/status/2026-07-01_AGENT-170.md`,
   `.agent/status/2026-07-01_AGENT-164.md`, and the active AGENT-171 status.
2. Run `squeue -u andresfierro231` and inspect the four long CFD jobs and the
   dev node job. Confirm which are finished, still running, or failed.
3. If long CFD jobs have usable windows, extract latest-window heat balance,
   mass flow, pressure role, and thermal closure summaries before updating the
   paper state.
4. Use `paper_ready_not_yet_in_paper.csv` as the first paper-integration queue.
   Open a separate paper-edit task before modifying `../papers/3d_analysis`.
5. Keep the July 1 compact ROM fit as a model-form comparison baseline. Schedule
   the full dense fit only after deciding the scoring vector and compute budget.
6. Preserve scaling-study notes as postponed. None of the scaling jobs were
   submitted in this cycle, and one planned scaling job from yesterday should be
   resubmitted when the scaling study resumes.

## Files In This Package

- `paper_ready_not_yet_in_paper.csv`: pass-to-paper queue with readiness,
  provenance, paper gap, and recommended target section.
- `simulation_state_for_paper.csv`: compact state table for CFD, closures, ROM,
  uncertainty, and validation.
- `tomorrow_next_steps.csv`: prioritized operational agenda.
- `source_review_index.csv`: source-review ledger separating reviewed current
  anchors from historical journals/reports that still need a full paper-pass
  audit.
- `README.md`: this close-safe narrative.

## Source Review Boundary

This is a first paper-state compilation, not a completed audit of every historic
journal line. Current June 29-July 1 report anchors, active July 1 task journals,
and paper-readiness operational notes were reviewed directly. Older June 2-26
reports and journals were inventoried as prior evidence or superseded context
and should be re-read before any older figure, coefficient, or claim is promoted
into the manuscript.
