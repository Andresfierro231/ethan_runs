# Perturbation-Run Convergence Audit (Salt Jin hiq/loq/hi5q/lo5q/hiins/loins/optins)

Date: `2026-06-30` · Owner: claude (AGENT-156) · Type: convergence/provenance audit
Trigger: before using the existing perturbation runs to grow the upcomer
recirculation correlation (lane U1), verify they are at a NEW steady state
representative of their perturbed boundary conditions.

## TL;DR (honest)

The perturbation runs **pass a naive flat-monitor steadiness check but are NOT
trustworthy as distinct operating points.** Their loop mdot is pinned at the
NOMINAL value (~−0.0132 kg/s for Salt 2) despite real ±5–10% heater-power changes
— physically implausible at true steady state for a natural-circulation loop. The
thermal field has almost certainly NOT equilibrated to the perturbed BC (loop
thermal time constant ≫ the 2000–5000 s these advanced). **Do not treat them as
converged perturbed operating points without further runtime/verification.**

## Evidence

Simulated time (latest) and monitor steadiness for the 18 nominal Salt-Jin
perturbation runs (excludes `failed_stage_preserved`):

- ALL 18 report `assess_time_convergence.py` overall=stationary (hyd+thermal) —
  BUT that only means the dense monitor time series is flat over its trailing
  window. See the caveat below for why that is necessary-not-sufficient here.
- Simulated times range t≈2431–7955 s. Several BARELY ADVANCED past their restart:
  `salt2_jin_optins` t=2431, `salt2_jin_hiq_balq` t=2431, `salt3_jin_optins`
  t=2514 — i.e. ~0 s of advance past the nominal continuation restart → the
  perturbation had no time to take effect at all.
- `salt2_jin_hiq_balq`: NO mdot monitor written → did not run forward usefully.

BC actually changed (case_config Q), Salt 2:
- nominal 265.7 W; hiq_hiins 292.27 (+10%); loq_loins 239.13 (−10%);
  hi5q_balq 278.985 (+5%); lo5q_balq 252.415 (−5%).
- **`insulated.h` = 5.964 in ALL variants** → the hiins/loins INSULATION knob is
  NOT reflected in `insulated.h` (it may be applied to another patch group, or
  not at all). NEEDS VERIFICATION of where/whether insulation was perturbed.

Operating-point response (the red flag):
- Salt 2: every variant ends at mdot ≈ −0.0132 (nominal), last-20 range ~4e-6,
  i.e. flat — AT THE NOMINAL VALUE.
- Salt 4: hiq_hiins mdot −0.017110 vs loq_loins −0.017104 → a ±10% power swing
  moves mdot by ~0.04%. Laminar natural circulation expects mdot ∝ ~Q^(1/3) →
  ~±3% for ±10% Q. Observed ≈ 0.04% is ~70× too small.

## Interpretation

A flat monitor pinned at the nominal operating point after a real BC change means
the run RESTARTED from the nominal converged field and the slow thermal mode has
not re-equilibrated (mdot is buoyancy-driven through the bulk T field, whose
relaxation time is much longer than 2000–5000 s). The monitor "looks steady"
because it is still sitting near the old fixed point. **This is a false-steady:
steady-appearing but not at the perturbed steady state.**

Consequence for lane U1: extracting these as-is would populate the correlation
with points that are NOT distinct in Re (all ≈ nominal) and whose local thermal
state (wall–core ΔT, hence recirculation) may also be un-equilibrated. Using them
naively would FABRICATE apparent scatter / false repeatability.

## TODO (carry until resolved) — perturbation-run requalification

1. **Quantify advance-past-restart per run** (restart time = first monitor time of
   the perturbed segment; advance = latest − restart). Reject any run with advance
   below a thermal-relaxation threshold (estimate τ_thermal = ρ cp V_loop / (UA);
   compute it — likely several×10³ s, so most current runs are too short).
2. **Convergence criterion must be the OPERATING POINT, not just monitor flatness**:
   require mdot to have MOVED from nominal by the physically expected amount
   (~Q^(1/3) scaling) AND then re-plateaued. Add this as a gate in a new
   convergence mode (e.g. `--require-moved-from <baseline>`), or check by hand.
3. **Verify the insulation perturbation** actually changed a wall BC (hiins/loins):
   `insulated.h` is unchanged; find where insulation was meant to change, or
   conclude the knob was not applied.
4. **Re-run / continue** the genuinely interesting variants (the Q and insulation
   extremes) for long enough to reach the perturbed steady state — coordinate with
   Ethan/the run owner (these are jadyn_runs campaign assets; do not mutate). The
   incoming onset/limit CFD should bake in a thermal-relaxation-based end time.
5. Only AFTER (1)–(4): extract recirculation + characteristic Ri and add to the
   upcomer correlation (lane U1), flagging each point's convergence status.

## Provenance

Runs under `jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/runs/`
and `.../2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runs/`.
Convergence outputs: `tmp/2026-06-30_claude_action_items/pert_conv/<case>/`.
Method/caveat for the false-steady: `assess_time_convergence.py` checks monitor
stationarity, which is necessary but NOT sufficient when a run restarts near a
prior fixed point — documented here and to be hardened per TODO item 2.
