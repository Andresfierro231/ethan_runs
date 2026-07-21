# Action-Item Package — CFD→1D Closure Rigor (AGENT-156)

Date: `2026-06-30`
Owner: claude (AGENT-156)
Companion workflow note: `operational_notes/06-26/30/2026-06-30_cfd_1d_closure_workflow.md`
Motivating review: `.agent/journal/2026-06-30/claude-inspection-cfd-1d-closure-postprocessing.md`

This package addresses the 8 ranked action items from the 2026-06-30 inspection
of the CFD post-processing → 1D closure pipeline. It separates **observed
output**, **interpretation**, and **confidence boundaries**, per the project's
disclosure and rigor principles. All numbers below are reproducible via the run
commands in the workflow note; raw artifacts are under
`work_products/2026-06-30_claude_*/`.

## Scope

Salt **Jin** paper subset (Salt 2/3/4 Jin primary; Salt 1 Jin caveated). Kirst =
historical/sensitivity only; perturbation lanes = separate sensitivity group
(per the repo run-classification rule). Water out of scope here.

---

## Results by item

### #2 Convergence (DONE) — `assess_time_convergence.py`
Observed: over the staged window, **Salt 2/3/4 Jin are stationary** in both loop
`mdot` (drift <0.15%, autocorr-corrected SE ~0.02%) AND gross wall heat duty
(drift <0.2%; ~487/546/621 W gross), with net heat imbalance closing to
**<0.2% of gross duty**. **Salt 1 Jin is only quasi-stationary** (1.3% mdot
drift) with a **−2.4%** heat-closure residual.
Interpretation: the late-window "frozen" approach is well-justified for Salt
2/3/4; Salt 1's documented short-window caveat is now quantified.
Confidence: `total_Q` is a near-zero NET imbalance — it MUST be normalized by
gross duty (this tool does), or it falsely reads as 18–54% "drift". Numbers are
for the staged (parent-warmup) window, not necessarily the continuation-closure
basis (see #6).

### #3 Closure honesty (DONE) — `represent_closures_per_case.py`
Observed: apparent Darcy `f` = **3.5–4×** (legs) and **~70×** (test section) the
fully-developed laminar `64/Re`. **~20%** of the apparent Re spread within a
physical case is pure Jin-vs-Kirst property choice. Jin-only fits have **dof ≤ 1**
(R²=1.000 is an overfit artifact, flagged). `log Re` and `log Pr` are
**collinear (corr −1.00)**.
Interpretation: the "apparent friction factor" is form/entrance-loss dominated,
not wall friction; the closures are single-regime **calibrations**, not
correlations; **Nu(Re,Pr) is not identifiable** — only Nu(Re) is, and even that
is saturated. Never query outside Re≈76–174 or for water.

### #6 Provenance (DONE) — `reconcile_freeze_windows.py`
Observed: **13 of 14** freeze-window lanes are **unverifiable** from the staged
data; claimed representative times exceed on-disk by 450–6041 s. Only
`salt1_jin` partially overlaps (2/18 times).
Interpretation/confidence: the mainline continuation (and hiq/loq) field data is
not in this workspace, so closures built on it cannot be re-derived here. Stage
that data to close the gap.

### #7 Segment map (DONE) — `validate_segment_map.py` + segment-map note
Observed: all closure-artifact segment tokens resolve except **`upcomer`**
(ambiguous) and **`heated_incline`** (provisional → `lower_leg`). The token
`lower_leg` is the RIGHT vertical heated leg (name is misleading).
Confidence: 2 open questions for Ethan before the map is final.

### #1 Section-mean pressure (workflow DONE; numbers partial) — `sample_section_mean_pressure.py`
Observed: established a non-mutating v12-reads-v13 reconstruction + cut-plane
sampling workflow; produced per-station **section-mean static `p_rgh`** for
salt2_jin (t=2431) and a **measured median bore area ≈ 7.9e-4 m²**.
Confidence: section-mean static pressure is sound on straight ("ok"-gated)
stations; **the dynamic-head term is NOT yet trustworthy** — area-averaged
normal velocity integrates to ~0 (mass flux ~100× below the mdot monitor),
flagged as the top open issue. This is a method demonstration on parent-warmup
data, not closure-grade.

### #4 Measured geometry (partial)
The legacy extractor's idealized circular area differs from the **measured**
median bore by ~2.2×; feeding measured area into `f` is a proposed patch
(workflow note §4). The measurement capability now exists (#1 tool).

### #5 Mesh independence (protocol DONE) — `operational_notes/06-26/30/2026-06-30_mesh_independence_protocol.md`
3-level GCI study on Salt 2/4 Jin defined; blocked on OF13 runtime +
`libRCWallBC.so`; sbatch-scoped.

### #8 Smaller corrections (documented)
Signed τ_w, ρ·u·cp bulk-T weighting, `qr` disclosure, NaN-handling, stale-surface
versioning — all specified as proposed patches (workflow note §4) for the
extractor owner (codex/AGENT-155), since AGENT-156 does not edit that file.

---

## What is sound vs what is not (one-glance)

- SOUND now: convergence evidence (Salt 2/3/4), honest closure re-presentation,
  provenance reconciliation, segment map (minus 2 confirmations), reconstruction
  + section-mean static pressure workflow.
- NOT yet: dynamic-head/total-pressure numbers (velocity anomaly), closure-grade
  re-run on mainline continuation data, mesh-independence bounds, the 2 segment
  confirmations.

## Reproduce
See `operational_notes/06-26/30/2026-06-30_cfd_1d_closure_workflow.md` §0–§2. Tests:
`python -m pytest tools/analyze/test_claude_action_items.py -q` (9 passing).
