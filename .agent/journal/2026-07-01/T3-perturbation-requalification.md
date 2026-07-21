# T3 — Perturbation-Run Operating-Point Requalification (convergence gate)

Date: `2026-07-01` · Owner: claude (AGENT-166; prompt said AGENT-164 but that ID was
already claimed by codex/claude for T2, and 165 by codex — took the next free ID 166).
Task: T3 in `operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md`.
Resolves: `TODO-PERT-REQUAL`. Precursor audit:
`.agent/journal/2026-06-30/perturbation-run-convergence-audit.md`.

## 2026-07-04 addendum: quarantine strengthened

A follow-up BC audit found the stronger root cause for the flat perturbation
response: the historical Salt Q perturbation roots are invalid closure data, not
merely too short. The intended Q changes were not reliably present in the
decomposed restart fields that `foamRun` actually read, and some root `0/T`
files changed only one lower heater patch while leaving the other two lower
heater patches nominal. Therefore the June 19/25 Salt Q perturbation roots are
quarantined. Do not use them for friction, HTC, closure-correlation, Re-response,
or 1D validation fits. They are admissible only as workflow-failure provenance.

Replacement campaign:
`jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/`. The
corrected workflow patches root `0/T`, patches copied
`processors64/<latest>/T` immediately before solver launch, and audits all three
lower heater patches plus the balanced upper cooling patches.

## Problem statement

`tools/analyze/assess_time_convergence.py` measures monitor *stationarity* (trailing-
window drift + peak-to-peak + autocorrelation-corrected SE). That is **necessary but
not sufficient** for a *perturbation* run to be at its NEW steady state. The salt_jin
perturbation runs (hiq/loq/hi5q/lo5q, and the hiins/loins that in practice only changed
Q) restart from the nominal converged field. Advanced only a fraction of the loop
thermal relaxation time, they sit — flat — at the OLD (nominal) fixed point. A flat
monitor pinned at nominal after a real ±5–10% heater-power change is **false-steady**:
steady-looking, not re-equilibrated. Using such points would fabricate false
repeatability / non-distinct Re in the upcomer correlation (lane U1 / T10).

## Method (what "converged" must mean for a perturbation run)

The gate requires BOTH:

1. **The operating point MOVED** from the nominal baseline by ~the physically expected
   amount. For a laminar natural-circulation loop the buoyancy/friction balance gives
   `mdot ~ Q^(1/3)` (Grashof-driven driving head ∝ Q via the bulk ΔT; laminar wall
   friction ∝ mdot). So a heater-power ratio `r = Q_pert/Q_nom` should move mdot by
   `|r^(1/3) − 1|`:
     - +10% Q → +3.23%   ;  −10% Q → −3.45%
     - +5%  Q → +1.64%   ;  −5%  Q → −1.70%
   We accept the run as "moved" only if the observed fractional move
   `|mdot_pert − mdot_nom|/|mdot_nom|` reaches at least `--move-tolerance` (default 0.5)
   of that expectation. A move below 25% of expectation is flagged specifically as
   `false_steady` (as opposed to a mere `insufficient_move`).

2. **It re-plateaued** — the hydraulic monitors themselves are (quasi-)stationary in the
   trailing window (reusing the existing drift/amplitude test).

The gate also reports the **advance-past-restart** = `t_end − restart_time`, where the
restart time is detected from the monitor restart-segment directory names. Staged trees
sometimes carry an inherited `t=0` segment (nominal warmup/continuation history); the
perturbation proper begins at the smallest NON-zero segment start when a zero segment
coexists with later ones, else at the smallest segment start
(`restart_time_from_segments`). When a thermal time constant `τ` is supplied
(`--tau-thermal`, τ ≈ ρ cp V_loop / UA), advance is also reported as `advance/τ` and runs
with `advance < --min-tau-advance·τ` (default 3τ) are flagged `too_short`.

Verdicts (precedence): `false_steady` (not moved, <25% of expected) → `insufficient_move`
(moved but <tolerance) → `moving_not_plateaued` (moved but hydraulic not stationary) →
`too_short` (moved+plateaued but advance<3τ) → `requalified` (usable). q_ratio≈1 runs are
relabeled `control_no_q_perturbation` (nothing to re-equilibrate to).

### Baselines and inputs
- Nominal mdot baseline per salt = trailing-window mean of the test-section mdot monitor
  (`mdot_pipeleg_left_04_test_section`) of the **mainline Jin continuation**
  (`jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt{1..4}_jin/.../*_continuation`):
  salt1 −0.01124, salt2 −0.01320, salt3 −0.01499, salt4 −0.01712 kg-flux/s.
- Nominal heater power Q (W): salt1 232.3, salt2 265.7, salt3 297.5, salt4 337.6
  (from each nominal continuation `case_config.yaml`).
- Perturbation Q read from each run's `case_config.yaml`; q_ratio = Q_pert/Q_nom.
- Pure Python, read-only postProcessing; no OpenFOAM compute, no reconstructPar; system
  python3 + numpy. No jadyn_runs case was mutated.

τ was **not** computed here: a defensible `ρ cp V_loop/UA` needs the loop volume, which is
not available without the mesh/geometry lane (T1). The gate exposes `--tau-thermal` so τ
can be supplied later; the primary gate (mdot-moved) is fully data-driven and does not
depend on τ. This is an explicit confidence boundary.

## Per-run verdicts (all Q-perturbation runs FALSE_STEADY)

| run | q_ratio | mdot moved % | expected % | advance (s) | plateaued | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| salt2_jin_hiq_hiins | 1.10 | −0.011 | 3.23 | 5503 | yes | false_steady |
| salt2_jin_loq_loins | 0.90 | −0.004 | 3.45 | 5277 | yes | false_steady |
| salt3_jin_hiq_hiins | 1.10 | +0.084 | 3.23 | 3284 | yes | false_steady |
| salt3_jin_loq_loins | 0.90 | +0.095 | 3.45 | 3087 | yes | false_steady |
| salt4_jin_hiq_hiins | 1.10 | +0.023 | 3.23 | 6228 | yes | false_steady |
| salt4_jin_loq_loins | 0.90 | +0.086 | 3.45 | 4115 | yes | false_steady |
| salt2_jin_hi5q_balq | 1.05 | +0.098 | 1.64 | 2537 | yes | false_steady |
| salt2_jin_lo5q_balq | 0.95 | +0.097 | 1.70 | 2554 | yes | false_steady |
| salt3_jin_hi5q_balq | 1.05 | +0.200 | 1.64 | 1327 | yes | false_steady |
| salt3_jin_lo5q_balq | 0.95 | +0.182 | 1.70 | 1563 | yes | false_steady |
| salt4_jin_hi5q_balq | 1.05 | +0.035 | 1.64 | 1162 | yes | false_steady |
| salt4_jin_lo5q_balq | 0.95 | +0.070 | 1.70 | 1218 | yes | false_steady |
| salt1_jin_hiq_balq  | 1.10 | +0.283 | 3.23 | 275  | yes | false_steady |
| salt1_jin_loq_balq  | 0.90 | +0.283 | 3.45 | 275  | yes | false_steady |
| salt2_jin_hiq_balq  | 1.00 | +0.300 | —    | 2432 | yes | control_no_q_perturbation |
| salt1_jin_basecont  | 1.00 | +0.319 | —    | 270  | yes | control_no_q_perturbation |

(Full record: `work_products/2026-07-01_claude_perturbation_requal/perturbation_requal.{json,csv}`.)

### Reading of the table
- Every ±10% Q run moved mdot by <0.1% (salt2/3/4 hiq/loq) against a ~3.2–3.5%
  expectation — i.e. 30–300× too small. Every ±5% run moved <0.2% against ~1.6–1.7%.
  The signs are also inconsistent with the BC (e.g. several −Q runs show a small +move),
  which is numerical drift, not a physical response. Classic false-steady.
- `salt1_jin_hiq_balq` and `salt1_jin_loq_balq` are additionally near-worthless: identical
  mdot and only ~275 s of advance past restart (barely stepped forward).
- The `hiins`/`loins` runs are NOT independent insulation variants — they only changed Q
  (`insulated.h` unchanged per the 06-30 audit), so they are treated here purely as Q
  perturbations, and they too are false-steady. Real insulation variants are T2's job.

## Which runs are usable for the upcomer correlation (U1/T10)?

**None of the current perturbation runs.** All 14 Q-perturbed runs are false-steady; the
two q_ratio≈1 runs carry no new operating point. Lane U1 / T10 therefore stays blocked on
new data and must consume the **T2 true-steady re-runs** (continue the Q and insulation
extremes for ≳3τ past restart until mdot moves to its Q^(1/3) value and re-plateaus).
When those land, re-run this gate; only `requalified` rows should feed the correlation,
each carrying its convergence status flag.

## Reproduce
```
python3 work_products/2026-07-01_claude_perturbation_requal/build_perturbation_requal.py
# or one run directly:
python3 tools/analyze/assess_time_convergence.py --source-id <name> \
  --case-dir <case_stage/...coarse_mesh> \
  --require-moved-from <nominal_mdot> --expected-q-ratio <Qpert/Qnom>
```

## Tests
- `python3 -m pytest tools/analyze/test_assess_time_convergence.py -q` → 7 passed.
- `python3 -m pytest tools/analyze/ tools/extract/ -q` → 183 passed (green baseline held).

## Confidence boundaries / limitations
- The Q^(1/3) law is the leading-order laminar-NC balance; the acceptance uses a generous
  0.5× tolerance so it does not over-reject a genuinely re-equilibrated run whose exponent
  differs modestly. The current runs fail by 1–2 orders of magnitude, so the verdict is
  robust to the exact exponent/tolerance.
- τ_thermal not computed (needs V_loop from the geometry lane); advance/τ gating is wired
  but unused until τ is supplied. The mdot-moved test alone is sufficient to reject every
  current run.
- Baseline mdot is the continuation window mean; using the last instantaneous value shifts
  it <0.05% and does not change any verdict.
