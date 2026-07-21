# Next Scope: Branch Closures, Upcomer-Cell CFD Design, Parallel Plan

Date: `2026-06-30` · Owner: claude (AGENT-156) · Audience: all agents + Ethan.
Read with: `.agent/journal/2026-06-30/1d-model-status-and-plan.md` (plan),
`operational_notes/06-26/30/2026-06-30_upcomer_convection_cell_model.md` (cell model),
`reports/2026-06/2026-06-30/2026-06-30_claude_closure_results/` (current numbers).

Operating range CONFIRMED by Ethan: loop tested ~165–210 °C; the CFD bulk T
(173/186/201 °C for Salt 2/3/4 Jin) sits inside it, so Re/Nu/Ri parameterization
needs no re-evaluation.

---

## 1. What is done / what is still blocked

DONE (mainline Salt 2/3/4 Jin continuation, closure-grade unless noted):
- Section-mean pressure + measured D_h (≈21.8 mm); convergence verified.
- Apparent friction f on the heated/forced straights (lower_leg), cross-validated
  vs the legacy fit; Re via Jin µ(T).
- HTC / UA' / R'=1/UA' / Nu per segment (B1 unlocked → T reconstructs under OF13).
- Upcomer recirculation metric (backflow fraction) paired with Ri/Ra/Re.

STILL BLOCKED / OPEN:
- **B2 coarse mesh** — no mesh-independence bound on ANY f/Nu/UA'/recirc. GCI
  harness ready (`compute_gci.py`); EXECUTION now unblocked (OF13 available) but
  needs medium/fine meshes (multi-node sbatch). This is the #1 trust limiter.
- **Downcomer (right_leg)** thermal is policy-blocked (residual bucket) and not
  yet checked for its OWN recirculation (buoyancy-OPPOSED cooled descent can also
  reverse — see §2).
- **Upcomer correlation** has only 3 coupled points; onset/max not yet bracketed
  (see §3/§4). Characteristic Ri/Ra definition needs a page-audit of the solver's
  Lc and reference ΔT before publication.
- **Fittings/bends** (minor-loss K) not yet extracted (NIST two-tap method).
- **Salt 1 Jin** provisional only (heat closes −2.08%, short window).

## 2. Are we fitting correlations for all branches? — NO, each branch differs

The branches require DIFFERENT closure types and have DIFFERENT data support.
Treating them all as "f(Re) + Nu(Re)" is wrong (LitRev ch.13/14 explicitly).

| Branch (CFD span) | Closure type | Status / trust |
| --- | --- | --- |
| `lower_leg` (heated, ~horizontal) | Darcy f(Re) + Nu(Re)/HTC | Best-supported; cross-validated. Coarse-mesh caveat. |
| `upcomer` = left_lower + test_section + left_upper | Convection-cell + recirc correlation in Ri/Ra; Nu(Ra,Pr); NOT a friction factor | Seed data only (3 pts); onset/max unbracketed |
| `downcomer` (right_leg, cooled descent) | **DECIDED: ordinary f(Re)+Nu straight** — NO recirculation (0% backflow, alignment 0.99; clean +f 1.31/1.00/0.86). Recommend UNBLOCKING its thermal (q_w reconstructed, T available). See `2026-06-30_downcomer_closure_analysis.md` | Done (existing data) |
| bends / junctions / reducers | minor-loss K(Re) via NIST two-tap (total-pressure loss), cluster K where close-coupled | Not started |
| cooler / heater vicinity | imposed BC + residual | OK as BCs |

ACTION: add downcomer extraction + a reversal check (it is the obvious next
"branch" gap), and start fitting bend K's. Do NOT force a single loop-wide f or Nu.

## 3. CFD design to find when the upcomer cell CEASES and is at MAX

### The core difficulty (state plainly)
In a natural-circulation loop the flow rate (Re) is a RESULT of the buoyancy
balance, not an input. A heater-power (Q) sweep therefore moves the system along a
CONSTRAINED curve in (Re, Ri) space — you cannot independently set Re and the
buoyancy that drives the cell. To map an onset/limit ENVELOPE you must add a
SECOND independent knob that changes the upcomer's LOCAL transverse buoyancy
(near-wall vs core ΔT) without simply scaling the whole loop.

The cell physics: cooled near-wall fluid in the upcomer sinks while the hot core
rises → a counter-rotating cell. Strength ∝ local wall–core ΔT (set by wall heat
loss = INSULATION and cooler proximity); SUPPRESSED by loop forced flow (Re).
So **MAX cell = low insulation (max wall ΔT) + low loop Re; cell OFF = high
insulation (min wall ΔT) + high loop Re — never "heaters off" (that kills flow,
the trivial/degenerate zero).**

### Use the data we ALREADY have first (provenance below)
Perturbation runs already on disk break the Q–insulation coupling:
`jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/runs/` and
`.../2026-06-25_..._wave/runs/` contain per-case `hiq_hiins`, `loq_loins`,
`hi5q_balq`, `lo5q_balq`, `hiq_balq`, `loq_balq`, `optins`. Extracting recirc +
Ri/Re from these (convergence-gated) expands the correlation from **3 → ~15–18
points** with NO new CFD. THIS IS THE FIRST STEP (see §5 lane U1). Caveat: some
are short/unconverged (e.g. `salt2_jin_hiq_balq` latest=2431) — must pass
`assess_time_convergence.py` first.

### New CFD runs that would actually pin onset/max (ranked)
1. **High-Re / high-insulation corner pushed to cell-OFF.** The hand estimate
   (§4) puts lower-upcomer shutoff near Re≈250 vs current max ~150. Run the
   best-insulated + highest-stable-Q case long enough to reach Re≳250 and confirm
   backflow→0. This LOCATES the onset Ri_crit. (Highest value.)
2. **Low-insulation / low-Q corner for MAX.** Lowest insulation (max wall loss) +
   lowest Q that still circulates → highest Ri → cell saturation. Establishes the
   bf_max plateau.
3. **A 2-D matrix** {3–4 Q levels} × {3–4 insulation levels} per representative
   case (Salt 3 Jin as the mid anchor) to fill the (Re, Ri) interior and fit the
   onset surface, not just endpoints.
4. **(Best, if the solver/rig allows) a FORCED-flow variant** — impose an inlet
   velocity / pump term to sweep Re at ~fixed buoyancy, fully decoupling Re from
   Gr. This is the cleanest single-variable onset map and removes the coupling
   caveat entirely. Flag for Ethan: is a forced-flow boundary feasible in the rig
   model?
5. **Longer averaging + (eventually) a finer mesh** on 1–2 of the above so the
   cell metric is not coarse-mesh/short-window limited (ties to B2).

All new runs should write the same FOs (U, T, wallHeatFlux, Gr/Ra/Ri/Re/Pr) and
run to pseudo-steady (gross wall duty stationary).

## 4. Can we estimate by hand instead? — YES (two independent routes)

Route A — **regress the recirculation metric vs Re/Ri and extrapolate to bf→0.**
Done this session on the 3 nominal points (linear bf vs Re):
- lower upcomer (TW7/TP4): backflow→0 at **Re≈240–260**
- upper upcomer (TP5/TW8): backflow→0 at **Re≈550–570** (more persistent cell)
- top (TP6): slope ≈0 → **not Re-controlled** (cooler/junction-pinned; won't shut
  off by raising loop Re).
TRUST: LOW. 3 points, Re and Ri co-vary (coupled loop), extrapolation is ~2–4×
beyond the data. Use as a TARGET for the CFD in §3, not a result. Adding the
existing perturbation points (§3) will tighten this a lot and decouple Re from Ri.

Route B — **classical mixed-convection flow-reversal criterion** (LitRev ch.14,
Jackson–Cotton–Axcell buoyancy criteria Eqs 3–4; buoyancy-aided vertical tube
reversal). Compute the literature buoyancy parameter (a Gr/Re^n group) at our
conditions and compare to its published reversal threshold to get a theory-based
Ri_crit independent of our CFD. This is a desk calculation from the salt
properties + leg ΔT + geometry; it should bracket Route A. NOT yet done — it is a
clean, fast next task (no CFD).

Agreement between Route A (data extrapolation) and Route B (literature criterion)
would be a defensible onset estimate even before the new CFD lands.

## 5. Parallel work map (independent lanes; claim on .agent/BOARD.md)

Compute is 1-core serial (reconstruction/sampling) — keep OF runs on ONE driver;
everything else parallelizes. Suggested lanes:

| Lane | Work | Needs OF compute? | Parallel with |
| --- | --- | --- | --- |
| **U1 Existing-perturbation extraction** | **BLOCKED** — the perturbation runs are false-steady (mdot pinned at nominal despite ±5-10% Q; thermal field not equilibrated). Must REQUALIFY first: see `.agent/journal/2026-06-30/perturbation-run-convergence-audit.md` + board `TODO-PERT-REQUAL`. Do NOT extract them into the correlation until requalified. | YES (after requal) | U2,U3,U4,U5 |
| **U2 Hand reversal criterion (Route B)** | DONE: Re_crit≈100–235, Ri_crit≈O(1); brackets Route A to ~factor 2. `2026-06-30_upcomer_reversal_criterion_hand_estimate.md` + `mixed_convection_reversal.py` | no | all |
| **U3 Downcomer closure** | DONE: f(Re)+Nu, no recirculation; recommend unblocking thermal. `2026-06-30_downcomer_closure_analysis.md` | reuses existing recon | U2,U4,U5 |
| **U4 Bend/junction minor-loss K** | NIST two-tap K extraction at corners using section-mean planes + straight-friction removal | reuses existing recon | U2,U3,U5 |
| **U5 Correlation fitting + figures** | Fit bf=F(Ri) onset form + Nu(Ra,Pr) cell scaling as U1 lands; paper-ready plots | no (consumes U1 output) | all |
| **U6 Mesh-independence (B2)** | medium/fine mesh gen + runs + GCI on Salt 3 Jin | YES (multi-node sbatch) | all |

Authoring lanes (U2,U3 setup,U4 setup,U5,U6 scripts) can be done by parallel
sub-agents NOW; the OF-compute lanes (U1, U6 execution) run on the single serial
driver. Recommended order: launch U1 reconstruction on the driver while agents do
U2 + U4-setup + U5-scaffold in parallel.

## 5b. Inclination is now a correlation variable (user question)

Closures did not previously carry leg INCLINATION; they should (buoyancy splits
into streamwise g·cosθ → reversal/cell, and transverse g·sinθ → stratification).
**HIGH-PRIORITY DISCREPANCY (unresolved):** the CFD data and the physical rig
DISAGREE on orientation. Rig (Ethan): heater & cooler legs at 20° from horizontal
(70° from gravity); all other legs vertical. CFD data (mesh+g, heater heat-flux-
identified): heater leg VERTICAL (∥ gravity), downcomer ~horizontal — i.e. heater
and downcomer orientations do NOT match the rig (cooler & upcomer roughly do).
The solver Gr/Ra/Ri are in the SIM frame, so if it mismatches the rig the
recirculation closures may not transfer. The inclination-based 'downcomer is
transverse' explanation is RETRACTED. Empirical recirculation (upcomer 15-33%,
downcomer ~0%) is frame-independent and stands. NEEDS Ethan/mesh audit of the CFD
gravity orientation. See `2026-06-30_upcomer_convection_cell_model.md` §6c.

## 6. Trust limits & provenance (be honest)

- **Mainline data**: salt2/3/4 Jin continuations under
  `jadyn_runs/.../2026-06-18_convergence_and_jin_envelope_wave/runs/` — stationary,
  verified, closure-grade for the CURRENT coarse mesh.
- **Perturbation data** (§3): exists but mixed convergence; each point must pass
  `assess_time_convergence.py` before entering the correlation. Provenance =
  the 2026-06-19 / 2026-06-25 waves; some are `failed_stage_preserved` (exclude).
- **Coarse mesh everywhere** → all f/Nu/UA'/recirc carry an unquantified
  discretization error until B2/U6. This is the single biggest "needs more data".
- **Upcomer correlation** is SEED-stage: 3 coupled points, Re∈[50,153], all
  in-cell. Onset (Re~250) and max are EXTRAPOLATED, not observed → new CFD (§3) or
  the existing perturbation points (U1) are REQUIRED to claim a correlation.
- **Characteristic Ri/Ra** use the solver's local-field definition; the Lc and
  reference ΔT must be page-audited before a published correlation (NEEDS-AUDIT).
- **Downcomer & fittings** unmodeled → currently in the lumped residual; the 1D
  model's residual fraction quantifies how much remains uncovered.
- **Property T-dependence**: Re/Nu use Jin µ(T)/k(T) at the (now-confirmed) bulk
  T; the Kirst variant is a separate sensitivity, not mainline.
