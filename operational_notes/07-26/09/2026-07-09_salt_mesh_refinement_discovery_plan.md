# Salt Mesh Refinement Discovery And Incorporation Plan

Date: `2026-07-09`
Task: `AGENT-226`
Role: `Coordinator / Writer`

## Observed Source Drop

Ethan's Salt mesh-family source is readable at:

`/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs/salt/`

It contains `coarse/`, `medium/`, and `fine/` levels. `fine` is the highly
refined level. Each level has all Salt tests `1-4` and both `jin`/`kirst`
property variants, for `24` total case directories.

The structure is clean enough for a staged intake, but this first pass did not
stage, register, or postprocess anything.

## What We Did With Earlier Runs

Earlier Salt closure work followed a useful pattern:

- create explicit task scope on `.agent/BOARD.md`;
- keep source paths in manifests and work products rather than relying on
  symlinks;
- separate mainline Jin continuations from historical Kirst and perturbation
  runs;
- build derived products under dated `work_products/` or `reports/` packages;
- feed later model work through a shared `closure_observations.csv` contract
  rather than one-off fitting CSVs.

The strongest reusable products are the July 8 closure-observation contract and
the pressure/thermal ledgers feeding it. The biggest weak point was that all
current closure coefficients still lacked mesh/GCI uncertainty.

## What Worked Well

- The admission vocabulary is already in place: `mesh_level`, `mesh_status`,
  `source_case_root`, `fit_eligible`, `validation_eligible`, and
  `admission_status`.
- Prior notes already define the minimum mesh/GCI scope: Salt 2 Jin and Salt 4
  Jin endpoints first, with mdot, wall duty, f, Nu, UA', y+, pressure terms, and
  feature K as QoIs.
- The new source tree has all three levels for all cases, which is better than
  the minimum requested endpoint-only mesh plan.

## What Did Not Work Well

- Some older products mixed warmup-era coarse sources with later continuation
  evidence. Any new mesh comparison must explicitly reconcile the external
  `coarse/` source against the repo's current mainline continuation roots.
- Kirst runs were historically tempting to use as extra data. Current repo rules
  say not to use Kirst as default current evidence.
- Most medium/fine logs inspected here end with signal 15, likely walltime
  termination. That is not a numerical crash by itself, but it means convergence
  must be proven before admission.
- The prior mesh/GCI task was blocked by unreadable directories. That is now
  unblocked for discovery, but not yet converted into admitted analysis data.

## File-Structure Rules For Future Work

Use this layout to avoid mess:

- Keep source folders read-only at Ethan's path.
- Create a staged intake package only after a new board row claims it:
  `staging/modern_runs/YYYY-MM-DD_salt_mesh_refinement/`.
- Keep generated inventories and GCI products under:
  `work_products/2026-07/2026-07-DD/YYYY-MM-DD_salt_mesh_gci_<scope>/`.
- If a source is registered, use source ids that encode case, property variant,
  mesh level, and whether it is external source or continuation, for example:
  `salt2_jin_medium_mesh_external_20260707`.
- Never call a row simply `salt2_jin` once mesh levels enter the table.
  Include at least `mesh_level`, `source_case_root`, `source_path`, `time_window`,
  and `admission_status`.

## Provenance Labels

Recommended labels:

- `mesh_level`: `coarse`, `medium`, `fine`.
- `mesh_status`: `coarse_no_gci`, `mesh_family_candidate`,
  `mesh_gci_ready`, `mesh_gci_failed`, `mesh_level_unconverged`.
- `run_class`: `nominal_mesh_refinement`, not perturbation or baseline.
- `independence_group_id`: one group per physical operating point and property
  variant, e.g. `salt2_jin_mesh_family`.
- `fit_use_status`: `held_for_mesh_uq` until the GCI package decides whether the
  row updates a central value or only an uncertainty band.

## Incorporation Plan

1. Intake and staging row:
   create a manifest that records all 24 exact source paths, mtimes, cell counts,
   mesh settings, processor layout, and source ownership. Stage only the minimum
   needed for analysis, not a blind copy of every large field tree.
2. Reconcile coarse:
   decide whether GCI uses Ethan's external `coarse/` roots or the repo's current
   continuation roots. If they differ materially, do not mix them silently.
3. Quality gate:
   run lightweight log/postProcessing checks per case: terminal state,
   convergenceMonitor status, latest time, mdot drift, heat-duty drift, y+
   availability, and required field presence.
4. First GCI target:
   process Salt 2 Jin coarse/medium/fine first. It is the only medium/fine Jin
   endpoint where both medium and fine tails showed clean convergence in this
   discovery pass.
5. Upper endpoint:
   evaluate Salt 4 Jin next. If medium/fine are not quasi-steady, continue or
   label failed/partial; do not fabricate a three-level GCI.
6. Closure observation refresh:
   propagate mesh uncertainty into the July 8 closure-observation contract only
   after GCI readiness is established. Mesh rows should qualify existing
   observations, not create a parallel untracked fit target table.
7. Closure-correlation retry:
   refit pressure/thermal/minor-loss correlations only after the observation
   table carries mesh uncertainty and each row has an explicit fit/validation
   status.

## Immediate Next Board Row

Recommended next task: `Coordinator / Implementer / Tester / Writer`.

Scope should include a script-driven quality gate and manifest builder, likely:

- `imports/YYYY-MM-DD_salt_mesh_refinement_intake.json`
- `tools/analyze/build_salt_mesh_refinement_quality_gate.py`
- `tools/analyze/test_salt_mesh_refinement_quality_gate.py`
- `work_products/YYYY-MM/YYYY-MM-DD/YYYY-MM-DD_salt_mesh_refinement_quality_gate/**`

It should remain read-only against Ethan's source tree and should not run heavy
OpenFOAM extraction on a login node.
