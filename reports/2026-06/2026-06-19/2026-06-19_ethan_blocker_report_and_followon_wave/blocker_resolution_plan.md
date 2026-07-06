# Blocker Resolution Plan

Generated: `2026-06-19`

## Purpose

Separate the remaining blockers into:

- work that more CFD runtime can solve;
- work that needs a new retained-time extraction path before more CFD becomes
  scientifically useful.

## Blocker classes

### 1. Feature `K_eff` full-path closure

- current status: `not_defensible_yet`
- current failure mode: proxy endpoint `p_rgh` plus local straight-reference
  evidence exists, but a retained-time feature-path hydro integral does not
- key implication: more runtime by itself will only create more proxy-positive
  rows, not a defended feature closure

Required sequence:

1. build a retained-time feature-path extractor that preserves pathwise
   density / hydro integrals and the corresponding dissipative feature drop;
2. emit a per-feature, per-time table with at least:
   - `source_id`
   - `feature_name`
   - `time_s`
   - `mdot_kg_s`
   - `re_effective`
   - `delta_p_total_pa`
   - `delta_p_hydro_pa`
   - `delta_p_dissipative_pa`
   - `keff_effective`
   - support / sign / residual gates
3. rerun the feature hardening package and the v3 dependency package on the
   new preserved table;
4. only then decide whether extra feature-positive CFD cases are still needed.

Best next CFD role for this blocker:

- low immediate priority
- let the current continuations keep improving retained-time support, but do
  not open a dedicated feature DOE until the extractor exists

Release criterion:

- at least one feature class moves from `proxy_only_available` to an explicit
  retained-time pathwise closure with positive dissipative loss and fit-ready
  support.

### 2. Straight-section late-window retained rows

- current status: straight friction is `provisional_defended`
- current failure mode: fit-used rows are preserved as case means, so the
  late-window sensitivity audit is formally `not_run`
- key implication: this blocker can be improved by more runtime on the current
  cases, because the missing information is retained-time support rather than a
  fundamentally absent physical observable

Required sequence:

1. let the June 18 continuations finish long enough to preserve a real late
   window on the active Salt Jin and Water cases;
2. rebuild retained-time hydro-corrected straight rows from those
   continuations;
3. rerun the straight hydraulic sensitivity package with a true last-window
   check;
4. if stable, promote straight friction from case-mean-only support toward a
   stronger late-window-backed claim.

Best next CFD role for this blocker:

- highest immediate CFD priority
- current continuation jobs are already the right move
- after those complete, the next bounded scenario expansion remains the
  deferred Salt 3 Jin midpoint bracket, not a new family or physics change

Release criterion:

- retained-time defended straight rows exist for the last approximately `20 s`
  window, and the late-window sensitivity package is rerun from preserved rows
  instead of a formal blocker note.

### 3. Water closure hardening

- current status: readiness-only
- current failure mode: Water still lacks closure-gated hydraulic and thermal
  support strong enough for defended dependency fitting
- key implication: Water should consume current continuations first, not a new
  DOE wave

Required sequence:

1. recover stronger retained-time support on the already-running Water cases;
2. repeat the Salt-style closure gates on Water with the updated retained-time
   evidence;
3. only then decide whether Water needs a bounded scenario bracket.

Best next CFD role for this blocker:

- medium priority
- keep Water out of new scenario expansion until the existing continuations are
  analyzed

Release criterion:

- Water moves from readiness-only to at least one closure-gated dependency
  subset with explicit admitted rows.

## Immediate decision ladder

1. Keep monitoring the currently running June 18 continuations.
2. Keep the newly submitted Salt 2 / Salt 4 heater-plus-insulation bracket
   wave in queue.
3. Do not submit new Water scenarios yet.
4. Do not submit a dedicated feature `K_eff` DOE yet.
5. If another new submission is justified before extractor work lands, make it
   the deferred Salt 3 Jin midpoint bracket.

## Checkpoints

- `CP1`: the active continuation cases preserve a usable retained-time late
  window rather than only inherited short tails
- `CP2`: straight retained-time defended rows are rebuilt from preserved
  continuation data
- `CP3`: the late-window straight sensitivity package is rerun from those rows
- `CP4`: a retained-time feature-path extractor emits a machine-readable path
  integral table
- `CP5`: feature `K_eff` hardening is rerun on the new pathwise table
- `CP6`: Water is reclassified from readiness-only to a closure-gated subset,
  or explicitly held back again with updated evidence
