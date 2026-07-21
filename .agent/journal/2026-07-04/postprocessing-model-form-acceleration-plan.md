# Post-Processing and Model-Form Acceleration Plan

Date: `2026-07-04`
Role: Coordinator / Implementer / Writer
Task ID: `AGENT-175`

## Current run state observed

Scheduler state checked on `2026-07-04`:

- `3265969` `ethan_s34mid_ne5d`: cancelled on `2026-07-04T08:31:44`.
- `3265971` `ethan_s41lo2mid_ne5d`: cancelled on `2026-07-04T08:31:44`.
- `3265972` `ethan_s123hi_ne5d`: cancelled on `2026-07-04T08:31:44`.
- `3265970` `ethan_w1234_ne5d`: still running.
- `3275322` `NuclearEnergy-dev` interactive job: still running.

The stopped Salt jobs should be post-processed only enough to document their final
state and convergence failure. They should not feed friction/HTC/model-form fits
unless a future gate unexpectedly requalifies a case.

## First thing to do

Build a reproducible run-status and frozen-window inventory before launching
more extraction or model-form fitting. The inventory should answer:

- what run families exist;
- where the case directories are;
- what latest monitor time is available;
- whether the case is nominal, Q-perturbed, insulation-perturbed, Water, or mesh/GCI;
- whether it is stationary, quasi-stationary, false-steady, running, or blocked;
- whether it can be used for closure fitting, model-form scoring, meeting figures,
  or only provenance.

This is the dependency for all later work because it prevents false-steady Salt
perturbations from being silently promoted into a closure correlation.

## Parallel work map

### Lane A — run inventory and frozen-window gate

Owner: one coordinator/implementer.

Immediate work:

- Parse current Slurm outputs and case directories.
- Run `assess_time_convergence.py` logic on all live/recent packed slots.
- Emit `run_status_inventory.csv`, `run_status_inventory.json`, and a short
  markdown summary.
- Mark Salt perturbation slots as `false_steady` unless the operating-point gate
  passes.
- Leave Water as `running` until `3265970` exits, then rerun the same inventory.

This lane is login-node safe because it reads monitor files only.

### Lane B — Water completion post-processing

Owner: one implementer after `3265970` exits.

Ready to launch on Slurm after Water completes:

- Water frozen-window convergence report.
- Water pressure/friction extraction on the final retained window.
- Water thermal closure extraction if the retained fields and reconstruction
  contract are complete.

Do not start this before Water is done unless the goal is a provisional progress
screen; otherwise the frozen window will churn.

### Lane C — Salt nominal closure refresh

Owner: one extractor implementer.

Can run now if assigned and if it does not overlap active extractor owners:

- Rebuild the closure table for Salt 2/3/4 Jin nominal continuations using the
  corrected mesh-derived geometry.
- Include friction as `f(Re)` by leg, de-buoyed friction budget, bend/minor K,
  HTC/UA'/Nu, and recirculation metrics.
- Keep GCI/mesh error as an explicit trust limiter.

This is likely Slurm or dev-node work when it reconstructs fields or runs
OpenFOAM sampling.

### Lane D — model-form comparison matrix

Owner: one modeling implementer/writer.

Can start now from existing trusted Salt 2/3/4 nominal closure products:

- Build a model-form matrix where each row adds or swaps exactly one term.
- Score mdot, segment pressure drop, temperature/energy, residual closure, number
  of fitted parameters, and leave-one-case-out behavior where possible.
- Start with `f(Re)` only, then global multiplier, per-leg multiplier, per-leg
  power law, bend/minor K, diameter correction, thermal UA'/HTC forms, upcomer
  cell term, and boundary/radiation/insulation state.

This lane is mostly Python/modeling and can run on login/dev resources unless a
large external Fluid campaign is submitted.

### Lane E — new CFD design and submission

Owner: one CFD run coordinator.

Do not launch blindly. First use Lane A plus the existing T2/T13 notes to define
the matrix. Candidate future runs:

- true-steady Salt Q perturbations;
- real insulation variants for Salt 2/3/4;
- upcomer onset/limit cases;
- Water completion/repeats if Water remains useful;
- mesh/GCI support when a valid meshing path exists.

These are Slurm jobs and should have fresh staging, clear run manifests, and
postProcessing functions ready before submission.

## What can go to sbatch right away

Good immediate sbatch candidates, after scope is claimed:

- Field-based extraction for trusted nominal Salt continuation windows.
- Water post-processing once `3265970` completes.
- A larger model-form sweep if it uses many coupled 1D evaluations and needs a
  clean job log.

Not good immediate sbatch candidates:

- New Salt perturbation CFD before a run matrix and end-time/tau policy are
  written.
- Extraction of stopped false-steady Salt perturbations for closure fitting.
- Mesh/GCI production runs before the NCC/refinement blocker has a valid path.

## Implementation started in this task

AGENT-175 starts with Lane A: a reproducible status/frozen-window inventory
builder under `tools/analyze/`, plus generated work products for today's run
state. Later agents can consume that inventory instead of repeating one-off
manual checks.
