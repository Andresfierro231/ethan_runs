# AGENT-138 Raw Journal

Date: `2026-06-26`
Role: `Coordinator / Implementer / Writer`

## Context

The user asked to continue the 1D-model closure effort, specifically the CFD-
derived friction-factor and HTC/Nu terms. Existing June 19 and June 23
artifacts already define a partial defended closure boundary, but the terms are
still spread across handoff reports rather than exposed as one reusable local
bundle.

## Scope choice

- Did not reopen `tools/analyze/build_ethan_1d_closure_bakeoff.py` because
  `AGENT-122` still actively owns that path.
- Did not write into `reports/2026-06/**` because `AGENT-127` currently claims
  that broad subtree.
- Chose new fresh tool paths plus `work_products/2026-06-26_ethan_cfd_closure_bundle/`
  so the bounded modeling follow-on can proceed without path conflict.

## Immediate intent

- Convert the currently defended straight-friction fit and thermal branch
  policies into callable local code.
- Emit machine-readable bundle artifacts that distinguish:
  - use-now straight friction
  - primary `UA'` state-surface branches
  - limited-domain direct `Nu`
  - calibration-only residual buckets
  - blocked feature and downcomer direct closures

## Work completed

- Added [cfd_closure_bundle.py](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/analyze/cfd_closure_bundle.py:1)
  on a fresh non-conflicting path under `tools/analyze/`.
- The script now:
  - reads the June 23 closure-term recommendations and branch development
    summary
  - reads the June 19 blocked dependency requirements
  - exposes callable evaluators for:
    - defended straight Darcy friction on `lower_leg` and
      `test_section_span`
    - limited direct `Nu(Re)` on `left_lower_leg`
  - emits one local Salt closure contract with `UA'`, HTC, residual-bucket,
    and blocked-term policy metadata for downstream 1D use
- Added [test_cfd_closure_bundle.py](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/analyze/test_cfd_closure_bundle.py:1)
  covering coefficient parsing, Reynolds-domain parsing, friction / `Nu`
  evaluation, and end-to-end bundle generation.

## Outputs

- [README.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-06-26_ethan_cfd_closure_bundle/README.md:1)
- [salt_closure_bundle.json](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-06-26_ethan_cfd_closure_bundle/salt_closure_bundle.json:1)
- [closure_term_contract.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-06-26_ethan_cfd_closure_bundle/closure_term_contract.csv:1)
- [branch_state_surface_policy.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-06-26_ethan_cfd_closure_bundle/branch_state_surface_policy.csv:1)
- [reference_curve_samples.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-06-26_ethan_cfd_closure_bundle/reference_curve_samples.csv:1)
- [blocked_term_followons.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-06-26_ethan_cfd_closure_bundle/blocked_term_followons.csv:1)
- [summary.json](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-06-26_ethan_cfd_closure_bundle/summary.json:1)
- [2026-06-26_ethan_cfd_closure_bundle.json](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/imports/2026-06-26_ethan_cfd_closure_bundle.json:1)

## Validation

- `python3.11 -m py_compile tools/analyze/cfd_closure_bundle.py tools/analyze/test_cfd_closure_bundle.py`
- `python3.11 -m unittest tools.analyze.test_cfd_closure_bundle`
- `python3.11 tools/analyze/cfd_closure_bundle.py`

## Interpretation boundary

- This follow-on packages the currently defended local Salt closure boundary;
  it does not promote any new feature `K_eff`, downcomer direct `Nu`, or
  cooler-side direct `Nu` claim.
- `UA'` remains the primary admitted thermal surface.
- Direct `Nu` remains a narrow `left_lower_leg`-only option.
- The next real modeling step is not another closure invention pass; it is
  wiring this bundle into the active local 1D evaluation path once the user
  wants that scope reopened.
