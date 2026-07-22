# Tomorrow Unlock Execution Plan

Task: AGENT-445
Date: 2026-07-15

## Objective

Turn the current diagnostic evidence into admission-ready hydraulic and
closure-QOI decisions. The immediate missing pieces are pressure orientation,
straight-loss subtraction, recirculation masks, and consistent branch-specific
coefficient labels. Mesh/GCI remains a separate admission gate; do not promote
coarse-only rows to final fits.

## Overnight / Live Jobs To Check First

| Job | Name | Source row | Expected output | Tomorrow action |
| --- | --- | --- | --- | --- |
| `3297860` | `press_ladder` | AGENT-445 | 30 station planes per Salt2/Salt3/Salt4; station and adjacent pressure deltas | If terminal, run AGENT-445 harvest and open `station_pressure_ladder.csv` plus `adjacent_pressure_ladder.csv`. |
| `3297843` | `pm5_onset` | AGENT-439 | matched-plane/onset extraction | Harvest for recirculation/onset metrics before any true coefficient fit. |
| `3297844` | `m3ts_score` | AGENT-439 | M3+TS scorecard | Use for forward model score, not pressure admission. |
| `3297842` | `val_s2_ext` | AGENT-439 | val_salt2 external-test processing | Use for validation boundary evidence. |
| `3293924` -> `3295438` | `saltq_sel_cont` -> `saltq_s24_sel_harv` | corrected-Q chain | terminal corrected-Q harvest | Do not duplicate while dependency chain is live. |

## Tomorrow Work Sequence

1. Check job terminal states with `sacct`.
2. Harvest completed jobs into their owning packages; do not mix outputs across
   packages until each package has a status/journal/import closeout.
3. For AGENT-445, build `pressure_orientation_by_branch.csv` from adjacent
   pressure deltas:
   - compare `p` and `p_rgh` trends;
   - label likely upstream/downstream direction by branch;
   - flag branches where reverse-area fraction makes a single stream invalid.
4. Build `straight_loss_subtraction_screen.csv`:
   - use adjacent within-branch station deltas;
   - identify candidate straight/developing spans;
   - isolate connector/test-section residual only after adjacent straight loss
     is estimated.
5. Build `hydraulic_coefficient_admission_candidates.csv`:
   - true `f_D`/`K`: only low-recirculation, admitted pressure-definition rows;
   - section-effective diagnostic: recirculating or orientation-ambiguous rows;
   - blocked: missing pressure planes, no straight-loss subtraction, no mesh/GCI.
6. Reconcile with PM5/onset:
   - merge RAF/RMF/SVF/Ri/Re/Pr/Gz when AGENT-439 output lands;
   - preserve upcomer as recirculation/hybrid/onset lane, not ordinary pipe fit.
7. Update final forward-v1 gate only if all required lanes are admitted. Most
   likely tomorrow result is a narrower blocked state, not full final admission.

## Do Not Do

- Do not treat AGENT-445 pressure ladder as mesh/GCI proof.
- Do not compute final component `K` before straight-loss subtraction.
- Do not fit true `f_D`, `K`, or `Nu` on recirculating rows.
- Do not use realized CFD wall heat flux or pressure rows as predictive runtime
  inputs.
- Do not mutate native CFD solver outputs or registry/admission state.

## Success Criteria For Tomorrow

- Pressure orientation table exists by branch and case.
- Straight-loss subtraction screen exists with explicit blockers.
- Recirculation masks are joined or explicitly pending.
- Each candidate coefficient row is labeled true-fit, section-effective
  diagnostic, validation-only, or blocked.
- Final forward-v1 remains blocked unless all admission gates explicitly pass.
