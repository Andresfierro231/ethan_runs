# Ethan Internal Nusselt / HTC Model-Form Comparison

Generated: `2026-07-09`
Task: `AGENT-243`
Role: Coordinator / Writer

Tags: #thermal-parity #internal-nu #external-boundary #effective-htc
#model-form #litrev-synthesis #source-envelope

## Related

- `operational_notes/07-26/10/2026-07-10_NEXT_MEETING_START_HERE.md`
- `operational_notes/07-26/10/2026-07-10_thermal_parity_roadmap.md`
- `reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/README.md`
- `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/README.md`
- `operational_notes/07-26/13/2026-07-13_litrev_synthesis_start_here.md`
- `work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger/README.md`
- `work_products/2026-07/2026-07-09/2026-07-09_thermal_control_volume_admission_review/README.md`

## Short Answer

The OpenFOAM CFD does not prescribe an internal Nusselt-number correlation for
the salt-side heat transfer. It solves the internal velocity and temperature
fields with a laminar momentum model, Fourier thermal transport, tabulated
salt viscosity/conductivity, and wall thermal boundary conditions. Any
`Nu`, `h_i`, or internal convection coefficient quoted from the CFD side is
therefore a postprocessed effective quantity, not a CFD input closure.

The current 1D Fluid model is different. It explicitly closes the internal
convective resistance using a pipe-flow Nusselt correlation:

```text
Laminar:   Nu = max(4.36, 1.86 * (Re * Pr / (L/D))^(1/3)),  Re < 2300
Turbulent: Nu = 0.023 * Re^0.8 * Pr^0.4,                    Re >= 2300
h_i = M_i * Nu * k / D
R_i' = 1 / (h_i * pi * D)
```

where `M_i` is normally `1.0` in the baseline but may include direct per-segment
or profile-descriptor multipliers in CFD-informed scenarios.

On the outside walls, the OpenFOAM cases do not solve a resolved external air
domain. They use external-temperature style thermal boundary conditions with
prescribed external `h`, ambient/surroundings temperature, emissivity metadata,
and wall/layer resistance terms. That is a wall-boundary resistance model, not
a coupled outside-air convective CFD solve.

## Files In This Package

- `README.md`: paper-facing method comparison and scientific interpretation.
- `model_form_comparison.csv`: compact CFD-vs-1D table for later reference.
- `source_index.csv`: evidence map for every major claim.
- `summary.json`: machine-readable package metadata.

No new OpenFOAM extraction, Fluid rerun, solver-output mutation, or external
model edit was performed. This package consolidates existing code, dictionaries,
and July 2026 report products.

## Evidence Boundary

This report describes the current Ethan Salt comparison machinery, especially
the admitted mainline Salt 2/3/4 Jin continuation rows and the current external
Fluid solver lineage:

- CFD case-family evidence comes from readable OpenFOAM dictionaries under
  `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/`.
- CFD thermal diagnostics come from July 8 heat-ledger and transport outputs.
- 1D model-form evidence comes from
  `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/`.
- Current defended 1D setup context comes from the July 1 local 1D setup report.

Salt 1 nominal is still pending terminal admission evidence as of this package.
Corrected-Q perturbation rows remain sensitivity/correlation-support material,
not mainline predictive-validation rows.

## CFD Internal Heat Transfer: What Is Solved

### Governing Model Visible In The Dictionaries

The representative Salt 2 Jin continuation OpenFOAM case declares:

- `constant/momentumTransport`: `simulationType laminar`.
- `constant/thermophysicalTransport`: laminar thermal transport model
  `Fourier`.
- `constant/physicalProperties`: `heRhoThermo` with `sensibleEnthalpy`,
  tabulated incompressible-style transport (`icoTabulated`), polynomial density
  equation of state, constant heat capacity coefficients, and tabulated
  temperature-dependent `mu` and `kappa`.
- `0/U`: default wall type `noSlip`, with explicitly listed slip NCC neighbor
  patches.
- `0/T`: wall thermal boundary conditions such as `rcExternalTemperature`,
  `externalTemperature`, and `zeroGradient`.

In practical terms, the CFD resolves the internal velocity field, the internal
temperature field, and the wall-normal thermal gradient inside the computational
domain. The internal heat-transfer coefficient is not selected from a Dittus-
Boelter, Sieder-Tate, Graetz, or other explicit Nusselt formula in the case
setup. Instead, heat flux follows from the solved temperature gradient and the
local thermal conductivity.

Paper-facing wording:

> The CFD simulations solve the internal salt-side thermal field directly using
> laminar momentum and Fourier heat transport with temperature-dependent salt
> properties. Salt-side Nusselt numbers are not imposed as closure correlations;
> any Nusselt or internal heat-transfer coefficient reported from CFD is an
> effective diagnostic reconstructed from wall heat flux and representative
> wall-to-bulk temperature differences.

### What The Outside Wall Boundary Does

The `0/T` dictionary shows external-temperature style wall boundary conditions.
For `rcExternalTemperature` rows, the boundary metadata include prescribed
external heat-transfer coefficient `h`, ambient air temperature `Ta`,
surroundings temperature `Tsur`, emissivity, internal radius, layer thicknesses,
layer conductivity coefficients, layer density coefficients, layer heat-capacity
coefficients, and `steadyWall true`.

This is not a resolved external-air computational domain. There is no separate
mesh around the loop that solves outside-air momentum, thermal plumes, fan
mixing, room recirculation, or radiation view factors as volume fields. The
external side is represented by boundary-condition data and thermal resistance
terms. The July 8 boundary reference further records that the audited Salt CFD
rows preserve emissivity metadata but have no exported `qr` or `G` radiation
field in the current heat ledger.

Paper-facing wording:

> The OpenFOAM cases use wall thermal boundary conditions with prescribed
> external convection and layer-resistance metadata. They should not be
> described as solving coupled convective heat transfer in the surrounding air.
> The internal fluid domain is solved, while the external environment enters as
> boundary data.

## CFD Effective Nu / HTC: What Is Postprocessed

Several repo products compute effective thermal quantities from CFD fields.
Those quantities are diagnostics. They are useful for interpreting why the 1D
model succeeds or fails, but they are not the equations used by OpenFOAM during
the solve.

The July 8 patchwise heat ledger reconstructs an internal effective convection
coefficient as:

```text
DeltaT_internal = T_wall_mean - T_bulk_span
h_eff = wallHeatFlux_mean / DeltaT_internal
R_eff = 1 / h_eff
```

The June 10 and June 15 streamwise/branch transport tables similarly report
columns such as `mean_effective_htc_w_m2_k`, `mean_effective_ua_per_m_w_m_k`,
and effective thermal resistance. If desired, an effective Nusselt number can
be formed from those diagnostics as:

```text
Nu_eff = h_eff * D_h / k_bulk
```

but that conversion requires a consistent diameter, bulk-temperature, and
fluid-conductivity convention. The present package does not create a new Nu
table because no new extraction or uncertainty pass was performed.

Important caveats:

- The effective `h_eff` can be sign-sensitive when wall heat flux and
  `T_wall - T_bulk` have opposite signs.
- Small wall-to-bulk temperature differences can inflate or destabilize
  inferred `h_eff`.
- Patch support and recirculation affect the meaning of a single bulk
  temperature, especially in the upcomer.
- The current closure-quality notes state that apparent `Nu`/`UA`/`HTC`
  closures still lack a three-grid discretization-error bound.
- A CFD effective HTC includes local three-dimensional development, bends,
  buoyancy, secondary flow, and nonlocal wall-boundary effects. It is not
  identical to a clean pipe-correlation HTC.

## 1D Internal Nu / HTC Model

### Baseline Correlation

The current external Fluid solver implements `internal_nusselt(Re, Pr, L_over_D)`
in `tamu_loop_model_v2/solver.py`. The function uses:

```text
Re_eff = max(Re, small)
Pr_eff = max(Pr, small)

if Re < 2300:
    Nu_fd  = 4.36
    Nu_dev = 1.86 * (Re_eff * Pr_eff / max(L/D, small))^(1/3)
    Nu     = max(Nu_fd, Nu_dev)
else:
    Nu     = 0.023 * Re_eff^0.8 * Pr_eff^0.4
```

The laminar branch combines a fully developed constant-wall-flux value
(`Nu = 4.36`) with an entry/developing-flow correction. The turbulent branch is
a Dittus-Boelter-style power law. The implemented laminar developing term does
not include an explicit viscosity-ratio wall correction.

For each normal ambient-loss segment, the solver computes:

```text
Re = rho * v * D_i / mu
Pr = cp * mu / k
Nu_i = internal_nusselt(Re, Pr, L/D_i)
h_i = M_i * Nu_i * k / D_i
R_i' = 1 / (h_i * pi * D_i)
```

Then `R_i'` is placed in series with the pipe-wall, insulation, external
convection, and optional radiation resistances to obtain a per-length heat-loss
path. The segment energy balance is marched as:

```text
T_out = T_in + (Q_source - Q_hx_sink - Q_ambient) / (mdot * cp)
```

### Heat Exchanger Use Of The Same Correlation

For a segment marked as the heat exchanger in `predictive_airside_hx` mode, the
solver applies the same `internal_nusselt` function to the salt side and also
uses it for the annular air-side hydraulic diameter. The HX calculation builds
salt-side, wall, and air-side resistances, converts them to `UA`, then uses an
epsilon-NTU relation to predict cooler duty.

This is central to the July 8 slide-6 issue: the baseline/current 1D model's
predicted cooler duty is controlled by the 1D HX resistance model and air-side
boundary inputs, whereas the CFD cooler duty comes from the OpenFOAM wall heat
flux at the cooler boundary. A replay that prescribes CFD cooler duty is a
diagnostic comparison, not the baseline predictive 1D model.

### Multipliers And CFD-Informed Thermal Model Forms

The baseline internal HTC path has `internal_htc_mode = baseline`, so the direct
multiplier is `M_i = 1.0`.

The solver also supports `internal_htc_mode = per_parent_multiplier`, which
looks up a positive multiplier by resolved parent segment or segment name.
This is a direct way to inject branchwise CFD-informed HTC factors.

Separately, the profile-descriptor path can multiply HTC with shape/developing
signals. In the current implementation:

```text
developing_signal = exp(-local_x_over_d / decay_x_over_d)
profile_multiplier =
    max(0.1, 1 + htc_gain * htc_shape_weight * htc_shape_signal
             + htc_gain * htc_developing_weight * developing_signal)

M_i = manual_internal_htc_multiplier * profile_multiplier
```

The July 1 setup report identifies the defended local scenario as
`ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, active mode
`predictive_airside_hx`, base `1.0 in` insulation, radiation enabled, and no
hybrid branchwise outer-loss multipliers in the defended winner. It also records
that the direct internal thermal-law evidence was limited to `left_lower_leg`,
while broader thermal closure support lived in a profile-library lane over
`left_lower_leg`, `test_section_span`, `left_upper_leg`, and `upcomer`. The
right leg/downcomer, cooler return, and feature losses remained unsupported or
calibration-only lanes.

## Why CFD/1D Agreement Behaves The Way It Does

### 1. The Models Are Solving Different Thermal Closure Problems

The CFD resolves local wall gradients and local three-dimensional flow. Bends,
inclines, buoyancy, local acceleration/deceleration, developing boundary layers,
and recirculation can all alter the wall heat flux without appearing as a
single pipe-correlation parameter.

The 1D model collapses each segment to a bulk stream temperature and a scalar
internal resistance. Its baseline Nusselt correlation assumes idealized internal
pipe-flow behavior. It can represent development through `L/D`, but it cannot
directly resolve cross-section distortion, secondary flow, local buoyancy cells,
or asymmetric wall heating/cooling.

Expected consequence:

> Agreement is best where the flow behaves like a single stream with a stable
> bulk temperature and the wall heat transfer is dominated by ordinary
> developing pipe behavior. Agreement weakens where three-dimensional
> recirculation, bend-induced mixing, local wall-boundary roles, or external
> boundary mismatch dominate.

### 2. The Current Largest Temperature Error Is Not Purely Internal Nu

The July 8 thermal replay showed that prescribing the CFD cooler duty largely
collapses the fixed-mdot mean loop-temperature error. That means a major part
of the current temperature disagreement is the cooler/HX boundary closure, not
just a salt-side internal-Nu mismatch.

Scientific interpretation:

> Internal Nu matters for distributing wall-to-bulk temperature resistance and
> local heat transfer, but the current largest loop-temperature offset is
> dominated by the difference between the 1D predicted air-side HX duty and the
> realized CFD cooler wallHeatFlux. Therefore, fitting only internal Nu without
> fixing the cooler boundary can give misleading agreement.

### 3. The CFD Effective HTC Is A System Diagnostic

When an effective CFD `h_eff` is calculated from `wallHeatFlux/(T_wall -
T_bulk)`, the result includes everything that made the local wall flux and bulk
temperature what they are: mesh support, local geometry, wall boundary
condition, recirculation, thermal development, and the definition of bulk
temperature. It is not guaranteed to be the same as a textbook convective HTC.

Scientific interpretation:

> CFD-inferred HTC should be used as a closure-observation diagnostic only after
> support, sign, bulk-temperature, and mesh-uncertainty gates are passed. It is
> stronger evidence for local model inadequacy than it is for a universal Nu
> law.

### 4. The 1D Baseline Is Physically Transparent But Under-Expressive

The baseline 1D Nu model is transparent: one can compute `Re`, `Pr`, `L/D`,
`Nu`, `h_i`, and `R_i'` at every segment. That is good for a paper because the
model form is reproducible and falsifiable. Its weakness is that it has no
native representation of branch-to-branch CFD spread unless multipliers or
profile descriptors are enabled.

Scientific interpretation:

> The baseline should be presented as the current physically transparent
> reference model, not as a claim that the loop behaves like fully developed
> straight pipe everywhere. CFD-informed multipliers/profile descriptors are
> candidate corrections, but they need admission gates and uncertainty bounds
> before they become final predictive closures.

### 5. Mesh And Admission Gates Still Limit Paper Claims

The repo's GCI tooling explicitly notes that apparent `f` and `Nu`/`UA`/`HTC`
closures currently carry no discretization-error bound until a three-grid study
is available. This matters for paper wording. A coarse CFD effective Nu table
can support mechanism and model-form diagnosis, but it should not be treated as
a final validated closure law without mesh-UQ support.

## Current Paper-Ready Position

Use this wording, or a close variant, in the manuscript/report:

> The OpenFOAM simulations resolve the internal salt-side velocity and
> temperature fields with laminar momentum transport and Fourier heat transport
> using temperature-dependent salt properties. No internal Nusselt correlation
> is imposed in the CFD. Salt-side Nusselt numbers and heat-transfer
> coefficients are therefore reported only as effective postprocessed
> quantities reconstructed from wall heat flux and representative wall-to-bulk
> temperature differences. In contrast, the 1D model closes internal convection
> explicitly with a pipe-flow Nusselt correlation, using a laminar
> fully-developed/developing maximum below `Re = 2300` and a Dittus-Boelter-style
> turbulent branch above that threshold. The resulting `h_i = Nu k / D`, with
> optional CFD-informed multipliers, enters a series thermal-resistance model
> for wall, insulation, external convection, and radiation. Disagreement
> between the two models should therefore be interpreted as a combination of
> internal thermal-development effects, three-dimensional flow effects,
> external boundary/HX closure differences, and postprocessing support limits,
> not as a one-to-one failure of a single Nu correlation.

For the external boundary:

> The OpenFOAM cases do not solve a coupled outside-air convective domain.
> External heat exchange enters through wall thermal boundary conditions with
> prescribed external heat-transfer coefficients, ambient/surroundings
> temperatures, layer resistance metadata, and emissivity metadata. The
> resolved CFD domain is the internal loop fluid plus its wall boundary
> treatment, while the external environment is parameterized.

## Recommended Fixes For The Analysis Stack

1. Keep the slide/report labels readable:
   `Baseline current 1D`, `CFD cooler duty only`, and
   `CFD cooler + heater flux` are preferable to `P0`, `P1`, etc.

2. Do not label a CFD effective HTC plot as "the CFD Nu model." Use
   `CFD-inferred effective HTC/Nu` or `postprocessed wall-flux HTC`.

3. Separate three comparison axes:
   baseline predictive 1D, CFD-cooler-duty replay, and CFD-cooler-plus-heater
   interface replay.

4. For paper tables, report both model-form equations and evidence status:
   baseline correlation, direct per-parent HTC multipliers, profile-descriptor
   multipliers, and CFD-inferred effective HTC should not be blended into one
   label.

5. Before final closure claims, add a mesh/UQ row for effective `Nu`/`UA`/`HTC`
   or explicitly mark the closure as coarse/no-GCI diagnostic.

6. For HX-focused comparisons, keep cooler duty separate from internal Nu.
   The current temperature agreement behavior strongly suggests that the HX
   boundary/duty mismatch is a first-order issue.

## Compact Reference

See `model_form_comparison.csv` for a row-by-row comparison of the CFD and 1D
forms. See `source_index.csv` for the exact evidence map.
