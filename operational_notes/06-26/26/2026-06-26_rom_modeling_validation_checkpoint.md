# ROM Modeling And Validation Checkpoint

Date: `2026-06-26`
Checkpoint writer: `AGENT-145`

## Purpose

This note is the restart package for the current ROM modeling and validation
lane. It captures:

1. the live status of the June 23 latest-window Salt freeze publication
2. the current defended CFD-derived closure surface now packaged for reuse
3. the current local June 22 1D validation and closure-bakeoff state
4. the exact next steps needed to keep building and validating the ROM without
   re-tracing the repo

## Big picture

Today’s relevant modeling work has two different states:

- completed:
  - the current defended Salt CFD closure boundary is now packaged into one
    reusable local bundle
  - the existing June 22 frozen-state local 1D validation and bakeoff stacks
    were rebuilt with that closure bundle wired in
- still running:
  - the June 23 latest-window Salt frozen-state publication is still in the
    expensive exact-time case-refresh path and has not yet emitted its final
    report package

The practical consequence is:

- the local modeling stack is better organized than it was this morning
- the best currently published local validation surface is still the rebuilt
  June 22-based stack
- the intended next validation surface is the June 23 latest-window stack, but
  it is not published yet

## What exists now

### 1. Reusable CFD closure bundle

Primary artifacts:

- [cfd_closure_bundle.py](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/analyze/cfd_closure_bundle.py:1)
- [test_cfd_closure_bundle.py](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/analyze/test_cfd_closure_bundle.py:1)
- [README.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-06-26_ethan_cfd_closure_bundle/README.md:1)
- [salt_closure_bundle.json](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-06-26_ethan_cfd_closure_bundle/salt_closure_bundle.json:1)
- [closure_term_contract.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-06-26_ethan_cfd_closure_bundle/closure_term_contract.csv:1)
- [branch_state_surface_policy.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-06-26_ethan_cfd_closure_bundle/branch_state_surface_policy.csv:1)
- [blocked_term_followons.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-06-26_ethan_cfd_closure_bundle/blocked_term_followons.csv:1)

Current defended boundary:

- straight Darcy friction:
  - status: `provisional_defended`
  - admitted target regions: `lower_leg`, `test_section_span`
- direct internal `Nu(Re)`:
  - status: `provisional_defended_limited_domain`
  - admitted target region: `left_lower_leg`
- primary thermal comparison surface:
  - branchwise effective `UA'`
- explicitly not promoted:
  - feature `K_eff`
  - direct downcomer `Nu`
  - broad cooler-side direct `Nu`

Interpretation boundary:

- `UA'` remains the main thermal surface for reduced-order comparison.
- Direct `Nu` is still a narrow local option, not a loop-global replacement.
- `upcomer` remains sensitivity-only rather than a defended direct straight
  branch.

### 2. Current local 1D validation and bakeoff surface

Current rebuilt June 22-based local packages:

- [2026-06-23_ethan_frozen_state_1d_validation](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06/2026-06-23/2026-06-23_ethan_frozen_state_1d_validation:1)
- [2026-06-23_ethan_1d_closure_bakeoff](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06/2026-06-23/2026-06-23_ethan_1d_closure_bakeoff:1)

Key current outcome:

- defended winner still:
  `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`

New useful outputs now present in both local packages:

- `closure_term_reference.csv`
- `closure_branch_policy.csv`
- `scenario_bundle_alignment.csv`

Why these matter:

- the local 1D comparison no longer leaves the closure boundary only in prose
- each readable scenario can now be checked against the defended straight
  friction / `UA'` / limited direct-`Nu` bundle
- the defended winner is currently marked `full_bundle_alignment`

### 3. Latest-window frozen-state publication

Target final report root:

- [2026-06-23_ethan_frozen_state_results_latest_window](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06/2026-06-23/2026-06-23_ethan_frozen_state_results_latest_window:1)

Builder:

- [build_ethan_latest_window_frozen_state_stack.py](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/analyze/build_ethan_latest_window_frozen_state_stack.py:1)
- [test_ethan_latest_window_frozen_state_stack.py](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/analyze/test_ethan_latest_window_frozen_state_stack.py:1)

Important builder hardening already completed:

- defaults now point to the real nested June 23 report tree under
  `reports/2026-06/2026-06-23/...`
- the import manifest now records the requested `--checkpoint-root` rather than
  a stale hard-coded default

Current runtime state observed during this session:

- live long-running process was launched through the latest-window builder
- `salt1_jin` already has a refreshed package root at:
  [salt1_jin](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tmp/2026-06-23_ethan_latest_window_case_analysis_refresh/salt1_jin:1)
- `salt2_cont` has started writing refreshed raw-extraction outputs but does
  not yet have a final `summary.json`
- the final latest-window report root is still empty, so the publication is
  not done yet

Observed exact-time status at the last checks:

- `salt1_jin` completed the retained-time field reconstruction path and entered
  cross-section reduction
- one observed reduction slice:
  `time 3229`, `379` surfaces, finished in about `189.6 s`
- later observed reduction slice:
  `time 3398.45`, still in progress during polling

Interpretation:

- no logic failure has been observed
- the long pole is the exact-time reconstruction plus reduction workload
- the latest-window package should be treated as in progress, not missing

### 4. External ROM / Fluid replay status

Relevant active status:

- [2026-06-22_AGENT-102.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/.agent/status/2026-06-22_AGENT-102.md:1)

Current state:

- the local replay package against the June 22 frozen-state contract exists
- the tracked external readable `Fluid` bundle is still stale:
  `validation_data/ethan_cfd_informed_salt_v1/`
- there is still no in-repo producer under
  `../cfd-modeling-tools/tamu_first_order_model/Fluid/**` that regenerates a
  fresh Ethan CFD-informed Salt validation bundle from the newer local closure
  and frozen-state surfaces

Practical meaning:

- local validation work can continue inside `ethan_runs`
- a refreshed externally readable ROM validation package still needs either:
  - a real bundle producer path, or
  - a temporary versioned `v2` static-bundle publication path

## Recommended next-step order

This is the best order to continue without wasting expensive refresh work.

### Step 1. Finish the latest-window frozen-state package

If the current live refresh completes successfully, do a clean final republish
with skip-refresh so the corrected builder code writes the final report and
manifest:

```bash
python tools/analyze/build_ethan_latest_window_frozen_state_stack.py \
  --freeze-windows-csv reports/2026-06/2026-06-23/2026-06-23_ethan_cfd_freeze_checkpoint/freeze_case_windows.csv \
  --representative-timesteps-csv reports/2026-06/2026-06-23/2026-06-23_ethan_cfd_freeze_checkpoint/representative_timesteps.csv \
  --checkpoint-root tmp/2026-06-23_salt_last20_checkpoint \
  --case-analysis-root tmp/2026-06-23_ethan_latest_window_case_analysis_refresh \
  --output-dir reports/2026-06/2026-06-23/2026-06-23_ethan_frozen_state_results_latest_window \
  --import-manifest-path imports/2026-06-23_ethan_frozen_state_results_latest_window.json \
  --skip-case-refresh
```

If the live refresh dies before all four Salt Jin case roots are complete,
rerun the same command without `--skip-case-refresh`.

Success condition:

- the final report root contains at least:
  - `summary.json`
  - `frozen_state_contract.csv`
  - `branch_behavior_summary.csv`
  - `branch_development_summary.csv`
  - `branch_drift_by_case.csv`
  - `README.md`

### Step 2. Publish the latest-window local 1D validation

Once the latest-window frozen package exists:

```bash
python tools/analyze/build_ethan_frozen_state_1d_validation_package.py \
  --frozen-dir reports/2026-06/2026-06-23/2026-06-23_ethan_frozen_state_results_latest_window \
  --output-dir reports/2026-06/2026-06-23/2026-06-23_ethan_frozen_state_1d_validation_latest_window \
  --closure-bundle-dir work_products/2026-06-26_ethan_cfd_closure_bundle \
  --import-manifest-path imports/2026-06-23_ethan_frozen_state_1d_validation_latest_window.json
```

Validation package checks:

- confirm `summary.json` exists
- confirm `closure_term_reference.csv` exists
- confirm `scenario_bundle_alignment.csv` exists
- confirm the source-contract label reflects the latest-window frozen package,
  not the June 22 contract

### Step 3. Publish the latest-window local closure bakeoff

```bash
python tools/analyze/build_ethan_1d_closure_bakeoff.py \
  --frozen-dir reports/2026-06/2026-06-23/2026-06-23_ethan_frozen_state_results_latest_window \
  --output-dir reports/2026-06/2026-06-23/2026-06-23_ethan_1d_closure_bakeoff_latest_window \
  --closure-bundle-dir work_products/2026-06-26_ethan_cfd_closure_bundle \
  --import-manifest-path imports/2026-06-23_ethan_1d_closure_bakeoff_latest_window.json
```

Bakeoff checks:

- confirm the defended winner remains or note if it changes
- inspect `scenario_bundle_alignment.csv`
- inspect `defended_full_coverage_surface/case_metric_summary.csv`
- explicitly compare latest-window results against the current June 22-based
  bakeoff before changing any top-line claim

### Step 4. Publish the latest-window discrepancy explainer

```bash
python tools/analyze/build_ethan_1d_discrepancy_explainer_latest_window.py \
  --frozen-dir reports/2026-06/2026-06-23/2026-06-23_ethan_frozen_state_results_latest_window \
  --validation-dir reports/2026-06/2026-06-23/2026-06-23_ethan_frozen_state_1d_validation_latest_window \
  --bakeoff-dir reports/2026-06/2026-06-23/2026-06-23_ethan_1d_closure_bakeoff_latest_window \
  --output-dir reports/2026-06/2026-06-23/2026-06-23_ethan_1d_discrepancy_explainer_latest_window \
  --import-manifest-path imports/2026-06-23_ethan_1d_discrepancy_explainer_latest_window.json
```

Goal of this step:

- turn the latest-window comparison into a bounded explanation package instead
  of only raw score tables

### Step 5. Turn the local closure bundle into actual ROM inputs

The next modeling step after publication is not more free-form closure
invention. It is consuming the defended bundle in the ROM path.

Immediate sub-steps:

- map bundle outputs from
  [salt_closure_bundle.json](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-06-26_ethan_cfd_closure_bundle/salt_closure_bundle.json:1)
  onto the inputs expected by the external `Fluid` validation surface
- define one explicit boundary document for:
  - where straight friction is applied
  - where `UA'` is the primary thermal target
  - where only sensitivity-only `Nu` / HTC should be used
  - which regions remain blocked rather than approximated

If a refreshed external bundle producer is built, it should ingest the local
bundle rather than duplicate the closure numbers by hand.

### Step 6. Refresh the external readable ROM validation surface

This remains the main unclosed gap.

Options:

1. preferred:
   build a reproducible producer under
   `../cfd-modeling-tools/tamu_first_order_model/Fluid/**` that consumes the
   refreshed frozen/closure inputs and emits a fresh Ethan Salt bundle
2. fallback:
   publish a versioned `v2` static bundle and wire the existing replay path to
   that new versioned input

Do not claim a refreshed readable ROM validation surface until one of those
exists.

## Modeling TODO list

### Immediate TODO

- [ ] Let the current latest-window refresh complete or fail decisively.
- [ ] Republish the latest-window frozen-state package with
  `--skip-case-refresh`.
- [ ] Run latest-window local validation with the closure bundle.
- [ ] Run latest-window local bakeoff with the closure bundle.
- [ ] Run latest-window discrepancy explainer.

### ROM integration TODO

- [ ] Write the bundle-to-ROM variable mapping.
- [ ] Confirm which ROM branches consume straight friction versus `UA'`
  versus sensitivity-only thermal terms.
- [ ] Keep direct downcomer and feature closures blocked unless new evidence
  truly expands support.
- [ ] Record any latest-window change in defended winner or error surface
  before touching external presentation claims.

### Validation TODO

- [ ] Summarize latest-window mass-flow, TP, TW, and heater-normalized energy
  errors in one table once the new packages exist.
- [ ] Compare June 22-based and latest-window-based local surfaces side by side.
- [ ] Separate hydraulic improvements from thermal allocation/setup mismatch.
- [ ] State explicitly whether the global `1.4 in` scenario remains absent from
  the readable external bundle.

### Stretch TODO

- [ ] Build a refreshed external `Fluid` producer or `v2` static bundle.
- [ ] Re-run the readable ROM validation campaign against the refreshed local
  closure/frozen contract.
- [ ] Publish a paper-facing validation-context package only after the updated
  local latest-window surface and external readable surface agree on the
  bounded scenario menu.

## Commands already validated in this lane

Closure bundle:

```bash
python3.11 -m py_compile tools/analyze/cfd_closure_bundle.py tools/analyze/test_cfd_closure_bundle.py
python3.11 -m unittest tools.analyze.test_cfd_closure_bundle
python3.11 tools/analyze/cfd_closure_bundle.py
```

Current local 1D surface:

```bash
python3.11 -m py_compile \
  tools/analyze/build_ethan_frozen_state_1d_validation_package.py \
  tools/analyze/build_ethan_1d_closure_bakeoff.py \
  tools/analyze/test_ethan_frozen_state_1d_validation_package.py \
  tools/analyze/test_ethan_1d_closure_bakeoff.py

python3.11 -m unittest \
  tools.analyze.test_ethan_frozen_state_1d_validation_package \
  tools.analyze.test_ethan_1d_closure_bakeoff
```

Latest-window builder hardening:

```bash
python3.11 -m py_compile \
  tools/analyze/build_ethan_latest_window_frozen_state_stack.py \
  tools/analyze/test_ethan_latest_window_frozen_state_stack.py \
  tools/analyze/build_ethan_1d_discrepancy_explainer_latest_window.py \
  tools/analyze/test_ethan_1d_discrepancy_explainer_latest_window.py

python3.11 -m unittest \
  tools.analyze.test_ethan_latest_window_frozen_state_stack \
  tools.analyze.test_ethan_1d_discrepancy_explainer_latest_window
```

## Claim boundary

Safe claims today:

- the local closure boundary is better packaged and more explicit than before
- the current defended local June 22-based winner is still the baseline
  `1.0 in` radiation-on row
- latest-window publication is in progress but not published
- the readable external `Fluid` surface is still stale relative to the current
  local closure and frozen-state work

Do not claim today:

- that the latest-window frozen-state package exists
- that the latest-window local validation or bakeoff has been published
- that the readable external ROM validation surface has been refreshed
- that downcomer direct `Nu`, feature `K_eff`, or a loop-global direct `Nu`
  closure is now defended
