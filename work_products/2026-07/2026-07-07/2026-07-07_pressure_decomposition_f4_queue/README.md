# Pressure Decomposition / F4 Queue Handoff

Date: `2026-07-07`  
Task: `AGENT-184`  
Role: Coordinator / Writer  
Owner: codex

## Objective

Define a practical attack plan for continuing the pressure decomposition and F4
buoyancy-modified friction queue, using the same startup and evidence context
that Claude is expected to read.

## Coordination State

Task ID: `AGENT-184`

Allowed edit paths for this planning task:

- `.agent/BOARD.md` own row only
- `.agent/status/2026-07-07_AGENT-184.md`
- `work_products/2026-07-07_pressure_decomposition_f4_queue/**`

Read-only paths for this planning task:

- `AGENTS.md`, `.agent/FILE_OWNERSHIP.md`, `.agent/ROLES.md`
- `CLAUDE.md`, `.agent/DECISIONS.md`
- recent `.agent/journal/**` and `operational_notes/**`
- existing `work_products/**`
- active corrected Salt solver trees under
  `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/**`
- external Fluid code under `../cfd-modeling-tools/**`

## Inputs / Provenance Inspected

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `.agent/DECISIONS.md`
- `CLAUDE.md`
- `.agent/journal/README.md`
- `operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md`
- `operational_notes/06-26/30/2026-06-30_mesh_geometry_vs_probe_csv_provenance.md`
- `operational_notes/06-26/30/2026-06-30_cfd_1d_closure_workflow.md`
- `operational_notes/07-26/04/2026-07-04_monday_todo_pressure_decomposition.md`
- `operational_notes/07-26/07/2026-07-07_coordinator_status_and_task_queue.md`
- `.agent/status/2026-07-04_AGENT-179.md`
- `.agent/status/2026-07-07_AGENT-181.md`
- `.agent/journal/2026-07-04/coordinator-implementer-pressure-drop-decomposition.md`
- `.agent/journal/2026-07-04/coordinator-monday-handoff-and-claude-bootstrap.md`
- `.agent/journal/2026-07-07/implementer-jin-gap-api-fix-and-salt-preliminary-gate.md`
- `.agent/journal/2026-07-01/T1b-momentum-budget-debuoyed-friction.md`
- `.agent/journal/2026-07-02/per-leg-friction-implementation-and-predictivity.md`
- `.agent/journal/2026-07-02/driver-side-thermal-overheat-finding.md`
- `work_products/2026-07-01_claude_momentum_budget/momentum_budget.csv`
- `work_products/2026-07-01_claude_momentum_budget/momentum_budget.json`
- `work_products/2026-07-01_claude_segment_friction/segment_friction.csv`
- `work_products/2026-07-04_friction_forms/friction_forms_comparison.csv`
- `work_products/2026-07-04_friction_forms/run_friction_forms_compare.py`
- `work_products/2026-07-04_consolidated_closure_and_model_jobs/next_1d_model_forms/README.md`
- `work_products/2026-07-04_consolidated_closure_and_model_jobs/next_1d_model_forms/per_leg_re_power_law_screen.csv`
- `work_products/2026-07-06_overnight_postprocess_jobs/water_postprocess_after_3265970/next_1d_model_forms/README.md`
- `work_products/2026-07-07_corrected_salt_preliminary_gate/README.md`
- `work_products/2026-07-07_corrected_salt_preliminary_gate/preliminary_gate_analysis.json`
- `work_products/2026-07-04_jin_perleg_gap_analysis/slurm-jin_perleg_gap-3275531.out`
- `work_products/2026-07-04_jin_perleg_gap_analysis/slurm-jin_perleg_gap-3275531.err`

## Planned Outputs

For the next implementation task, keep outputs in a new dated directory, for
example:

- `work_products/2026-07-08_f4_buoyancy_friction_fit/f4_calibration_dataset.csv`
- `work_products/2026-07-08_f4_buoyancy_friction_fit/f4_fit_summary.json`
- `work_products/2026-07-08_f4_buoyancy_friction_fit/f4_fit_readme.md`
- optionally, a tool under an explicitly claimed path such as
  `tools/analyze/build_f4_buoyancy_friction_fit.py`

Do not edit `../cfd-modeling-tools/**` until a separate board row explicitly
claims the Fluid solver paths.

## Acceptance Criteria

The F4 work should be accepted only if it:

- uses the de-buoyed momentum-budget target, not raw signed apparent-friction
  rows with pressure-recovery flags;
- computes or imports a documented Richardson-number definition, preferably
  median section Ri with streamwise projection where relevant;
- keeps `buoyancy_pressure()` as the separate buoyancy-head term and implements
  F4 only as a shear/resistance correction;
- compares F4 against F1, F3 Hagenbach, and existing F5 per-leg CFD multipliers;
- reports fit residuals by physical leg class: heater, cooler, downcomer,
  upcomer, test section;
- marks Salt 1 and any corrected Salt Q row with
  `needs_special_gate_scrutiny=True` as hold-for-coordinator-review;
- refuses closure-fit admission for corrected Salt Q rows unless the formal gate
  reports `operating_point_verdict=requalified` and no special-scrutiny flag is
  unresolved;
- documents limitations: coarse mesh/no GCI, driver-side thermal mismatch,
  pending gap-analysis follow-through, and small current sample size.

## Raw Observations

- `CLAUDE.md` says Claude should read `AGENTS.md`, `.agent/BOARD.md`,
  `.agent/FILE_OWNERSHIP.md`, `.agent/ROLES.md`, the master TODO, the mesh
  geometry/probe provenance note, the CFD-to-1D workflow, and `.agent/DECISIONS.md`.
- AGENT-179 implemented F1 and F3 Hagenbach in the external Fluid repo and left
  F4 buoyancy-modified friction as the next closure.
- The July 4 pressure roadmap says buoyancy is already handled separately in
  `buoyancy_pressure()` and should not be added again inside the friction loop.
- `momentum_budget.csv/json` provide de-buoyed friction targets. Salt 2/3/4
  heater, cooler, and downcomer are roughly `2-3x` laminar after the buoyancy
  decomposition.
- `friction_forms_comparison.csv` shows F3 Hagenbach explains much of the short
  upcomer excess but leaves a large residual in heater/cooler/downcomer.
- `segment_friction.csv` includes signed apparent-friction rows with
  pressure-recovery flags; those are useful diagnostics but are not the F4 fit
  target.
- The July 4 gap job `3275531` failed with `ModuleNotFoundError:
  No module named 'tamu_loop_model_v2'`; later AGENT-182 work fixed a separate
  copied-script API bug, so the per-leg gap rerun is pending follow-through
  rather than available calibration evidence here.
- Corrected Salt Q runs are moving in the right direction, but formal gate output
  remains the admission boundary. Early/flagged rows must carry
  `needs_special_gate_scrutiny` forward.
- The 1D driver-side thermal comparison found the model running about `60 K`
  hotter than CFD in one scenario, so friction improvements alone should not be
  expected to fix mass-flow predictivity.

## Interpretation

The cleanest F4 target is not "make mdot match." The target is a physically
separate resistance multiplier or correction that explains the remaining
de-buoyed `f_corrected/f_lam` gap after F1/F3, especially in heater, cooler, and
downcomer spans.

The first F4 implementation should be data-building and comparison-first:
assemble the admitted rows, compute the exact Ri convention, fit a simple bounded
candidate, and only then wire it into Fluid. This avoids double-counting buoyancy
and avoids training on still-running perturbations.

## Attack Plan

1. **Freeze the admission set.** Start with mainline Salt 2/3/4 Jin only. Add
   corrected Salt Q rows later only after the formal gate says
   `operating_point_verdict=requalified`, and hold any
   `needs_special_gate_scrutiny=True` row for coordinator review.
2. **Build the F4 calibration table.** Join `momentum_budget.json`,
   `friction_forms_comparison.csv`, segment geometry, and Ri/Ra/Re data. Fields
   should include case, span, physical leg class, Re, D, L, x_plus, f_lam,
   f_corrected, F3h ratio, residual `f_corrected/f_F3h`, Ri definition, and
   admission flags.
3. **Audit Ri before fitting.** Use median section Ri, not the mean, and project
   by streamwise gravity where the leg is inclined. Record the exact formula and
   source of `deltaT`, property basis, and length scale.
4. **Fit minimum viable F4.** Start with a transparent form such as
   `f_F4 = f_F3h * (1 + C_leg * max(Ri_streamwise, 0)^n)` or a shared `C,n`
   with leg-class offsets. Keep the fit bounded and leg-class aware.
5. **Compare, do not declare victory.** Report F1, F3h, candidate F4, and F5
   per-leg CFD multiplier side by side on pressure distribution and mdot. Make
   clear whether F4 improves local pressure terms even if mdot remains limited
   by thermal-driver mismatch.
6. **Only then wire the solver.** In a new Implementer task, add
   `F4_buoyancy` to `friction_closures.py` and expose the Ri inputs through
   `solver.py`. Keep default `friction_form="F1"` unchanged.

## Claude Collaboration Split

Claude can work effectively in parallel if the ownership is split cleanly:

- **Claude lane A: literature/form inventory.** Read the lit-review forms and
  propose candidate F4/F6 functions, validity ranges, required dimensionless
  groups, and whether each form modifies friction, Nu, or both. Output a
  markdown/CSV inventory only.
- **Codex lane B: evidence/admission table.** Build the reproducible calibration
  table and enforce the gate/special-scrutiny policy. This lane should own the
  machine-readable admission flags.
- **Claude lane C: solver prototype, after B lands.** Implement candidate forms
  in external Fluid only after a board row grants `../cfd-modeling-tools/**`
  edit paths, then run the Fluid unit tests.
- **Codex lane D: reviewer/gate.** Review that the implementation does not
  double-count buoyancy, does not ingest held rows, and preserves F1/F3/F5
  comparability.

Avoid having both agents edit `friction_closures.py`, `solver.py`, or the same
work-product directory at the same time.

## Commands Run

```bash
pwd
sed -n '1,220p' AGENTS.md
sed -n '1,260p' .agent/BOARD.md
sed -n '1,260p' .agent/FILE_OWNERSHIP.md
sed -n '1,240p' .agent/ROLES.md
sed -n '1,260p' CLAUDE.md
rg -n "F4|buoyancy-modified|buoyancy modified|pressure decomposition|pressure-drop decomposition|pressure drop decomposition|friction_form|friction closure|decomposition" .agent journals operational_notes reports work_products tools -g '*.md' -g '*.py' -g '*.json' -g '*.csv'
find work_products -name AGENTS.override.md -o -name README.md -o -name TODO.md
find .agent -maxdepth 3 -type f \( -name '*179*' -o -name '*181*' -o -name '*182*' -o -name '*pressure*' -o -name '*friction*' -o -name '*salt*gate*' \) | sort
rg -n "AGENT-183|Pressure decomposition / F4 queue|Unclaimed|Queue|Backlog|AGENT-179|AGENT-181|AGENT-182" .agent/BOARD.md
sed -n '1,240p' operational_notes/07-26/04/2026-07-04_monday_todo_pressure_decomposition.md
sed -n '1,220p' operational_notes/07-26/07/2026-07-07_coordinator_status_and_task_queue.md
sed -n '1,260p' operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md
sed -n '1,220p' .agent/DECISIONS.md
sed -n '90,150p' .agent/BOARD.md
sed -n '1,220p' .agent/status/2026-07-04_AGENT-179.md
sed -n '1,220p' .agent/journal/2026-07-04/coordinator-implementer-pressure-drop-decomposition.md
sed -n '1,180p' .agent/journal/2026-07-04/coordinator-monday-handoff-and-claude-bootstrap.md
sed -n '1,220p' .agent/journal/2026-07-07/implementer-jin-gap-api-fix-and-salt-preliminary-gate.md
sed -n '1,200p' .agent/status/2026-07-07_AGENT-181.md
sed -n '1,220p' work_products/2026-07-07_corrected_salt_preliminary_gate/README.md
sed -n '1,220p' work_products/2026-07-04_consolidated_closure_and_model_jobs/next_1d_model_forms/README.md
sed -n '1,220p' work_products/2026-07-06_overnight_postprocess_jobs/water_postprocess_after_3265970/next_1d_model_forms/README.md
sed -n '1,180p' operational_notes/06-26/30/2026-06-30_mesh_geometry_vs_probe_csv_provenance.md
find work_products/2026-07-04_friction_forms work_products/2026-07-01_claude_momentum_budget work_products/2026-07-01_claude_segment_friction work_products/2026-07-04_jin_perleg_gap_analysis work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap -maxdepth 2 -type f | sort
head -40 work_products/2026-07-04_friction_forms/friction_forms_comparison.csv
head -40 work_products/2026-07-01_claude_segment_friction/segment_friction.csv
head -80 work_products/2026-07-04_consolidated_closure_and_model_jobs/next_1d_model_forms/per_leg_re_power_law_screen.csv
sed -n '1,260p' work_products/2026-07-04_friction_forms/run_friction_forms_compare.py
head -80 work_products/2026-07-01_claude_momentum_budget/momentum_budget.csv
sed -n '1,220p' operational_notes/06-26/30/2026-06-30_cfd_1d_closure_workflow.md
sed -n '1,180p' .agent/journal/2026-07-01/T1b-momentum-budget-debuoyed-friction.md
sed -n '1,180p' .agent/journal/2026-07-02/per-leg-friction-implementation-and-predictivity.md
sed -n '1,160p' .agent/journal/2026-07-02/driver-side-thermal-overheat-finding.md
sed -n '1,220p' .agent/journal/README.md
sed -n '1,220p' work_products/2026-07-07_corrected_salt_preliminary_gate/preliminary_gate_analysis.json
tail -80 work_products/2026-07-04_jin_perleg_gap_analysis/slurm-jin_perleg_gap-3275531.out
tail -80 work_products/2026-07-04_jin_perleg_gap_analysis/slurm-jin_perleg_gap-3275531.err
mkdir -p work_products/2026-07-07_pressure_decomposition_f4_queue
```

One broad `find` for local instruction files was interrupted after it began
scanning large campaign trees.

## Files Changed / Generated

- `.agent/BOARD.md`
- `.agent/status/2026-07-07_AGENT-184.md`
- `work_products/2026-07-07_pressure_decomposition_f4_queue/README.md`

## Blockers

- No formal corrected-Salt gate output is available yet for closure admission.
- The July 4 Jin per-leg gap job failed before producing results; the rerun
  follow-through is outside this planning task.
- No mesh-independence/GCI bounds exist for the current friction/thermal closure
  evidence.
- The external Fluid solver paths are read-only for this task.

## Exact Next Action

Open an Implementer task for `work_products/2026-07-08_f4_buoyancy_friction_fit/**`
and, if needed, `tools/analyze/build_f4_buoyancy_friction_fit.py`; then build the
read-only F4 calibration table from mainline Salt 2/3/4 Jin plus explicit
admission/special-scrutiny columns.
