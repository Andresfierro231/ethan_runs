---
date: 2026-07-14
task: AGENT-368
tags:
  - hydraulics
  - forward-v1
  - overnight
  - handoff
status: complete
---
# Tomorrow Hydraulics And Overnight Compute Handoff

## Current Snapshot

Workspace:

```bash
cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
```

Observed compute context on 2026-07-14 evening:

- Current node: `c318-008.ls6.tacc.utexas.edu`.
- Running jobs:
  - `3293924` `saltq_sel_cont`, running on `c318-016`.
  - `3295120` `idv75667`, running on `c318-008`.
- Pending/held jobs:
  - `3295968` `upc_pm5q`, pending priority.
  - `3295438` `saltq_s24_sel_harv`, dependency-held.

Do not duplicate these jobs without a new board row and a concrete reason.

## What Landed Today

Hydraulics progressed from proxy evidence to an executable-but-still-gated
closure path:

- AGENT-338 produced the reset/K admission contract.
  - H1 remains proxy-only.
  - Reset/development requires a first-class Fluid term.
  - Component/cluster K has `0` fit-admissible rows.
  - F6 remains blocked until admitted Re-variation evidence exists.
- AGENT-349 implemented HYD-TAP.
  - `12` preserved corner rows now use existing mesh-centerline endpoint lengths
    instead of the old `abs(dz)` tap-length proxy.
  - `3` `test_section_complex` connector rows still require raw two-tap
    extraction or explicit endpoint mapping.
  - Component/cluster K still has `0` fit-admissible rows after the refresh.
- AGENT-361 implemented HYD-RESET-API in external Fluid.
  - Added `MinorLosses.reset_development_k_by_segment`.
  - Added `MinorLosses.reset_development_k_for_segment(segment)`.
  - Parsed `reset_development_k_by_segment` from Fluid `campaigns.yaml`
    minor-loss presets.
  - Charged reset/development K separately from localized fixed K in
    `distributed_and_minor_losses`.
  - Focused Fluid contract tests passed.
- AGENT-362 integrated the +/-5Q corrected-Q admission/split state with the
  hydraulic tap refresh.
  - There are `4` terminal-harvested +/-5Q rows.
  - There are `0` independent training expansion rows.
  - Forward-v1 remains blocked pending matched pressure/upcomer metrics,
    perturbation split policy, F6/onset gate, and BC/HX setup-only score targets.

## Non-Negotiable Guardrails

- Do not mutate native CFD solver outputs.
- Treat repaired/smoke outputs as diagnostic until an admission gate admits them.
- Do not use thermal fitting to repair hydraulic mdot.
- Do not use one global friction/K multiplier to hide missing named losses.
- Do not fit universal `f` or `K` on recirculation-invalid rows.
- Do not re-open stale blockers:
  - OF13 reconstruction works.
  - Mesh families exist.
  - CFD `rcExternalTemperature` includes radiation.

## Current Blockers

Hydraulics:

- `component_cluster_K_admission`: still blocked because current rows are
  coarse/no-GCI, missing raw connector evidence, or recirculation diagnostics.
- `reset_development_admission`: API exists, but pressure evidence is not
  admitted as a faithful reset/development term.
- `H1_faithful_launch`: blocked because local K and reset/development terms are
  not admitted.
- `F6_phi_re`: still blocked until admitted Re-variation/matched pressure rows
  exist and pass pressure-loss validation.

Forward/CFD:

- `3293924` must reach terminal before selected +/-10Q corrected-Q rows can be
  harvested/admitted.
- `3295438` is dependency-held and should process selected Salt2/Salt4 +/-10Q
  after `3293924`.
- `3295968` `upc_pm5q` is pending and should not be duplicated.
- Matched pressure/upcomer metrics remain pending for F6/onset decisions.

Thermal/Boundary:

- Predictive thermal/HX/wall setup remains a major forward-v1 blocker.
- Current heat-loss parity and presentation packages are useful, but do not
  admit predictive HX/wall submodels by themselves.

## Recommended Pickup Order Tomorrow

1. Check scheduler state first:

```bash
squeue -u andresfierro231
sacct -j 3293924 --format=JobID,JobName,State,ExitCode,Elapsed
sacct -j 3295968 --format=JobID,JobName,State,ExitCode,Elapsed
sacct -j 3295438 --format=JobID,JobName,State,ExitCode,Elapsed
```

2. If `3293924` is terminal, harvest selected +/-10Q corrected rows and let or
   inspect dependency job `3295438`. Keep split discipline: do not silently
   promote perturbations as independent training rows.
3. If `3295968` finished, harvest matched pressure/upcomer metrics and update
   the F6/onset gate.
4. Run the next hydraulics gate package:
   - consume AGENT-349 tap refresh;
   - consume AGENT-361 Fluid reset API status;
   - consume any new matched pressure/upcomer metrics;
   - output either `blocked_no_go` or a bounded F6/H1 screen plan.
5. Only after admitted pressure evidence exists, run F6 pressure validation.
   mdot is a secondary guardrail, not the primary fit target.

## Overnight Study Recommendations

Best immediate overnight posture: **monitor/harvest existing jobs, do not launch
duplicates**. The queue already has active/pending work that directly unblocks
hydraulics and forward-v1.

Recommended if an explicit new launch is authorized:

1. **Corrected-Q terminal watcher/harvester**
   - Trigger: `3293924` exits.
   - Purpose: terminal harvest/admission for selected +/-10Q corrected rows.
   - Output: updated corrected-Q admission/split package.
   - Risk: low if it reads outputs and writes derived work products only.

2. **Matched pressure/upcomer harvest**
   - Trigger: `3295968` exits.
   - Purpose: parse matched pressure/upcomer metrics for Salt2/Salt4 +/-5Q.
   - Output: matched pressure/upcomer metric table for F6/onset gate.
   - Risk: low; do not submit a duplicate while `3295968` is pending.

3. **Raw two-tap connector extraction plan/smoke**
   - Trigger: node availability and a new board row.
   - Purpose: replace the three blocked `test_section_complex` rows with actual
     two-tap endpoint evidence.
   - Constraint: write derived outputs to a dated work product; do not mutate
     native CFD solver outputs.
   - Risk: medium because OpenFOAM postprocessing can accidentally write into
     case `postProcessing`; use a staged or explicitly claimed output path.

4. **F6 ready-to-run gate package**
   - Trigger: can run anytime as a lightweight repo-local analysis.
   - Purpose: prepare F6 acceptance rules and block until admitted Re-variation
     evidence exists.
   - Risk: low; no solver outputs or external Fluid edits needed.

5. **Diagnostic Fluid reset-K sweep**
   - Trigger: after AGENT-361 external edits are available.
   - Purpose: verify the new reset-development API is numerically active and
     separately reported in small controlled scenarios.
   - Constraint: diagnostic only; do not claim H1 admitted from this.
   - Risk: low-to-medium; keep as 1D-only and avoid thermal fitting.

## Exact Files To Open Tomorrow

- `work_products/2026-07/2026-07-14/2026-07-14_hydraulic_reset_k_admission_contract/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_fluid_reset_development_api/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_forward_v1_pm5_hydraulic_delta/README.md`
- `.agent/BLOCKERS.md`
- `.agent/BOARD.md`

## Bottom Line

We made real progress: the H1 proxy has been decomposed into concrete admission
gates, tap-length evidence was improved, and Fluid now has a separate
reset/development API hook. But the honest scientific state is still blocked:
no component/cluster K rows are fit-admissible, reset/development terms are not
pressure-admitted, and F6 still needs admitted Re-variation/matched pressure
evidence.

Tomorrow should focus on harvesting terminal/pending CFD-derived metrics and
then running a gate, not on launching another proxy H1 score.
