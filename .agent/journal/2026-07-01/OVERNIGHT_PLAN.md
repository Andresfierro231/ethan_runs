# Overnight autonomous plan — 2026-07-01 → 2026-07-02

Set up 2026-07-01 ~17:35 CDT. Owner: claude (autonomous). User is away; granted full
permission to make progress across /scratch/09748/andresfierro231/projects_scratch/**.
Meeting with advisor ~morning 2026-07-02. This doc is the self-prompt contract; each
scheduled wake re-reads it and advances the current phase.

## Guardrails (HARD — do not violate)
- Work only inside projects_scratch (ethan_runs, cfd-modeling-tools). Stage CLONES for
  any mesh/case mutation; NEVER mutate read-only sources (jadyn_runs/** continuation
  trees, /scratch/09807/ethanrozak/**).
- Do NOT kill or pause T2 (my insulation runs, PIDs under idev 3269598) or codex's
  production jobs (3265969-72 on other nodes). T2 is too slow to finish (see §Findings)
  but is the user's study — leave it; use the ~128 FREE cores on c318-008 instead.
- No destructive/irreversible actions (rm of tracked data, force-push, external sends).
- Prefer REUSABLE scripts + documented workflows over one-off analysis. Rigor > speed.
- Document EVERY step in dated journals; be explicit about caveats/assumptions/uncertainty
  and always add "next steps to bolster credibility."
- If a step is genuinely risky/ambiguous, document the decision and choose the
  conservative path; leave a clear note for the user rather than guessing on irreversibles.

## Findings that reshape the night
- **T2 insulation runs are far too slow**: 7915→8072 sim-s in ~7h (~22 s/hr) vs endTime
  33000 → ~1000+ h needed. They will NOT reach steady overnight or this week as configured
  (deltaT too small / throughput too low). Document; the upcomer correlation (T10) stays
  blocked on this regardless. Do NOT kill T2, but do NOT wait on it. Flag for the user:
  the insulation study needs a bigger timestep / different acceleration or a rethink.
- Per-leg friction multiplier IMPLEMENTED in the 1D model this session (backward-compatible).
  Per-leg predictivity comparison running now (perleg_run.log).

## PHASE 1 — compute + analysis (now → ~04:30 CDT)
Priorities (highest value first; all documented + reusable scripts):
1. **Per-leg friction predictivity** (cheap, presentation-central): finish
   run_perleg_friction_compare.py; add a per-segment ΔP comparison showing per-leg
   friction collapses the +96-400% per-segment errors the global multiplier caused.
   -> figures + table + journal.
2. **Mesh self-generation DE-RISK** (the #1 trust limiter, T6): on a CLONE of
   recon_salt2_of13, run refineMesh -all (r=2) → createNonConformalCouples → checkMesh →
   tiny-endTime OF13 solver dry-run (prove it STARTS, no segfault). This is the key
   unknown. Document cell counts, checkMesh quality, and whether NCC regeneration works.
3. **IF de-risk validates**: launch a bounded coarse+fine GCI run on the FREE cores
   (do not evict T2); extract mdot/f(de-buoyed)/Nu/y+ per level; 2-level Richardson/GCI
   (assumed order, labeled honestly). If it will not finish by ~04:30, checkpoint and
   report partial + the exact resume command.
4. **1D driver-side investigation** (cheap): the trial found the model runs Re 2-3x CFD
   at matched loss (buoyancy/ΔT driver over-predicts). Sweep the 1D model's ambient/
   insulation/property knobs vs CFD ΔT & duty to localize the driver error. Reusable script.
5. Keep a running RESULTS LOG (work_products/2026-07-02_overnight/RESULTS_LOG.md) with
   every run, its inputs, outputs, and caveats.

## PHASE 2 — report + figures + documentation (~05:00 CDT)
- Assemble a comprehensive internal report from all overnight results: extend
  reports/2026-07/2026-07-01/2026-07-01_model_form_comparison/ and write a new
  reports/2026-07/2026-07-02/ overnight-synthesis report.
- Regenerate/curate figures (reusable make_figures scripts). Update the presentation
  package (work_products/2026-07-01_claude_checkpoint_presentation/).
- Thorough journals for each Phase-1 workstream. Every quantitative claim cites its artifact.

## PHASE 3 — presentation key items (~07:00 CDT)
- Distill the 3-5 highest-value, MOST DEFENSIBLE things to present, each with its caveat
  and a next-step to strengthen it. Update the deck outline + facts/Q&A sheet.
- Produce a crisp "what's solid / what's provisional / what's blocked / next steps" one-pager.
- Anticipate the advisor's hard questions (cells count, mesh independence, convergence,
  friction derivation, predictivity) with honest, sourced answers.

## Scheduling
- Self-paced via ScheduleWakeup; wake ~hourly (or on background-task completion) to advance.
- At each wake: `date` → determine phase → do the next bounded unit → document → re-arm.
- Transition to Phase 2 at/after 05:00 CDT, Phase 3 at/after 07:00 CDT.

## Status ledger (update each wake)
- [17:35] Plan written; per-leg comparison running; T2-too-slow documented.
- [18:29] Wake 1 (Phase 1): per-leg friction predictivity DONE (doc+fig4); viscosity
  diagnosis (1D salt_current ~25% > Jin; NOT the Re-2.3x cause -> thermal driver);
  driver_thermal_compare.py launched (bg); mesh de-risk AGENT-169 progressing (refineMesh
  +NCC+checkMesh+mapFields ran). Re-armed ~45min.
- [18:50] Wake 2 (agent-triggered): MESH de-risk (AGENT-171) done — refineMesh+NCC works
  geometrically (17.34M cells) but refined NCC interface BREAKS fvMeshStitcher at runtime;
  no GCI; fix=conformal-first/snappy. DRIVER finding: 1D loop ~60K hotter than CFD (512 vs
  450K) -> explains Re 2.3x, driver is THERMAL not closures. Both documented + logged.
  19:21 wake pending.
- [19:21] Wake 3 (Phase 1): scenario-BC matching. 1D heater power matches CFD (265.7W);
  launched insulation_sweep.py to test if an insulation setting reproduces CFD T~450K
  (would attribute the 60K to setup not model). Re-armed ~45min.
- [20:08] Wake 4 (Phase 1): MAJOR CORRECTION — insulation sweep shows the 60K over-heat
  is mostly a BC mismatch (CFD 450K bracketed 0-1in); matched-T Re gap 2.3x->1.5x. Prior
  predictivity numbers were at an uncontrolled (60K-hot) thermal condition -> must redo
  closure comparison at CFD-matched insulation. Fine sweep launched to pin it. Re-armed.
- [20:56] Wake 5 (Phase 1): fine sweep pins CFD-matched insulation ~0.27in. At matched T
  the 1D UNDER-predicts mdot (-25%), so closure benefit on mdot is CONDITION-DEPENDENT
  (helps when hot/over, hurts when matched/under) -> pressure DISTRIBUTION is the robust
  closure metric, not mdot. matched_closure_compare.py running. Re-armed.
- [21:47] Wake 6 (Phase 1): predictivity thread FULLY diagnosed. Matched-insulation closure
  compare (default -27% -> per-leg -49% at CFD-matched T); "drive too weak" DISPROVEN (ΔT
  matches 12.1K, head not smaller); factor-2 mdot gap = OPEN momentum-balance discrepancy;
  f/f_lam is Re-dependent (partial contributor). Culminating journal written. Model-form
  report updated with §6 overnight corrections. Predictivity thread DONE; next wakes shift to
  consolidation (per-segment ΔP fig, presentation) + Phase 2 report at 05:00. Re-armed.
- [22:34] Wake 7: overnight figures done (figA insulation-sensitivity, figB condition-
  dependent closure). Next: Phase 2 overnight-synthesis report skeleton + presentation update.
- [23:21] Wake 8 (Phase 2 early): comprehensive overnight-synthesis report written
  (reports/2026-07/2026-07-02/2026-07-02_overnight_synthesis/). Next: presentation update.
- [00:08] Wake 9 (Phase 2): presentation package updated with corrected predictivity story
  (facts_and_qa + outline C-E); figA/figB/fig4 copied in. Major deliverables (report+figs+
  presentation) DONE. Next: Phase 3 one-pager + hard-Q answers (can start ahead of 07:00).
- [00:56] Wake 10 (Phase 3 early): PRESENTATION_KEY_ITEMS.md + MORNING_BRIEF.md written;
  9 figures verified; package self-consistent. ALL MAJOR DELIVERABLES COMPLETE ahead of
  07:00. Winding to longer cadence (3600s) for a final morning readiness pass; no
  substantive work left (mesh blocked, T2 slow, analysis done).
- [01:59] Wake 11 (light readiness): state UNCHANGED — T2 still crawling (8306, ~47s/hr, will
  not finish); jobs healthy; no new background results. Deliverables complete + consistent;
  no churn per instruction. Re-armed long (~3600s).