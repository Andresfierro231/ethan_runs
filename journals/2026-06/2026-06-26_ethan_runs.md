# 2026-06-26 Ethan Runs

## Observed Output

- Built a new synthesis package under
  `reports/2026-06/2026-06-26/2026-06-26_ethan_progressive_story_synthesis/`
  to turn the journal trail plus the analytical report stack into one dated
  narrative.
- The package includes:
  - `README.md`
  - `phase1_journal_synthesis.md`
  - `phase2_report_gap_scan.md`
  - `phase3_full_report_synthesis.md`
  - `open_analysis_queue.md`
  - `open_analysis_queue.csv`
  - `source_map.csv`
  - `analysis_followups.csv`
- The source pass covered:
  - all journal files from `2026-05-29` through `2026-06-25`
  - the analytical report packages from `2026-06-02` through `2026-06-23`
  - blocker, contradiction, readiness, and phase-plan tables where they
    existed

## Inferred Interpretation

- The work history is now much easier to read as one continuous progression:
  - the project started as intake plus validation triage
  - became a Salt 2 hydraulic and heat-accounting repair campaign
  - expanded into a cross-case transport and trust-gating workflow
  - then pivoted into Salt-first closure-to-modeling handoffs
  - and finally narrowed onto frozen-state, replay, and continuation support
- The main defended results remain bounded rather than universal:
  - Salt straight friction is usable with explicit subset caveats
  - direct Salt Nu support remains strongest on `left_lower_leg`
  - `upcomer` is still a separate modeling problem
  - `right_leg` remains blocked for direct headline thermal closure
- The most repeated lesson is methodological:
  package maturity improved when the workflow separated
  `observed evidence`, `support-limited interpretation`, and
  `blocked or not-yet-defensible closure claims`.
- The deeper follow-on synthesis now also turns the open-analysis queue into a
  recommended order of work rather than leaving it as an unordered list of
  follow-up rows.

## Contradictions / Caveats

- The external readable `Fluid` replay surface is still stale relative to the
  June 22 frozen-state contract.
- Water still lags Salt in defended closure maturity, especially for any
  cross-family collapse claim.
- Several open questions are now clearer, but they are not solved by this
  synthesis alone:
  - retained-time full-path hydro support for feature `K_eff`
  - stronger last-window straight rows
  - broader retained-time thermal closure support beyond the current safe
    branch subset

## Next Suggested Actions

- Use `analysis_followups.csv` as the ranked next-analysis list.
- Use `open_analysis_queue.md` when the goal is to choose the next real
  analysis task rather than just inspect the unresolved rows.
- Keep the next phase bounded to one blocker-reduction lane at a time instead
  of reopening a broad mixed report/campaign wave.
- If the goal is a stronger 1D closure story, the next highest-value lanes are:
  - refreshed external replay against the frozen-state contract
  - retained-time straight refresh after the continuation windows mature
  - retained-time branchwise thermal support on currently blocked branches

## Observed Output

- Repacked the June 25 pending `normal` continuation/boundary wave off the
  `3259055-3259094` chain and onto four `NuclearEnergy` submissions after two
  extra nodes became available.
- Confirmed the live `NuclearEnergy` partition limit is `5-00:00:00`, so the
  requested `6 d` pack had to be submitted at the legal maximum `120 h`.
- Submitted:
  - `3261320` `ethan_s123hi_ne5d` for
    `salt1_jin_basecont`, `salt1_jin_hiq_balq`,
    `salt2_jin_hiq_balq`, `salt3_jin_hiq_balq`
  - `3261321` `ethan_s41lo2mid_ne5d` for
    `salt4_jin_hiq_balq`, `salt1_jin_loq_balq`,
    `salt2_jin_hi5q_balq`, `salt2_jin_lo5q_balq`
  - `3261322` `ethan_s34mid_ne5d` pending on `afterany:3254179`
  - `3261323` `ethan_w1234_ne5d` pending on `afterany:3254178`
- The immediate packs started at once on the four newly free `NuclearEnergy`
  nodes, while the superseded `normal` jobs disappeared from `squeue`.

## Inferred Interpretation

- The user-requested case grouping and dependency intent were preserved even
  though the walltime target had to be shortened from `6 d` to `5 d`.
- Packing four `64`-rank runs across two `NuclearEnergy` nodes remains
  operationally acceptable for this continuation class because the two new
  immediate jobs started without waiting for more nodes beyond the newly opened
  capacity.

## Contradictions / Caveats

- The `NuclearEnergy` queue policy, not the user request, set the effective
  walltime cap. Any pack that needs more than `120 h` will still require a
  continuation strategy.
- This pass restructured queue placement only. It did not audit solver health
  inside the already running anchors `3254178` and `3254179`.

## Next Suggested Actions

- Check the first-hour `slurm` logs for `3261320` and `3261321` to confirm that
  all four packed subruns in each job reached solver time advancement cleanly.
- Before either running pack nears `120 h`, decide whether a continuation chain
  will be needed to preserve progress beyond the `NuclearEnergy` walltime cap.
