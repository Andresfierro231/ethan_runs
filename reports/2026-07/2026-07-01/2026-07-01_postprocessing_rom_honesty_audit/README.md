# CFD Post-Processing and ROM Honesty Audit

Date: `2026-07-01`  
Task: `AGENT-163`  
Role: Coordinator / Writer / Reviewer  
Status: paper-facing internal note; no new CFD results

## Purpose

This note audits whether the current CFD post-processing and 1D reduced-order
model (ROM) closure workflow is scientifically honest enough to support thesis
and paper work. It focuses on five concerns:

1. geometry provenance and whether another agent can reconstruct what physical
   segment a number belongs to;
2. pressure reduction, especially `p_rgh`, absolute pressure, total pressure,
   and the risk of interpreting buoyancy residuals as friction;
3. heat-transfer quantities (`HTC`, `UA'`, `R'_thermal`, `Nu`) and whether their
   reference temperatures and sign conventions are defensible;
4. closure fitting, correlation language, and uncertainty/error accounting;
5. reusable scripts needed to compare many model forms for the master's thesis.

This is an audit and methods note. It does not run OpenFOAM, does not modify
native solver outputs, and does not replace the active mesh-centerline
extraction task.

## Sources Reviewed

Primary evidence:

- `.agent/journal/2026-07-01/T1-mesh-centerlines-geometry-refix.md`
- `operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md`
- `operational_notes/06-26/30/2026-06-30_mesh_geometry_vs_probe_csv_provenance.md`
- `operational_notes/06-26/30/2026-06-30_cfd_1d_closure_workflow.md`
- `operational_notes/06-26/30/2026-06-30_thermal_extraction_spec.md`
- `operational_notes/06-26/30/2026-06-30_next_scope_branch_closures_and_cfd_design.md`
- `operational_notes/06-26/30/2026-06-30_upcomer_convection_cell_model.md`
- `operational_notes/06-26/30/2026-06-30_downcomer_closure_analysis.md`
- `.agent/journal/2026-06-30/claude-inspection-cfd-1d-closure-postprocessing.md`
- `.agent/journal/2026-06-30/perturbation-run-convergence-audit.md`
- `.agent/journal/2026-06-30/1d-model-status-and-plan.md`
- `reports/2026-06/2026-06-30/2026-06-30_claude_closure_results/README.md`
- `reports/2026-06/2026-06-30/2026-06-30_3d_to_1d_field_reduction_methods/README.md`
- `tools/extract/sample_section_mean_pressure.py`
- `tools/analyze/derive_segment_friction.py`
- `tools/extract/sample_segment_htc_uaprime.py`
- `tools/extract/sample_upcomer_convection_cell.py`
- `tools/analyze/represent_closures_per_case.py`
- `tools/analyze/compute_gci.py`
- `tools/analyze/build_ethan_1d_closure_bakeoff.py`
- `tools/analyze/build_ethan_salt_pressure_drop_predictivity.py`
- `tools/analyze/build_ethan_1d_discrepancy_explainer_latest_window.py`

## Executive Finding

The post-processing stack has moved past the most serious early mistakes:
section-mean pressure exists, dynamic head is carried, mesh-derived geometry is
now available, and thermal extraction uses an enthalpy-flux bulk temperature.
The remaining risk is subtler and more important for publication: we must stop
using single formulas outside their valid assumptions.

The mainline statement should be:

- Current Salt 2/3/4 Jin continuations are useful coarse-mesh, laminar,
  stationary CFD anchors.
- Existing fitted surfaces are narrow operating-point calibrations, not
  transferable correlations.
- The upcomer is not an ordinary friction segment; it contains a buoyancy-driven
  recirculation cell.
- Heated/cooled non-isothermal leg pressure gradients require a variable-density
  buoyancy correction before they can be interpreted as pure friction.
- No `f`, `Nu`, or `UA'` coefficient is paper-grade without mesh/GCI uncertainty.
- Perturbation runs and postponed scaling jobs must not be silently folded into
  the evidence base.

## Geometry Contract

### Current state

The authoritative geometry is now the mesh, not `tp_tw_probe_locations.csv`.
The schematic probe CSV is useful for historical labels, but it is not a
geometry source. The mesh-centerline journal reports:

- heater/lower leg: about `21.5 deg` from horizontal;
- cooler/upper leg: about `22 deg` from horizontal;
- test section: vertical, smaller bore around `20.9 mm`;
- other pipe legs: about `22.1 mm` bore;
- endpoint stations near fittings can show distorted apparent bore/inclination.

This matters because pressure gradients, buoyancy projections, and mixed
convection groups depend on local tangent and bore. A table of `span`, station,
`s`, tangent, inclination, `A`, wetted perimeter, and `D_h` should be the
geometry contract consumed by every downstream extractor.

### Recommended paper definition

For each station `i` on a span:

```text
x_i        = section center point
t_i        = unit tangent in downstream 1D direction
s_i        = cumulative arc length
A_i        = masked cross-section area
P_i        = wetted perimeter or measured section perimeter
D_h,i      = 4 A_i / P_i
theta_i    = angle between t_i and gravity or horizontal, explicitly stated
valid_i    = mask/alignment/fitting-end quality flag
```

The section mask is:

```text
keep face f if ||(I - t_i t_i^T)(x_f - x_i)|| < r_mask
```

with a flow-coherence gate:

```text
alignment_i = ||mean(U_f)|| / mean(||U_f||)
```

Stations with low alignment or fitting-end flags are not straight-leg closure
stations. They may still be useful for bend/junction work if treated as feature
stations, not distributed friction stations.

### Required documentation improvement

The report and future scripts should publish a `geometry_reference.csv` or JSON
beside every closure package. Minimum columns:

```text
source_id, span, station, s_m, x_m, y_m, z_m,
tx, ty, tz, inclination_from_horizontal_deg,
A_m2, P_m, D_h_m, bore_class, is_fitting_end,
geometry_source, quality_flag
```

This is the simplest way to make the geometry legible to future agents.

## Pressure Reduction

### Definitions

Let `s` be downstream arc length and `t = dx/ds` the downstream unit tangent.
Let

```text
psi(x) = g dot (x - x_ref)
p_rgh  = p - rho psi
q_dyn  = 0.5 rho U_b^2
p0_rgh = <p_rgh>_A + q_dyn
```

where `<.>_A` is a section average over a single-leg cut and `U_b` is the bulk
through-flow speed. The current `sample_section_mean_pressure.py` reports
section-mean `p_rgh`, `rho`, `U_b`, `q_dyn`, `p0_rgh`, measured area, and
`D_h`. That is the right data surface.

### Why `p_rgh` gradients are not always friction

For constant density, the hydrostatic part cancels cleanly and a downstream
decrease in `p0_rgh` can be interpreted as mechanical loss. For variable density,
the derivative contains an additional buoyancy/source term:

```text
p = p_rgh + rho psi
d(p + q_dyn)/ds = d(p_rgh + q_dyn)/ds + rho dpsi/ds + psi drho/ds
```

The mechanical loss after subtracting the local gravity work is therefore:

```text
loss'_mech = -[ d(p + q_dyn)/ds - rho dpsi/ds ]
           = -d(p_rgh + q_dyn)/ds - psi drho/ds
```

Equivalently, in a Boussinesq-style local form, the non-reference density
contribution appears as a streamwise buoyancy source proportional to
`rho' g dot t`. The exact sign must be pinned to the OpenFOAM `gh` convention
with a manufactured hydrostatic-column test, but the scientific conclusion is
not ambiguous: on heated or cooled non-isothermal legs, a raw `p_rgh` or
`p0_rgh` slope is not automatically a Darcy friction loss.

This explains the current T1 observation that some heated/cooled legs can
produce negative apparent friction while clean isothermal or weakly buoyant
segments remain sensible. The next extractor step should compute and report:

```text
dp0rgh_ds               = d(<p_rgh> + q_dyn)/ds
buoyancy_density_term   = psi drho/ds        or a locally equivalent rho' g dot t term
mechanical_loss_ds      = -dp0rgh_ds - buoyancy_density_term
f_D                     = 2 D_h mechanical_loss_ds / (rho U_b^2)
```

The older static-only pressure route should remain as a diagnostic, not a
closure source.

### Absolute pressure

Absolute pressure is useful for solver consistency and reconstructing
mechanical-energy terms, but the ROM should not fit friction directly to raw
absolute pressure drops around a buoyancy loop without explicitly accounting for
gravity and density variation. The hierarchy should be:

1. reconstruct or sample `p`, `p_rgh`, `rho`, and `U`;
2. derive section means on single-leg cuts;
3. form total pressure including dynamic head;
4. remove reversible/gravity/buoyancy terms according to the 1D balance;
5. only then fit distributed loss or feature loss.

### Pressure along the loop

For paper and agent reuse, a loop-pressure table should use one row per station:

```text
source_id, station, span, s_m,
z_or_psi_m2_s2, rho_kg_m3,
p_abs_pa, p_rgh_pa, q_dyn_pa, p0_rgh_pa,
dp0rgh_ds_pa_per_m, buoyancy_term_pa_per_m,
mechanical_loss_pa_per_m,
quality_flag
```

Plots should show at least three curves: `p_rgh`, `q_dyn`, and `p0_rgh`, with
feature stations visually separated from straight-span stations. A fourth
curve, `mechanical_loss` accumulated along `s`, is the one that maps most
directly to ROM hydraulic loss.

## Friction Closure

For a straight, coherent through-flow segment, Darcy friction is defined by:

```text
loss'_mech = f_D (1/D_h) (0.5 rho U_b^2)
f_D        = 2 D_h loss'_mech / (rho U_b^2)
Re         = rho U_b D_h / mu(T_b)
f_lam      = 64 / Re
```

The current `derive_segment_friction.py` correctly reports Darcy, not Fanning,
and compares against `64/Re`. It also reports negative apparent friction rather
than clamping it. That is good scientific hygiene.

The missing publication step is to distinguish three categories:

- `direct_friction`: clean through-flow, density/buoyancy correction applied,
  station set excludes fitting ends, mesh uncertainty carried;
- `apparent_resistance`: useful for ROM calibration but includes bends,
  redevelopment, buoyancy residuals, or section noise;
- `invalid_single_f`: recirculating or cell-dominated sections where one Darcy
  factor is not a physically meaningful closure.

The upcomer belongs in `invalid_single_f` for the current cases because the
single-leg velocity sections show substantial backflow. The downcomer appears to
be clean through-flow in the current coarse data, but it still needs right-leg
Ri/Ra sampling and mesh uncertainty before coefficients are publishable.

## Thermal Closure

### Correct bulk temperature

For a section `S`, the mixed-mean temperature must preserve advected enthalpy:

```text
T_b = integral_S rho u_n cp(T) T dA
    / integral_S rho u_n cp(T) dA
```

The signed normal velocity `u_n = U dot t` should be retained. Reverse-flow
faces are part of the enthalpy balance; dropping them biases recirculating
sections. `sample_segment_htc_uaprime.py` now implements this enthalpy-flux
definition, which fixes an important older weakness.

### Conductance definitions

Use a clearly stated heat-to-fluid convention. If OpenFOAM wallHeatFlux is
stored as positive outward from the fluid, define:

```text
q''_f      = -q''_OF
q'_f       = Q_f / L
DeltaT_f   = T_wall - T_b
h          = q''_f / DeltaT_f
UA'        = q'_f / DeltaT_f
R'_thermal = 1 / UA'
Nu         = h D_h / k(T_b)
```

If the script reports solver-signed flux instead, it must also report the
physics-positive transformed value. Publication tables should avoid ambiguity by
including:

```text
wall_flux_sign_convention, q_of_wm2, q_to_fluid_wm2,
T_wall_k, T_bulk_k, deltaT_wall_minus_bulk_k,
h_wm2k, UAprime_wmk, Rprime_mk_w, Nu
```

The current thermal extractor has the right mathematical structure, but a final
paper table should include an explicit sign audit for each segment. A positive
conductance should mean that heat moves from hot side to cold side under the
chosen convention; it should not depend on the solver's raw sign.

### Where HTC/Nu are meaningful

`h` and `Nu` are local/segment heat-transfer coefficients only when the section
has a meaningful bulk through-flow and the wall-fluid temperature difference is
well conditioned. For recirculating upcomer sections, `UA'` may still be useful
as an effective ROM conductance, but calling the result a transferable forced
convection `Nu(Re,Pr)` law is not honest.

Use this policy:

- `UA'`: primary ROM thermal surface, because the 1D energy equation consumes
  conductance per length directly.
- `h`: secondary diagnostic requiring a stated wetted perimeter and sign
  convention.
- `Nu`: regime-specific diagnostic or direct closure only where a Nusselt law is
  physically identifiable.
- `R'_thermal = 1/UA'`: useful for resistance-network interpretation and error
  comparison.

## Correlation Honesty

The current Salt closures should be described as narrow laminar calibrations.
They are not broad correlations. Reasons:

- only a few physically distinct mainline Salt Jin operating points are
  available;
- the flow is deeply laminar;
- Re and Pr are largely collinear over the available salt window;
- mesh uncertainty is not yet quantified;
- upcomer recirculation has only seed/onset evidence and no cell-off point;
- perturbation runs are false-steady until requalified.

A defended correlation must state:

```text
training_case_count
physical_case_count
free_parameter_count
degrees_of_freedom
valid Re/Ri/Ra/Pr range
mesh level and GCI band
convergence gate
holdout or leave-one-case-out error
domain-clamp behavior
extrapolation policy
```

Recommended language:

- say `calibration` for current `f(Re)` and `Nu(Re)` fits;
- reserve `correlation` for a fit with enough independent physical cases and
  uncertainty bounds;
- reserve `closure law` for the final ROM-facing functional form with domain
  guards and residual accounting.

## Error and Uncertainty Policy

A rigorous ROM comparison must separate these error sources:

| Error source | Symbol / metric | Required treatment |
| --- | --- | --- |
| time convergence | trailing slope, heat-balance residual, mdot stationarity | gate before extraction |
| false-steady restart | operating-point movement from baseline | required for perturbation runs |
| mesh/discretization | GCI, Richardson extrapolated QoI | required before paper-grade coefficients |
| geometry | `D_h`, `A`, tangent, inclination uncertainty | publish geometry table and flags |
| pressure reduction | buoyancy-correction residual, static-vs-total split | report terms separately |
| property model | Jin/Kirst or parameter sensitivity | keep as sensitivity, not fitted Re spread |
| extraction noise | station count, alignment, fitting-end flags | carry row-level quality flags |
| model-form error | residuals against CFD QoIs | compare candidate forms on same data |
| parameter uncertainty | confidence/prediction intervals where identifiable | do not report fake intervals with zero DOF |

For the master's thesis, each candidate ROM model form should be scored against
the same target vector:

```text
y = [mdot, branch heat duties, wall-temperature profile, centerline/bulk T,
     accumulated pressure loss, segment pressure residuals]
```

Use both absolute and nondimensional errors:

```text
e_i          = y_model,i - y_CFD,i
relative e  = e_i / scale_i
RMSE         = sqrt(mean(e_i^2))
MAE          = mean(|e_i|)
bias         = mean(e_i)
max error    = max(|e_i|)
weighted J   = sum_i w_i (e_i/scale_i)^2
```

The scale must be physical, not convenient:

- mass flow: CFD `|mdot|` or nominal design `|mdot|`;
- heat: heater gross duty;
- temperature: imposed loop temperature rise or wall/bulk spread;
- pressure: total loop buoyancy drive or accumulated mechanical loss.

When case count is small, report leave-one-physical-case-out error rather than
only in-sample `R^2`. `R^2` with one or zero degrees of freedom is a fit
artifact, not validation.

## Reusable Script Architecture

The current scripts are valuable but fragmented. To support thesis-scale
model-form comparison, create a common observation table and a model-form bakeoff
interface.

### Common observation table

Each extraction tool should emit or be adaptable into:

```text
closure_observations.csv
```

Minimum columns:

```text
source_id, case_family, mesh_level, time_window,
span, segment_1d, station_or_segment, s_start_m, s_end_m,
quantity, value, units,
geometry_source, pressure_method, thermal_method,
convergence_status, mesh_status, quality_flag,
valid_for_fit, valid_for_validation, caveat
```

This lets the ROM bakeoff consume the same data structure regardless of whether
the candidate model uses friction factors, minor-loss `K`, `UA'`, direct `Nu`,
or an upcomer recirculation law.

### Candidate model-form spec

Use a small JSON/YAML spec for each model form:

```text
model_id
target_quantity
functional_form
features_used
fit_scope
domain_guards
fixed_parameters
free_parameters
training_cases
validation_cases
```

Examples:

- `f_D = C/Re` with branch-specific `C`;
- `f_D = a Re^b` with branch-specific fit;
- `K_bend = constant` by feature class;
- `UA' = constant per segment`;
- `UA' = a Re^b`;
- `backflow_fraction = bf_max / (1 + (Ri_crit/Ri)^k)`;
- hybrid upcomer switch: ordinary through-flow below `Ri_crit`, cell model
  above `Ri_crit`.

### Bakeoff outputs

Every model-form comparison should produce:

```text
fit_parameters.csv
case_predictions.csv
case_error_summary.csv
model_error_summary.csv
domain_guard_violations.csv
README.md
summary.json
```

The existing bakeoff scripts already compute some of these error surfaces. The
next improvement is to make the input closure observations and model specs
explicit so a future agent can add or remove a model form without rewriting a
bespoke analysis script.

## Analysis Left On The Table

Highest value next tasks:

1. **Pressure buoyancy correction.** Add the variable-density correction to
   section-mean pressure-derived friction and rerun Salt 2/3/4 Jin continuations.
2. **Geometry reference artifact.** Publish mesh-derived `geometry_reference`
   with every closure package.
3. **Right-leg nondimensional sampling.** Extend convection-cell sampling to
   right_leg/downcomer to quantify reversal margin rather than only observing
   zero backflow.
4. **Minor-loss extraction.** Use two-tap total-pressure loss around bends and
   reducers after subtracting adjacent straight friction.
5. **Mesh/GCI.** Run the medium/fine study when compute is available; until then
   all coefficients remain coarse-mesh.
6. **Perturbation requalification.** Do not use existing Q/insulation variants
   until they demonstrate operating-point movement and true new steady states.
7. **Upcomer onset envelope.** Need cell-off and maximum-cell points; current
   three nominal cases are seed evidence only.
8. **Downcomer thermal unblock.** Existing evidence suggests coherent
   through-flow, so direct `UA'`/indicative `Nu` can be considered after policy
   update and uncertainty labeling.
9. **Model-form bakeoff interface.** Build the common observation/model-spec
   layer for thesis comparisons.

## Scaling And Deferred Compute Notes

The scaling lane is deferred and must not be used as evidence for scientific
claims. The current scaling note records the canceled rank pilot and I/O
follow-up. The user also asked to remember that another scaling job from
`2026-06-30` should be resubmitted when the scaling study reopens; because that
operational note is owned by the active AGENT-162 row, this audit records the
reminder here rather than editing that file.

Scientific compute still needed is not the same as scaling optimization:

- mesh/GCI runs are needed for uncertainty;
- perturbation continuations are needed for correlation domain expansion;
- scaling jobs are only runtime optimization and can stay postponed.

## Bottom Line For The Paper

The honest 1D model story is not that CFD has already delivered universal
correlations. The honest story is:

1. the 3D CFD identifies which reduced physics are needed by branch;
2. the ROM should consume direct, section-mean, geometry-corrected quantities
   where assumptions hold;
3. recirculating regions need different closure structure from clean through-flow
   legs;
4. current coefficients are coarse-mesh calibrations with explicit validity
   windows;
5. scientific progress comes from shrinking the residual with traceable
   corrections and reporting the remaining error, not from hiding uncertainty in
   fitted constants.

That framing is defensible for a thesis: it explains why the existing 1D model
is useful, where it is not yet predictive, and what data or derivation is needed
to move from calibration toward correlation.
