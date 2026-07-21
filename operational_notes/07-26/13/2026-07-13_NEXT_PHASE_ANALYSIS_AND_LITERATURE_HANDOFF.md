# 2026-07-13 Next Phase Analysis And Literature Handoff

Task: `AGENT-295`  
Purpose: give the next agent a compact, evidence-backed plan for continuing
today's closure and predictive-model work without reading chat history.

## Open First

1. `.agent/BOARD.md` for current ownership. At handoff, avoid overlapping
   active rows such as `AGENT-294`, `AGENT-290`, and
   `TODO-PRED-WALL-SHELL-SAMPLE`.
2. `operational_notes/07-26/13/2026-07-13_CURRENT_CLOSURE_AND_PREDICTIVE_MODEL_START_HERE.md`
   for the AGENT-292 continuity anchor.
3. `operational_notes/07-26/13/2026-07-13_external_report_research_index_and_blocker_audit.md`
   for the project-wide topic map and stale-versus-real blocker audit.
4. `work_products/2026-07/2026-07-13/2026-07-13_litrev_todo_campaign_index/README.md`
   for the five literature gate packages and their reading order.
5. `work_products/2026-07/2026-07-13/2026-07-13_salt2_fine_reconstructed_t_repair_plan_sbatch/repair_trial_output/summary.json`
   for the completed fine reconstructed-`T` repair smoke result.
6. `work_products/2026-07/2026-07-13/2026-07-13_salt2_closure_qoi_mesh_gci/README.md`
   for the prior Salt2 Closure-QOI mesh/GCI blocker state.

## Current State

Observed facts:

- Salt2 fine reconstructed-`T` repair job `3293768` completed successfully:
  `COMPLETED`, exit `0:0`, elapsed `00:22:33`, node `c318-016`.
- The fine repair package reports: clean reconstructed `399/T`, successful
  `30/30` section temperature sampling, and segment thermal extraction with
  `computed=2` and `thermally_blocked_segment_right_leg=1`.
- Fine final `T` scan:
  - whole-file nonfinite scalar count: `0`
  - Kelvin temperature-list entries: `22,684,344`
  - temperature lists: `47`
  - temperature outside `250..1500 K`: `0`
  - temperature range: `350.122443..489.015015 K`
- Fine computed segment rows:
  - lower leg: `HTC=460.760023 W/m2/K`, `UA'=40.355909 W/m/K`
  - upcomer: `HTC=76.397611 W/m2/K`, `UA'=6.560882 W/m/K`,
    `Nu=4.208841`
  - downcomer remains `thermally_blocked_segment_right_leg`
- These are repair-smoke results, not closure admissions. Both computed segment
  rows carry `sign_consistent_heated_wall=False` in the segment CSV, so the next
  thermal task must review sign/heat-balance conventions before publication or
  fitting.

Interpretation:

The old refined thermal blocker has changed shape. It is no longer "fine
reconstructed `T` unavailable." The current blocker is "fine thermal smoke
exists, but thermal closure admission still needs sign, heat-balance,
downcomer-policy, and mesh-family review."

## Phase Plan

### Phase 1: Harvest And Close AGENT-291 Evidence

Goal: turn the completed fine repair smoke into durable accepted evidence or a
clearly bounded partial result.

Actions:

- Update AGENT-291 status/import/board row with terminal job evidence.
- Record `sacct -j 3293768 --format=JobID,JobName,State,ExitCode,Elapsed,NodeList%30`.
- Verify `repair_trial_output/summary.json`,
  `outputs/reconstruction_trials.csv`, section CSV/JSON, segment CSV/JSON, and
  logs are present.
- Preserve the native-output boundary: do not copy results into native case
  trees and do not edit source solver output.

Acceptance:

- A journal/status update says exactly which gates passed and which thermal
  closure admissions remain blocked.

### Phase 2: Salt2 Thermal Mesh/GCI Gate

Goal: rerun or extend the Salt2 Closure-QOI mesh/GCI package now that medium and
fine thermal smoke both exist.

Inputs:

- AGENT-267 medium thermal output:
  `work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_trial/`
- AGENT-291 fine thermal output:
  `work_products/2026-07/2026-07-13/2026-07-13_salt2_fine_reconstructed_t_repair_plan_sbatch/repair_trial_output/`
- Existing Salt2 Closure-QOI mesh/GCI package:
  `work_products/2026-07/2026-07-13/2026-07-13_salt2_closure_qoi_mesh_gci/`

Actions:

- Create or claim `TODO-PRED-THERMAL-MESH-GATE` or a new AGENT row.
- Add fine thermal rows to the Salt2 thermal QOI table.
- Compare coarse/medium/fine where all three QOIs exist.
- Keep QOIs without all three mesh levels as blocked or two-level diagnostics.
- Run sign and heat-balance review before interpreting HTC/UA/Nu.
- Do not publish a GCI number for non-monotone, oscillatory, or missing-triplet
  QOIs.

Acceptance:

- A table classifies each thermal QOI as `publication_ready_gci`,
  `diagnostic_two_level`, `blocked_sign_review`, `blocked_missing_coarse`,
  `blocked_downcomer_policy`, or equivalent.

### Phase 3: Thermal Admission Review

Goal: decide what, if anything, can enter closure fitting or thesis-strength
thermal evidence.

Questions:

- Are lower-leg and upcomer sign conventions consistent with the intended
  heated/cooled segment definitions?
- Is `q_sign` positive/negative convention aligned between wallHeatFlux,
  segment duty, enthalpy change, and UA/HTC definitions?
- Is the downcomer/right-leg thermal block a policy block, an extraction block,
  or a real invalid-stream block?
- Are medium and fine values close enough to support a mesh-family trend before
  using them?

Guardrail:

Do not use the repaired UA/HTC/Nu values as closure-fit targets until this phase
explicitly admits them.

### Phase 4: Predictive Model Hydraulic First

Goal: prevent thermal fitting from hiding hydraulic error.

Current evidence:

- `TODO-PRED-HYDRAULIC-GATE` reports forward-v0 mdot overprediction for every
  Salt row: `F0` mean `+0.008082 kg/s`, `F1` mean `+0.005478 kg/s` versus CFD.
- Fit-safe raw pressure-gradient rows are limited; momentum-corrected rows are
  broader but diagnostic.

Actions:

- Use pressure ledger, reset/named-loss, and CFD validity packages before any
  new friction/minor-loss fitting.
- Decide property lane first.
- Separate straight-section friction, component K, cluster K, branch-apparent
  loss, redevelopment/reset, and recirculation diagnostics.

Acceptance:

- A hydraulic scorecard states whether mdot error has been reduced without
  using thermal parameters.

### Phase 5: Predictive Thermal Boundary And Wall Layer

Goal: move from imposed CFD cooler duty toward predictive external-boundary and
wall-layer models.

Current evidence:

- `TODO-PRED-HX-FIT` delivered protocol but is blocked until a declared
  validation split exists.
- `TODO-PRED-HEATER-TEST-CONTRACT` recommends heater-only as the next unfitted
  imposed-cooler source contract.
- `TODO-PRED-WALL-LAYER` delivered E0 bulk-drive rows and blocked E1/E2 pending
  near-wall shell extraction.
- `TODO-PRED-WALL-SHELL-SAMPLE` is active and should not be overlapped.
- `TODO-FLUID-EXTERNAL-BC-DICT` remains the eventual Fluid API work for
  first-class external h/Ta/Tsur/emissivity/wall-layer boundary dictionaries.

Actions:

- Let `TODO-PRED-WALL-SHELL-SAMPLE` finish.
- Then compare E0/E1/E2 external hA mappings.
- Only after a validation split, fit HX UA or epsilon-NTU parameters.
- Keep CFD `wallHeatFlux` replay separate from predictive boundary conditions.

Acceptance:

- A thermal boundary scorecard separates imposed-cooler replay, heater-only
  source contract, wall-layer drive mapping, and predictive HX fit.

### Phase 6: Validation Split And End-to-End Score

Goal: stop fitting and scoring on the same rows.

Actions:

- Create `TODO-PRED-VALIDATION-SPLIT` before any calibrated HX, heater, wall, or
  friction parameter is treated as predictive.
- Declare training rows, held-out rows, perturbation/sensitivity rows, and
  diagnostic-only rows.
- Run `TODO-PRED-ENDTOEND-SCORE` only after hydraulic, thermal mesh/admission,
  sensor mapping, and validation split are all explicit.

Acceptance:

- One scorecard separates training versus held-out mdot, branch heat, Tmean,
  loop delta, TP/TW, uncertainty, and residual attribution.

## Needed Literature Gates

Use author/title provenance from the lit-rev packages. Do not rely on citation
numbers.

| Gate | Package | Literature / Method Role | How The Next Agent Should Use It |
| --- | --- | --- | --- |
| Source envelope | `2026-07-13_litrev_source_envelope` | Chen et al. molten-salt mixed convection; Tian et al. turbulent/horizontal cooling; Everts and Meyer entrance-length gates; Shah/Muzychka-Yovanovich developing-flow references. | Before promoting any `Nu`, `f`, or mixed-convection source, check whether TAMU branch `Re/Pr/Gr/Ri/Gz/L/D` is inside, outside, or unknown. Outside/unknown means reference-only or sensitivity-only. |
| Property sensitivity | `2026-07-13_litrev_property_sensitivity` | Reis/Jadyn replication properties versus Sohal/Janz, Jin viscosity, Parida/Basu cp, Santini conductivity, and related molten-salt property reviews. | Choose a property lane before fitting pressure, heat-loss, or Nu residuals. Keep replication and updated-property modes separate. |
| CFD validity | `2026-07-13_litrev_cfd_validity_diagnostics` | Patino-Jaramillo tee-flow diagnostics; Podila CFD loop modeling; coefficient naming discipline for invalid single-stream regions. | Reject universal `f_D`, `K`, or `Nu` labels where recirculation, reverse flow, or inseparable section effects are present. |
| Reset/named losses | `2026-07-13_litrev_reset_named_losses` | Lin pressure-loss reviews, Al-Tameemi/Ricco elbows, Patino-Jaramillo tee joints, Salehi close-coupled elbows, Muzychka-Yovanovich developing pressure loss. | Keep straight-section, component-K, cluster-K, and branch-apparent losses separate. Never hide them inside one global friction multiplier. |
| Heat-loss calibration | `2026-07-13_litrev_heat_loss_calibration` | VDI Heat Atlas resistance-network architecture; Reis/Seo/Hassan heater-failure and loop heat-loss context. | Keep jacket/cooler, passive convection, radiation metadata, heater input, wall/storage, and residual separate. Internal Nu must not absorb external heat-loss terms. |
| Internal heat transfer | `reports/.../2026-07-13_litrev_lessons_and_research_pathways` plus `2026-07-09_internal_nu_model_form_comparison` | Muzychka-Yovanovich forced developing Nu; Everts/Meyer entrance lengths; Chen 2017 low-Re molten-salt mixed convection; Yang/Shen/Chen multi-sided/nonuniform heating as diagnostics. | Treat fully developed Nu as reference. Treat Chen 2017 as conditional only after source-envelope pass. Treat nonuniform/inclination papers as diagnostics unless geometry/range matches. |
| ROM / reduced order | `reports/.../2026-07-13_litrev_lessons_and_research_pathways` | Manthey, Vergari, Star, Acierno ROM pathways. | Future method only. Do not claim ROM prediction until snapshot envelope, stabilization, and held-out validation exist. |

## Do-Not-Do Guardrails

- Do not mutate native solver outputs.
- Do not re-report solved blockers as open: OF13 reconstruction works, mesh
  families are readable, and CFD `rcExternalTemperature` includes radiation.
- Do not use Kirst runs as current mainline evidence.
- Do not classify perturbation runs as nominal baselines.
- Do not fit thermal parameters before hydraulic mdot error is accounted for.
- Do not use repaired fine UA/HTC/Nu as closure targets before sign,
  heat-balance, downcomer-policy, and mesh-family gates pass.
- Do not double-count radiation: current CFD `wallHeatFlux` embeds
  `rcExternalTemperature` effects and no separate observed `qr` term is
  available in these packages.
- Do not start broad documentation-system edits while AGENT-294 is active.

## Suggested Next Board Rows

Highest value immediate rows:

1. `TODO-PRED-THERMAL-MESH-GATE`: consume AGENT-267 medium and AGENT-291 fine
   thermal outputs; classify thermal QOIs; no closure admission without gates.
2. `TODO-PRED-VALIDATION-SPLIT`: declare train/held-out rows before fitting HX,
   heater, wall, or hydraulic parameters.
3. `TODO-FLUID-EXTERNAL-BC-DICT`: after wall-shell sampling, add Fluid-side
   support for external boundary dictionaries.
4. `TODO-PRED-ENDTOEND-SCORE`: only after hydraulic, thermal, sensor, and split
   gates are complete.

