# 2026-06-25 Ethan Normal Relaunch And Recirculation Boundary Wave

## Purpose

This campaign relaunches the failed `normal`-partition Ethan follow-ons on
fresh staged roots and extends the Salt heater-only boundary sweep to better
diagnose upcomer recirculation onset.

The campaign keeps three constraints explicit:

- do not mutate the June 18 / June 19 live running roots in place; reuse only
  non-live failed relaunch roots directly, and stage fresh June 25 copies only
  for the genuinely new Salt boundary cases;
- keep the campaign-local OpenFOAM runtime dependency reproducible by copying
  `libRCWallBC.so` into `runtime_libs/` under `/scratch`;
- keep new Salt boundary cases on the defended heater-only, baseline-insulation,
  residual-balanced cooling-branch path rather than reopening the rejected
  insulation-only wave.

## Why this relaunch exists

The recovered `normal` jobs `3254180` and `3254181` started on `2026-06-25`
and failed in `2-3 s` before solver launch because their scripts required
`libRCWallBC.so` under `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data`.
The same campaigns were otherwise scientifically valid and the live
`NuclearEnergy` recovery jobs still prove the staged roots themselves were not
corrupt.

This wave therefore reuses the same case intent but changes the runtime
packaging:

- failed Water and Salt high-Q relaunches reuse their existing non-live staged
  roots directly, while new Salt cases use lightweight June 25 stage roots that
  materialize `processors64/` from recorded source paths only if needed at job
  launch time;
- every submitted job points `RCWALLBC_LIBDIR` at
  `jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runtime_libs/`;
- every `normal` job requests one `128`-CPU node for `2 x 64` concurrent cases;
- the scientific target remains `216 h` (`9 d`), but `qnormal` hard-caps each
  individual job at `48 h`, so each packed pair is submitted as a five-segment
  `afterany` chain on the same case roots.

## Requested relaunch set

The user-requested relaunch scope is:

- Water continuations: `water1`, `water2`, `water3`, `water4`
- Salt follow-ons: `salt1_jin` continuation plus Salt `1-4` high-Q

The Water jobs are relaunched from the June 23 retained-window staged roots so
they preserve the last defended continuation state rather than reverting to the
older June 1 staging snapshot.

The Salt high-Q relaunches keep the June 22 corrected contract:

- baseline insulation restored
- lower-heater power changed only through the visible heater patches
- cooling-branch fixed sinks solved from the preserved parent late-window
  ledger

## Extra recirculation-boundary design

The existing Salt operating table already shows that mean state and loop
`Delta T` are not locked together:

- `Salt 1 Jin` is the lowest-mean case (`temp_upcomer_bulk_k ~= 436.66 K`) but
  has the largest baseline loop temperature span
  (`heater_to_cooler_bulk_delta_k ~= -3.13 K`,
  `max_branch_temp_delta_k ~= 8.24 K`)
- `Salt 4 Jin` is the hottest mean-state case
  (`temp_upcomer_bulk_k ~= 482.52 K`) yet its baseline heater-to-cooler span is
  smaller in magnitude (`~-2.63 K`)
- `Salt 2 Jin` and `Salt 3 Jin` sit between those limits in both bulk state and
  operating point

That partial decoupling means the cleanest next onset screen is:

1. retain the requested Salt `1-4` high-Q cases to push the heater-to-cooler
   span upward;
2. add `salt1_jin_loq_balq` so the low-mean Salt 1 anchor is bracketed on both
   sides and no half-empty `normal` node is needed;
3. add new balanced midpoint `+5%` and `-5%` heater cases for Salt `2-4` so the
   transition can be localized without the rejected insulation uncertainty.

This yields a compact four-level Salt ladder:

- Salt 1: base continuation, `-10%`, `+10%`
- Salt 2/3/4: live base continuation, live `-10%`, new `-5%`, new `+5%`, new
  `+10%`

That is the best bounded CFD set currently readable from the repo for testing
whether upcomer recirculation onset follows primarily:

- hotter global mean state,
- larger loopwise heater-to-cooler temperature span,
- or a mixed threshold across both.

## Job packing

| Chain name | Cases | Partition | Nodes | Tasks | Segment walltime | Chain length | Effective coverage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ethan_w12_nq9d` | `water1`, `water2` | `normal` | `1` | `128` | `48 h` | `5` | `240 h` |
| `ethan_w34_nq9d` | `water3`, `water4` | `normal` | `1` | `128` | `48 h` | `5` | `240 h` |
| `ethan_s1cont_s1hi_nq9d` | `salt1_jin_basecont`, `salt1_jin_hiq_balq` | `normal` | `1` | `128` | `48 h` | `5` | `240 h` |
| `ethan_s23hi_nq9d` | `salt2_jin_hiq_balq`, `salt3_jin_hiq_balq` | `normal` | `1` | `128` | `48 h` | `5` | `240 h` |
| `ethan_s4hi_s1lo_nq9d` | `salt4_jin_hiq_balq`, `salt1_jin_loq_balq` | `normal` | `1` | `128` | `48 h` | `5` | `240 h` |
| `ethan_s2mid_nq9d` | `salt2_jin_hi5q_balq`, `salt2_jin_lo5q_balq` | `normal` | `1` | `128` | `48 h` | `5` | `240 h` |
| `ethan_s3mid_nq9d` | `salt3_jin_hi5q_balq`, `salt3_jin_lo5q_balq` | `normal` | `1` | `128` | `48 h` | `5` | `240 h` |
| `ethan_s4mid_nq9d` | `salt4_jin_hi5q_balq`, `salt4_jin_lo5q_balq` | `normal` | `1` | `128` | `48 h` | `5` | `240 h` |

## Reproduction

- manifest: `campaign_manifest.csv`
- staging helper: `scripts/stage_cases.py`
- packed launcher: `scripts/run_packed_two_case_normal.sbatch`
- submission helper: `scripts/submit_jobs.sh`

## Lightweight restart staging

New Salt-only stage roots deliberately record the source restart tree in `SOURCE_PROCESSORS64.txt` instead of copying every processor file ahead of time. The packed launcher populates `processors64/` from that recorded path only when the staged root does not already contain it. This keeps the source roots immutable while avoiding a large pre-submit copy delay on `/scratch`.
