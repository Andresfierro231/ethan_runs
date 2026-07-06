# AGENT-087 Raw Journal — Closure-to-Modeling v3

## 2026-06-18

- Re-read the repo startup instructions, task board, ownership map, role map,
  and `tools/AGENTS.override.md` before claiming the new scope.
- Opened `AGENT-087` because the user explicitly requested the next full
  closure-to-modeling campaign rather than another planning pass.
- Deliberately kept the implementation additive:
  - no edits to AGENT-072-owned shared extraction files
  - new analyzers and new dated report roots only

### Task framing

- Salt stayed the primary scientific target.
- Water ran in parallel only as a readiness lane.
- The main decision entering the work:
  - do not preserve the previous provisional feature `K_eff` claim if the
    stronger method still does not exist
  - do try to salvage a limited-domain Salt Nu dependency only if the direct
    retained-time closure data support it

### Salt feature-path hydraulic hardening

- Added `build_ethan_salt_feature_path_hydraulic_hardening.py`.
- Chose a blocker-audit stance instead of inventing a fake full-path result.
- Inputs stayed on the already preserved June 19 feature proxy package.
- New package behavior:
  - preserve proxy-positive feature rows as `sensitivity_only`
  - preserve obviously nonpositive proxy rows as `excluded`
  - refuse any defended feature fit unless a full-path hydro integral exists
- I initially over-tightened the proxy-support gate to `1.0` and accidentally
  erased all proxy-positive context.
- Fixed that by returning the support floor to the existing proxy-support floor
  (`2/3`) and by correcting two source-column mismatches:
  - `positive_time_fraction`
  - `local_support_fraction_min`
- Final outcome:
  - `21` proxy-positive sensitivity-only rows preserved
  - `24` excluded rows
  - `0` defended rows

### Salt thermal closure hardening v3

- Added `build_ethan_salt_thermal_closure_hardening_v3.py`.
- Reused the exact retained-time v2 closure machinery instead of rewriting the
  physics path.
- Only changed the admission policy:
  - residual fraction ceiling raised from `0.30` to `0.45`
  - support, `|Twall - Tbulk|`, grouped reconstruction, and blocked-branch
    rules stayed unchanged
- Before hardening, I inspected the v2 case rows and confirmed the true blocker:
  - direct branches were not failing support
  - they were failing enthalpy-vs-wall closure
- This moderate gate admitted exactly one defensible direct branch family:
  - `left_lower_leg`
- Final outcome:
  - `7` fit-used rows
  - all on `left_lower_leg`
  - `right_leg` still blocked
  - `upcomer` still sensitivity-only

### Salt straight hydraulic sensitivity

- Added `build_ethan_salt_straight_hydraulic_sensitivity.py`.
- This package is intentionally a blocker-aware sensitivity layer, not a fake
  retained-time friction rebuild.
- The additive stack still does not preserve retained-time defended
  hydro-corrected straight rows, so:
  - ratio-gate sensitivities were run on the case-mean defended rows
  - late-window sensitivity was recorded as `not_run`
  - the missing artifact requirement stayed machine-readable

### Salt dependency package v3

- Added `build_ethan_salt_model_dependency_package_v3.py`.
- Deliberately changed the scientific posture relative to v2:
  - straight-section friction remains `provisional_defended`
  - feature `K_eff` is now refused rather than carried forward as provisional
  - Salt Nu is promoted only on a limited direct-branch domain
- Nu fitting result:
  - `7` fit-used rows
  - all from `left_lower_leg`
  - `7` distinct Salt cases
  - `Nu ~ Re^0.961`
  - bootstrap CI on the `log(Re)` slope stayed positive
- This is still not a broad Salt-family Nu claim. It is a domain-limited,
  direct-branch-only claim.

### Water readiness hardening

- Added:
  - `build_ethan_water_thermal_closure_readiness.py`
  - `build_ethan_water_feature_hydraulic_readiness.py`
  - `build_ethan_water_readiness_handoff.py`
- Thermal lane:
  - `24` case-span rows
  - `4` `closure_rebuild_priority`
  - `3` `closure_rebuild_candidate`
- Feature lane:
  - used the preserved proxy residual sign/warning structure only
  - `20` case-feature rows
  - `11` `candidate_for_future_dependency_fit`
  - `8` `needs_closure_rebuild`
  - `1` `blocked`
- No Water dependency was claimed.

### Final closure-to-modeling handoff

- Added `build_ethan_closure_to_modeling_handoff.py`.
- First pass failed because I launched it in parallel with the Salt v3 package
  before the dependent outputs were guaranteed visible.
- Reran it after the Salt v3 durable build landed.
- Tightened the handoff afterward by adding:
  - `exact_excluded_rows.csv`
  - explicit blocked dependency requirements

### Tests and validation

- Added `test_ethan_closure_modeling_v3.py`.
- Tests cover:
  - feature blocker classification
  - Water thermal priority classification
  - Water feature readiness classification
  - limited-domain Nu admission logic
- Validation path:
  - `py_compile`
  - unit tests
  - independent smoke builds
  - durable builds
  - dependent smoke reruns
  - final schema/sanity check

### Final scientific posture from this task

- Straight friction:
  - still usable, still caveated
- Feature `K_eff`:
  - now explicitly refused until the pathwise hydro method exists
- Salt Nu:
  - now publishable only as a direct-branch, limited-domain dependency
- Water:
  - still readiness only
  - more concrete than before, but still not dependency-ready

## 2026-06-19 blocker follow-on refresh

### What changed

- Reopened the Salt straight hydraulic sensitivity builder to consume the
  preserved retained-time package roots directly instead of emitting an empty
  retained-time table.
- Added retained-time reconstruction for `lower_leg` and
  `test_section_span` using:
  - `major_loss_cumulative_timeseries.csv`
  - `leg_centerline_station_definitions.csv`
  - the original hydro-corrected June 17 pressure reduction formulas
- Added a late-window aggregate table that computes per-case, per-section means
  inside the last nominal `20 s` window.
- Refreshed the feature path blocker package so the retained-time table now
  carries the explicit endpoint proxy decomposition:
  - total endpoint `p`
  - endpoint `p_rgh`
  - endpoint hydro proxy
  - proxy feature excess after the local straight reference

### Observed output

- The Salt straight package now publishes:
  - `74` retained-time hydro-corrected straight rows
  - `18` late-window mean rows
- The late-window sensitivity still resolves to `not_run`, but for a narrower
  reason:
  - available preserved tails are only `3-4 s`
  - the target release criterion is still about `20 s`
- The Salt feature blocker remains unresolved physically:
  - retained-time proxy evidence is now clearer and more machine-readable
  - a defended feature-path hydro integral still does not exist in the
    preserved artifact stack

### Interpretation

- Straight friction is no longer blocked by an absence of retained-time rows.
- Straight friction is still blocked by insufficient retained-time duration in
  the currently published package roots.
- Feature `K_eff` remains blocked by upstream physics preservation, not by a
  local postprocessing omission inside the current additive package roots.
