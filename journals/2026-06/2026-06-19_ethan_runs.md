# 2026-06-19 Ethan Runs

## Summary

Added a new internal handoff package:

- `reports/2026-06-19_ethan_litrev_to_1d_modeling_handoff`

This package compiles the most useful closure and model-form results from the
literature-review repo into a repo-local planning surface for future 1D model
work. The key correction is explicit: the future Ethan 1D model should not
assume that long sections are automatically pressure-drop-developed or
thermally developed just because fully developed reference values exist in the
literature.

## Observed Output

- The package publishes:
  - `closure_crosswalk.csv`
  - `correlation_registry.csv`
  - `segment_closure_policy.csv`
  - `shared_closure_bundle_contract.csv`
  - `nondimensional_group_spec.csv`
  - `required_future_cfd_observables.csv`
  - `rom_test_matrix.csv`
  - `dual_path_workstreams.csv`
  - `dual_path_execution_report.md`
  - `report_outline.md`
  - `writing_checklist.md`
  - `open_questions.md`
  - `summary.json`
- The compiled policy remains aligned with the current June 19 modeling stack:
  - straight friction on admitted Salt straights is usable
  - `UA'(x)` is the primary admitted thermal surface
  - `HTC(x)` remains secondary
  - direct fitted `Nu(Re)` remains limited to `left_lower_leg`
  - feature `K_eff` remains blocked
  - fixed readable cooler `Q` remains admitted while live cooler-side `h`
    remains unadmitted

## Inferred Interpretation

- The literature review already contains the right closure menu, but its most
  useful role for this repo is as a bounded menu of options rather than as a
  direct instruction to use fully developed values everywhere.
- The first useful Ethan 1D model should stay hybrid:
  - defended direct closures where current evidence supports them
  - support-gated thermal state surfaces where direct closures are still too
    narrow
  - explicit residual buckets where the current CFD artifact stack is still
    missing key observables
- The best current nondimensional strategy is still family-aware rather than
  one collapsed Salt-plus-Water fit.
- The package now answers the immediate execution question directly:
  - the Salt CFD-informed ROM effort can start now
  - the first code lane should be the current `Fluid` solver
  - the parallel clean lane should be `salt_cfd_rom`
  - both lanes should consume one identical closure bundle
  - defended feature `K_eff` is still not part of that first bundle

## Contradictions And Limits

- Fully developed friction and fully developed `Nu` values remain baseline or
  comparison surfaces, not universal closure defaults.
- Feature `K_eff` still needs a retained-time full-path hydro extractor before
  it can be defended.
- Right-leg direct thermal closure remains unsupported.
- Water remains readiness-only in the current closure-to-modeling stack.
- The readable 3D boundary model still exposes fixed cooler sink `Q`, not a
  directly readable cooler-side `h` control.

## Scripts And Reproducibility

- No new analysis builder was added for this package.
- The package is a manual evidence-synthesis pass grounded in:
  - the literature-review evidence tables and chapters
  - the June 19 closure-to-modeling and blocker packages
  - the June 19 Salt dependency package v3
  - the June 18 Salt thermal surface ranking
  - the June 17 nondimensional dashboard
  - the June 15 boundary-modeling report
  - the June 2 1D discrepancy report
  - the current `Fluid` directory guide, v2 solver README, Makefile, practical
    reduced-order planning report, profile-descriptor diagnostic report, and
    joint HTC/friction calibration artifacts
- The source set is recorded in:
  - `imports/2026-06-19_ethan_litrev_to_1d_modeling_handoff.json`

## Next Suggested Actions

- Use this package as the planning surface before opening any new 1D
  implementation task.
- Use the new dual-path execution report, bundle contract, correlation
  registry, and ROM test matrix as the handoff into the actual 1D code
  workspace.
- When work shifts from report planning to actual model implementation, open a
  separate task in the relevant 1D code workspace.
- Refresh this package after:
  - a retained-time feature-path hydraulic extractor lands
  - or the current continuation and bracket waves preserve enough late-window
    support to rerun the straight and thermal hardening packages on stronger
    retained-time evidence

## Monday Handoff

### Current state at stop

- The new Fluid-side campaign is launched in the sibling repo under:
  - `../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/ethan_cfd_informed_salt_v1`
- The active 3D queue state refreshed on `2026-06-22` is:
  - running:
    - `3244950` `ethan_s3j_cont`
    - `3244951` `ethan_s2j_cont`
    - `3244954` `ethan_s4j_cont`
    - `3244957` `ethan_w2_cont`
    - `3246561` `ethan_s2j_hiqins`
    - `3246564` `ethan_s2j_loqins`
    - `3250524` `ethan_s4j_hiqins_r2`
    - `3250525` `ethan_s4j_loqins_r2`
  - pending:
    - `3250526` `ethan_salt_optpack`
  - failed before repair:
    - `3246562` `ethan_s4j_hiqins`
    - `3246563` `ethan_s4j_loqins`
    - `3246927` `ethan_salt_optpack`
  - timed out:
    - `3244952` `ethan_w3_cont`
    - `3244953` `ethan_w1_cont`
    - `3244956` `ethan_w4_cont`
- The deferred Salt 3 Jin midpoint children are now fully staged but not
  submitted:
  - `jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/runs/salt3_jin_hiq_hiins/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh`
  - `jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/runs/salt3_jin_loq_loins/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh`

### Key modeling context to carry into Monday

- Do not talk about `f_D` or `Nu` as generic `Re`-only closures.
- The current defended posture is:
  - Salt-only direct hydraulic fit is context-aware and already uses segment
    class
  - direct `Nu(Re)` is defended only on `left_lower_leg`
  - `Gz` is the main entry-development diagnostic
  - `Ri = Gr / Re^2` is a buoyancy / mixed-convection gate
  - Salt and Water remain separate fitting families
- Do not propose or present a cooler-`h` DOE as if it were readable from the
  current case trees.
- Do not claim feature `K_eff` is closeable by more runtime alone; the missing
  item is a retained-time full-path hydro extractor.

### Monday TODO for presentation prep

- Recheck queue and campaign health first:
  - `squeue -j 3244950,3244951,3244954,3244957,3246561,3246564,3250524,3250525,3250526`
- Pull the current presentation-safe story from these report roots:
  - `reports/2026-06-19_ethan_blocker_report_and_followon_wave/`
  - `reports/2026-06-19_ethan_litrev_to_1d_modeling_handoff/`
  - `reports/2026-06-19_ethan_closure_to_modeling_handoff/`
  - `reports/2026-06-19_ethan_salt_conclusions_package/`
  - `reports/2026-06-17_ethan_nondimensional_dashboard_package/`
- Build the presentation around four clear messages:
  - why the continuation wave was necessary
  - what is actually defended for the first Salt 1D model
  - which CFD jobs are running or queued now
  - what remains blocked and why
- If there is time after presentation prep:
  - decide whether the Salt 3 midpoint pair should be submitted from the
    already-staged June 19 campaign root
  - otherwise leave them staged and explicitly call them “ready next wave”

## Development-Aware Closure Follow-On

## Summary

Added one concrete next-step plan under:

- `reports/2026-06-19_ethan_litrev_to_1d_modeling_handoff/development_aware_closure_plan.md`

This follow-on plan turns the earlier dual-path brief into a more explicit
development-aware closure roadmap for the next ROM pass.

## Observed Output

- The plan now recommends fitting normalized closure residuals rather than raw
  closure values:
  - `phi_f = f_D / (64 / Re)`
  - `phi_nu = Nu / Nu_ref`
- The first candidate nondimensional family is now explicit:
  - `Re`
  - `Pr`
  - `Ri = Gr / Re^2`
  - `Gz`
  - development distance normalized by hydraulic diameter
  - branch or reset class
- The proposed fit order is explicit:
  - fit friction first
  - compare direct thermal versus hydraulically informed thermal fits second
  - test a shared latent development-amplitude family if the separate fits are
    too coupled or too noisy

## Inferred Interpretation

- This is the right next modeling step because it keeps fully developed
  references visible as asymptotes while allowing development-aware
  corrections to vary by branch and reset history.
- `Ri` is the cleaner first buoyancy flag than raw `Gr` for the vertical and
  strongly heated branches.
- The first direct coupled closure should still stay Salt-only and branch
  bounded even if the final form later becomes more general.

## Contradictions And Limits

- No additional CFD submission was justified from this planning lane on
  `2026-06-22`.
- Current queue state refreshed on `2026-06-22`:
  - running: `3244950`, `3244951`, `3244954`, `3244957`, `3246561`, `3246564`, `3250524`, `3250525`
  - pending: `3250526`
  - failed before repair: `3246562`, `3246563`, `3246927`
  - timed out: `3244952`, `3244953`, `3244956`
  - completed: `3244955`
- The June 19 blocker package remains the authority for the compute decision:
  - keep the active continuation wave
  - keep the already-submitted Salt 2 / Salt 4 bracket wave
  - keep the repaired optimum wave queued
  - do not submit the deferred Salt 3 Jin midpoint bracket yet
  - do not submit new Water or feature-`K_eff` DOE

## Monday Pickup

- Freeze the exact development-coordinate contract:
  - hydraulic reset definition
  - thermal reset definition
  - branch transitions that count as resets
- Build the first low-order candidate fit harness around:
  - `F1` hydraulic development family
  - `T1` direct thermal family
  - `T2` hydraulically informed thermal family
  - `LT1` shared latent development family
- Open the separate 1D code-workspace task for:
  - the current `Fluid` replay/import lane
  - the clean `salt_cfd_rom` skeleton
- Start Monday presentation prep around:
  - why fully developed values are references, not defaults
  - what closures are admitted now
  - what remains blocked
  - why the current June 22 queue is already the right CFD action
