# AGENT-156 Phase 2 Raw Journal — continuation reproducibility + velocity anomaly

Date: `2026-06-30`
Role: Coordinator / Implementer / Writer
Owner: claude
Task: AGENT-156 phase 2 (the two follow-ups the user prioritized).

## Task 2 — velocity flux anomaly: ROOT-CAUSED and FIXED

Observed: in phase 1, `areaAverage(U)·n` at clean cross-sections was ~0 (implied
mass flux ~100x below the mdot monitor), so the dynamic-head term was untrusted.

Root cause (decisive evidence, salt2_jin parent t=2431):
- Dumped the raw cut-plane `U` and decomposed: mean SPEED `<|U|>` ~0.015 m/s
  (healthy), but the mean VECTOR ~0 -> directions CANCEL.
- Spatial split of the TW2 plane: faces cluster in TWO blobs, x~0 (Uy=+0.021)
  and x~0.888 (Uy=-0.012). The bounded plane spanned the WHOLE domain at that
  height and averaged two counter-flowing legs.
- Cause: the `cuttingPlane` `bounds` keyword is an ESI/foam-extend feature that
  OpenFOAM **Foundation** silently ignores. So every phase-1 plane averaged
  multiple legs -> velocity cancelled AND area came out ~2.2x a single bore (two
  bores). The phase-1 section-mean p_rgh was therefore ALSO contaminated.

Fix (verified): isolate a SINGLE leg by keeping faces within `--leg-radius-m`
(0.04 m) of the station point, in Python, on the raw `.xy` dump. Post-mask flow
alignment |meanU|/<|U|> = 0.99-1.00 at clean stations; u_bulk ~0.0135 m/s,
consistent with mdot/(rho*bore). Dynamic head now ~0.18 Pa at clean stations
(small but real, ~1% of the +/-20 Pa p_rgh swings — expected for U~0.014 m/s).

Deliverables: rewrote `tools/extract/sample_section_mean_pressure.py` (raw dump +
single-leg masking; flow-alignment gate; corner stations auto-flagged). New
`tools/analyze/diagnose_section_velocity.py` records the full-plane-vs-masked
evidence permanently.

## Task 1 — mainline continuation reproducibility: LARGELY RESOLVED

Observed: phase-1 reconcile reported 13/14 freeze-window lanes unverifiable — but
it only searched `staging/`. The mainline CONTINUATION data is staged locally
under `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/
{salt1..4}_jin,water1..4/case_stage/..._continuation/processors64/` (salt2->7915,
salt3->7618, salt4->10000, salt1->4026, water to 5036-9609). Upstream
`/scratch/09807/ethanrozak/` is also readable.

Actions:
- Extended `reconcile_freeze_windows.py` to search `staging/` AND `jadyn_runs/`,
  add `_continuation` candidate names, and pick the max-time tree. Result: now
  8/14 verifiable_on_disk (all nominal continuation + water lanes); the remaining
  5 unverifiable are the hiq/loq PERTURBATION lanes (separate sensitivity group,
  different times) and salt2_loq partial.
- Ran convergence (#2) on the four mainline Salt-Jin continuations (no recon
  needed; reads postProcessing): Salt 2/3/4 STATIONARY (hydraulic+thermal; heat
  closes +0.04/+0.07/+0.01% of ~487/546/621 W gross). Salt 1 stationary but
  closes only -2.08% (its short-window caveat persists even at t=4026).
  Cross-check: gross duties match the parent-warmup values -> consistent steady
  state across warmup and continuation.
- Set up + reconstructing the salt2_jin CONTINUATION (t=7915) into tmp for a
  closure-grade section-mean pressure rerun.

## Interpretation

- The reproducibility gap is mostly an INDEXING gap, not a data gap: the mainline
  field data exists locally; it was never registered into `staging/`/`registry`.
- Registering it into the shared `registry/case_registry.csv` needs coordinator
  approval (shared file) — flagged, not done unilaterally. See the staging plan.

## Open / next

- Finish salt2_jin continuation reconstruction -> rerun section-mean (#1) on the
  mainline; extend to salt3/4_jin.
- Decide with coordinator whether to register continuation runs into the canonical
  registry (vs leaving them in jadyn_runs with an index).
- Perturbation (hiq/loq) lanes remain unverifiable here by design (sensitivity).
