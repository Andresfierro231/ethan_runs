---
provenance:
  - .agent/BLOCKERS.md
  - operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md
  - operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md
  - operational_notes/07-26/15/2026-07-15_segment_resolved_pressure_thermal_modeling_plan.md
  - work_products/2026-07/2026-07-17/2026-07-17_predict_salt1_schema_promotion/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_salt2_pm5q_val_salt2_readiness_ledger/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock/README.md
tags: [thesis-dossier, latest-context, fluid-walls, split-policy, model-form, blockers]
related:
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/Outline.md
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-488
date: 2026-07-17
role: Writer
type: report
status: complete
---
# Thesis Dossier Latest Context Update

This note is the current-context bridge for the living thesis dossier. Older
slide outlines remain useful historical snapshots, but this is the July 17
context to carry into the thesis README, outline, and next presentation.

## Current Thesis Model Form

The target steady 1D model form is `fluid+walls`.

Each segment or branch region should carry geometry, material stack, pressure
model, thermal circuit, source/sink role, boundary-layer/development state,
recirculation/admission flags, and uncertainty status. This replaces any
implicit "fluid-only plus fitted heat leak" framing.

The current steady fluid energy balance is:

```text
d/ds[ mdot cp(T) T ] =
    q'_heater_to_fluid,i
  - q'_cooler_removed,i
  - q'_wall_loss,i
  + q'_other_source_to_fluid,i
```

No wall storage or transient heat-capacity term belongs in the present
steady-state thesis model. Storage/transient terms are future work unless a
later dated note reopens them.

The ordinary wall-loss path is:

```text
fluid bulk
  -> internal convection / thermal boundary layer
  -> pipe wall conduction
  -> insulation or local material layer
  -> external convection to ambient
  -> external radiation to surroundings
```

with a declared drive-temperature choice: bulk fluid, inner wall, pipe outer
wall, or insulation outer surface. Realized CFD `wallHeatFlux` is diagnostic or
scoring evidence only, not a predictive runtime input.

The test section is not deleted. It is the bare-quartz middle span of the
physical upcomer:

```text
left_lower_leg -> test_section_span -> left_upper_leg
```

Use a test-section form that computes the net sign:

```text
q'_test_section_to_fluid =
    q'_electrical_deposition_to_fluid_or_wall
  - (T_drive - T_external_drive) / R'_quartz_external
```

## Segment Pressure / Thermal Math

The compact root-solve shorthand is only a label. The thesis should avoid
implying a global `dp_drive(mdot)` or `dp_loss(mdot)` coefficient.

Buoyancy drive is an integral over the temperature/density/elevation field:

```text
Delta p_drive =
  integral_loop rho(T(s), p(s), composition, property_lane) g dz(s)
```

Pressure loss is segment-local:

```text
Delta p_loss =
  sum_i [
    f_i(Re_i, Pr_i, Ri_i, regime_i, roughness_i, geometry_i) (L_i/D_i) q_i
    + K_i(local_geometry_i, reset_i, development_i, regime_i) q_i
  ]
```

where `q_i = 0.5 rho_i V_i^2`. Different model forms are expected in heater,
cooler/HX, downcomer, upcomer, test section, lower/upper legs, and
junction/stub/connector regions.

## Current Final Predictive Split

The final predictive split is no longer Salt2 train / Salt3 validation /
Salt4 holdout. That older split remains a useful method-development snapshot
for dated scorecards only.

Current final policy:

| Role | Rows |
| --- | --- |
| final training | `salt1_nominal`, `salt2_jin_nominal`, `salt3_jin_nominal`, `salt4_nominal` |
| training support | `salt1_lo10q`, `salt1_hi10q`, `salt4_lo5q`, `salt4_hi5q` |
| holdout/testing | `salt2_lo5q`, `salt2_hi5q` |
| external test | `val_salt2`, after matching heat-loss/admission package |
| future holdout candidates | Salt2/Salt4 +/-10Q after terminal harvest/admission |
| new-CFD holdout candidates | Salt3 Q x insulation/onset matrix after run and admission |

Salt1 has now been schema-promoted for future final predictive training.
Salt2 +/-5Q remains holdout/testing-only. `val_salt2` remains external-test
only even though its heat ledger is training-quality as evidence.

## Current Blockers

Use `.agent/BLOCKERS.md` as authoritative. Current open blockers:

| Blocker | Thesis wording |
| --- | --- |
| `predictive-wall-test-section-submodels` | Heater and cooler/HX setup-only submodels are admitted as boundary evidence, but wall/test-section/passive-boundary heat loss is still not admitted. |
| `upcomer-onset-data-sparsity` | Current upcomer evidence is recirculating; onset remains extrapolated because non-recirculating or transition anchors are missing. |
| `f6-friction-re-correction` | F6 remains open but narrowed; current PM5 rows are recirculation diagnostics, not ordinary F6 fit evidence. Production remains `F3_shah_apparent`. |

Do not re-report these as open: `closure-qoi-mesh-gci`,
`thermal-cfd-1d-parity`, `predictive-heater-cooler-wall-submodels`,
`fluid-external-boundary-api-gap`, `refined-mesh-t-reconstruction-corruption`,
`of12-reconstructpar-segfault`, `no-mesh-for-gci`, or
`cfd-no-radiation-parity`.

## Current Claim Boundaries

- Strong: the thesis can defend a branchwise, provenance-controlled closure
  ledger rather than global fitted coefficients.
- Strong: the target 1D model is a steady `fluid+walls` segment ledger with
  explicit pressure, thermal, wall, boundary, source/sink, and admission slots.
- Strong: upcomer rows with material recirculation cannot be used to fit
  ordinary single-stream `Nu`, `f_D`, or `K`.
- Supported: Salt1 nominal is final-training evidence after schema promotion.
- Supported but not final: heater and cooler/HX setup-only submodels are
  admitted as boundary evidence; wall/test-section/passive-boundary modeling
  remains the active thermal boundary blocker.
- Diagnostic: M1/M1b/M2/M3 and imposed cooler-duty results explain model-form
  error, but any runtime use of CFD `mdot`, realized `wallHeatFlux`, imposed
  CFD cooler duty, or validation temperatures is not predictive evidence.
