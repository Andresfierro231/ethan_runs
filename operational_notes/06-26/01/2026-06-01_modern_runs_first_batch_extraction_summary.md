# 2026-06-01 modern_runs first batch extraction summary

## 2026-06-30 supersession note

This note is retained as a historical extraction checkpoint. The June 30 run
classification policy supersedes any implication below that Kirst cases are
current mainline comparison inputs. Continuation-derived Jin artifacts are the
current mainline path when present; Kirst rows remain historical/provenance
context only.

## Observed output

- Extracted local inventory and QoI products for the first staged `modern_runs` batch:
  - 8 salt viscosity-screen cases
  - 4 water laminar cases
- Campaign-level tables were generated under `work_products/campaigns/2026-06-01_modern_runs_first_batch/`.
- Summary counts from that campaign root:
  - `source_count = 12`
  - fluids: `hitec_salt_jin = 4`, `hitec_salt_kirst = 4`, `water = 4`
  - turbulence models: `laminar = 12`
  - validation status: all 12 cases report `derived_postprocessing_available`
  - run status counts: `terminated = 10`, `incomplete = 2`
- QoI availability is complete for all 12 extracted cases: mdot, total wall heat, PIV slab metrics, and probe temperatures are all present in the local extraction products.
- The two incomplete runs in this first batch are:
  - `viscosity_screening_salt_test_1_kirst_coarse_mesh`
  - `viscosity_screening_salt_test_2_kirst_coarse_mesh`
- Historical salt Jin/Kirst pair tables exist for tests `1-4` in
  `salt_variant_pairs.csv`; do not treat them as current mainline comparison
  inputs without a later dated re-admission note.
- Water laminar operating-point tables now exist for tests `1-4` in `water_laminar_operating_points.csv`.

## Inferred interpretation

- The local intake workflow is now proven on a real 12-case batch, not just on the original single salt2 case.
- The first modern batch is extraction-complete locally and is ready for campaign-level review.
- The salt campaign had enough local products for a historical Jin/Kirst
  property-screen audit, but this is no longer a mainline comparison path under
  the 2026-06-30 run classification policy.
- The water laminar set is ready for operating-point trend review and later 1D-bridge work.

## Contradictions / risks

- Local extraction completeness does not mean publish readiness.
- The current reference join tooling expects canonical case ids such as `salt_test_2`; it does not yet encode any re-admitted historical variant use.
- Kirst salt cases should not be treated as a current mature comparison set.
- The 4 water `kOmegaSSTLM` cases remain excluded because they still do not expose actual solver-output trees.

## Next suggested actions

- Do not make campaign-level physical claims from Kirst rows under the current
  mainline policy.
- If a future bounded Kirst use is needed, create a dated re-admission note and
  an explicit variant-aware comparison contract before publish handoff.
- Keep the water `kOmegaSSTLM` cases deferred until real runtime outputs exist.
- Use the new campaign tables as the local source of truth for any next-step comparison scripting.
