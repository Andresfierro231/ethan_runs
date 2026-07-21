# 3D-to-1D Field-Reduction Methods

Date: 2026-06-30

## Purpose

This report documents how the Ethan OpenFOAM 3D CFD fields are reduced into
1D profiles, section values, and closure inputs suitable for paper-facing
analysis. It is a methods report, not a new numerical result package.

The short answer to the zone/set question is:

- Yes, native OpenFOAM `faceZones`, `cellZones`, and `sets` are used when
  they encode physically meaningful monitor surfaces or regions. In the
  inspected Salt 2 Jin case, the `sets/` directory includes mdot `faceSet`
  objects and one `cellSet` object (`piv_slab`).
- No, they are not sufficient by themselves for the full 3D-to-1D reduction,
  because the paper-grade profiles require ordered streamwise coordinates,
  wall-patch membership, flow-direction signs, cross-section masks, and QC
  gates that are not fully encoded in the native mesh zones.

The current robust path is therefore a hybrid:

1. preserve and use native OpenFOAM zones/sets where they are authoritative;
2. use the case-analysis profile as the 1D coordinate contract;
3. sample/reconstruct fields on that coordinate;
4. reduce fields with explicit area, mass-flux, enthalpy-flux, and pressure
   definitions;
5. publish quality flags and confidence boundaries next to every derived
   closure quantity.

## Primary Sources

- `tools/case_analysis_profiles.py`
- `tools/extract/sample_leg_centerline_major_loss.py`
- `tools/extract/sample_section_mean_pressure.py`
- `tools/extract/sample_segment_htc_uaprime.py`
- `tools/analyze/derive_segment_friction.py`
- `reports/2026-06/2026-06-17/2026-06-17_ethan_streamwise_transport_math_reference/MATH_COMPANION.md`
- `reports/2026-06/2026-06-29/2026-06-29_ethan_reduction_contract_audit/README.md`
- `operational_notes/06-26/30/2026-06-30_cfd_to_1d_segment_map.md`
- `operational_notes/06-26/30/2026-06-30_cfd_1d_closure_workflow.md`

## Native Zones And Sets

The current Salt 2 Jin continuation mesh contains the following relevant native
OpenFOAM selection structures:

- `constant/polyMesh/faceZones`: four mass-flow monitor planes:
  `mdot_pipeleg_lower_05_straight`, `mdot_pipeleg_right_02_middle`,
  `mdot_pipeleg_left_04_test_section`, and `mdot_pipeleg_upper_05_cooler`.
- `constant/polyMesh/sets`: the same four mdot monitor selections as
  `faceSet` objects plus `piv_slab` as a `cellSet`.
- `constant/polyMesh/cellZones`: 33 cell zones, mostly geometry/topology
  regions such as junctions and pipe components.

These structures help in three ways:

1. They provide stable monitor surfaces for flow-rate validation.
2. They encode some authored geometric regions directly in the mesh.
3. They give provenance anchors: a reduction can say whether a field value came
   from a native monitor, an authored wall patch list, or a derived cut plane.

They do not solve the full 1D reduction problem because the target 1D model
requires ordered segment quantities along the loop. A zone named for a physical
part does not automatically define a monotone streamwise coordinate, a local
tangent, an upstream/downstream order, a wall perimeter, or a clean single-leg
cross-section.

## 1D Coordinate Contract

The 1D coordinate is defined in `tools/case_analysis_profiles.py`, not inferred
from raw mesh zones alone. For the Salt-family profile, six major spans are
declared:

| CFD span | Station labels | Native monitor support |
| --- | --- | --- |
| `lower_leg` | `TP1`, `TW1`, `TW2`, `TW3`, `TP2` | `mdot_pipeleg_lower_05_straight` |
| `right_leg` | `TP2`, `TW4`, `TW5`, `TW6`, `TP3` | `mdot_pipeleg_right_02_middle` |
| `left_lower_leg` | `TP3`, `TW7`, `TP4` | none |
| `test_section_span` | `TP4`, `TP5` | `mdot_pipeleg_left_04_test_section` |
| `left_upper_leg` | `TP5`, `TW8`, `TP6` | none |
| `upper_leg` | `TP6`, `TW11`, `TW10`, `TW9`, `TP1` | `mdot_pipeleg_upper_05_cooler` |

Each span carries:

- ordered centerline labels;
- wall patch membership;
- a flow-direction sign hint;
- optional mdot face-zone support;
- start/end patch metadata.

The locked CFD-to-1D semantic map is:

- `lower_leg` = heated leg, also the `heated_incline` target in the 1D closure
  map;
- `right_leg` = downcomer;
- `upcomer` = `left_lower_leg` + `test_section_span` + `left_upper_leg`;
- `upper_leg` = cooled leg.

This mapping is required because similar names such as `lower_leg` and
`left_lower_leg` refer to different physical roles. A paper result should cite
this segment map whenever it reports fitted closure terms by 1D segment.

## Field Preparation

The OpenFOAM cases are decomposed continuation runs, typically under
`processors64/`. Native solver outputs are treated as read-only. For field
postprocessing, a scratch reconstruction case is created and only the needed
fields are reconstructed or sampled.

The current pressure/velocity workflow reconstructs standard fields such as:

- `p_rgh`
- `p`
- `U`
- `rho`

Temperature is more sensitive because the original cases use a custom wall
boundary condition. The later OpenFOAM 13 route can reconstruct `T`, while the
OpenFOAM 12 compatibility route is restricted to standard fields. Reports must
therefore state which reconstruction route was used.

For non-mutating reconstruction, the scratch case:

- links or copies mesh and dictionary material into a temporary case;
- omits incompatible zone files if the OpenFOAM version cannot parse them;
- runs `reconstructPar` or `foamPostProcess` in scratch;
- writes reduced CSV/JSON outputs outside the native source tree.

## Streamwise Wall Profiles

The older streamwise package reduces wall fields on repaired major-span bins.
The main inputs are:

- wall patch membership from the case-analysis profile;
- wall-face fields such as `wallShearStress`, `wallHeatFlux`, `p_rgh`, `p`,
  and `T`;
- ordered station definitions from the repaired profile coordinate.

For each wall face, the reduction projects the face centroid onto the span
polyline to obtain:

- local streamwise coordinate `s`;
- local tangent direction;
- bin membership;
- distance-to-centerline diagnostic.

Faces are grouped into bins along each major span. Corners and junctions are
not silently folded into straight-span bins unless explicitly represented in a
separate feature reduction.

## Hydraulic Reduction

The wall-shear route projects wall shear onto the local tangent:

```text
tau_s = tau_w dot t_hat
```

The wall-area mean shear is then converted to a Darcy-style apparent friction
factor:

```text
f_D = 8 * tau_s / (rho_b * U_b^2)
```

The current report-grade interpretation is cautious:

- this is an apparent segment resistance, not a pure fully developed pipe
  friction factor;
- bends, entrance effects, redeveloping flow, and nonuniform heating are
  included in the apparent value;
- signed versus absolute wall shear matters in recirculating regions.

The newer section-mean route uses cut-plane pressure and velocity:

```text
p0 = <p_rgh> + 0.5 * rho * U_bulk^2
dp_loss/ds = - d(p0)/ds
f_D = 2 * D_h * (dp_loss/ds) / (rho * U_bulk^2)
```

That route is closer to a 1D mechanical-energy balance because it works from
section-mean total pressure rather than wall-registered static pressure alone.

## Cross-Section Sampling

Cross-section values are sampled using OpenFOAM `surfaces` function objects
with `cuttingPlane` surfaces. The plane point is the station center and the
normal is the local streamwise tangent.

A key implementation detail is that OpenFOAM Foundation ignores the
`cuttingPlane` `bounds` keyword used in some other OpenFOAM variants. The
reliable workflow therefore dumps the full raw plane and performs single-leg
masking in Python:

```text
keep faces where |x_face - x_station| < leg_radius
```

This avoids averaging two nearby counter-flowing legs into one section. The
flow-alignment metric

```text
alignment = |mean(U)| / mean(|U|)
```

is reported as a gate. Values below about `0.8` indicate that the masked plane
still mixes directions or intersects a bend, so section-mean values are not
paper-grade for that station.

Section outputs include:

- section-mean `p_rgh`;
- section-mean `rho`;
- `U_bulk`;
- measured cross-section area;
- measured hydraulic diameter;
- dynamic head;
- total pressure;
- mdot-derived velocity cross-check where a native monitor exists.

## Thermal Reduction

The thermal closure route reduces wall duty and bulk temperature to segment
quantities:

```text
q_w       = segment wall heat flux
q'_wall   = segment wall duty / segment length
T_wall    = wall-face or patch-mean wall temperature
T_bulk    = enthalpy-flux-weighted mixed mean
Delta T   = T_wall - T_bulk
h         = q_w / Delta T
UA'       = q'_wall / Delta T
R'_th     = 1 / UA'
Nu        = h * D_h / k(T_bulk)
```

The preferred bulk temperature is not a simple area mean. It is the
enthalpy-flux mixed mean:

```text
T_bulk = integral(rho * u_n * cp(T) * T dA)
       / integral(rho * u_n * cp(T) dA)
```

This is important for salt cases because `cp(T)` is temperature dependent. A
mass-flux-only mean can mis-weight hot and cold portions of the section.

The thermal quantities are support-gated. They should be reported only when:

- the section mask isolates one coherent leg;
- positive aligned flux is nontrivial;
- the selected cut-plane area is compatible with the expected monitor area;
- `|T_wall - T_bulk|` is large enough that `h` and `UA'` are not singular.

When these gates fail, wall heat and wall temperature can still be useful, but
`h`, `UA'`, `Nu`, and `R'_th` should be written as unavailable or provisional
rather than smoothed through the gap.

## What Goes Into A 1D Profile

A paper-grade 1D profile row should include, at minimum:

- case identifier and source path;
- time or representative time window;
- CFD span and mapped 1D segment;
- local streamwise coordinate or station label;
- field source: wall bin, native faceZone monitor, or sampled cut plane;
- reduced value and units;
- weighting definition;
- flow-direction convention;
- quality/status flag;
- provenance path to the script/report that produced it.

Examples of 1D quantities include:

- `p_rgh(s)`;
- `p0(s)`;
- `U_bulk(s)`;
- `rho(s)`;
- `T_bulk(s)`;
- `T_wall(s)`;
- `q'_wall(s)`;
- apparent `f_D(s)` or segment-mean `f_D`;
- `UA'(s)` or segment-mean `UA'`;
- branch totals such as `upcomer = left_lower_leg + test_section_span + left_upper_leg`.

## Why Zones/Sets Alone Are Not Enough

Native OpenFOAM zones and sets should be used when they are semantically
correct. They are especially useful for:

- mdot monitor planes;
- PIV slab summaries;
- checking that a sampled section has the right area and mass flux;
- preserving provenance from the original model setup.

They are not enough for the full reduction because:

- many 1D spans do not have a native mdot face zone;
- `cellZones` often describe geometry parts or junctions, not ordered 1D
  stations;
- a `cellZone` does not define wall perimeter, hydraulic diameter, or local
  streamwise tangent;
- zones do not resolve ambiguous 1D names such as `upcomer` versus
  `lower_leg`;
- reliable cross-section sampling still needs masking and alignment checks;
- wall-based and section-based reductions require different support surfaces.

The best practice is to use native zones/sets as trusted anchors, not as the
entire 1D model.

## Recommended Paper Methods Text

The following text can be adapted directly into a manuscript methods section:

> Three-dimensional OpenFOAM fields were reduced to one-dimensional profiles
> using a reproducible postprocessing contract rather than by directly
> averaging all cells in a mesh region. Each loop span was assigned an ordered
> centerline, wall-patch set, flow-direction convention, and optional native
> OpenFOAM monitor faceZone. Wall quantities were projected onto the local
> streamwise coordinate and binned by span. Cross-section quantities were
> sampled on cutting planes normal to the local centerline tangent and then
> masked to isolate a single pipe leg. Native OpenFOAM faceZones were used for
> mass-flow validation where available, but the final 1D profiles were formed
> from the repaired streamwise-coordinate contract because the native zones do
> not fully define the ordered 1D model geometry.
>
> Hydraulic reductions used both wall-registered and section-mean diagnostics.
> Wall-shear reductions projected the wall shear vector onto the local tangent
> and converted the area-averaged shear to an apparent Darcy factor. Section
> reductions computed hydrostatic-corrected static pressure, bulk velocity,
> dynamic head, and total pressure on masked cross-sections. Apparent segment
> friction factors were then derived from the downstream loss gradient of total
> pressure. Thermal reductions used wall heat flux and wall temperature together
> with an enthalpy-flux-weighted bulk temperature. Effective heat-transfer
> coefficients and `UA'` values were reported only when cross-section support,
> flow alignment, and temperature-difference gates were satisfied.
>
> All derived 1D quantities therefore carry explicit provenance and quality
> flags identifying the source fields, weighting definitions, coordinate map,
> and any masking or convergence limitations.

## Remaining Limitations

The current 3D-to-1D reduction is strong enough for transparent reporting, but
several limitations should remain visible:

- mesh independence is not yet established for the closure quantities;
- some thermal reductions require OpenFOAM 13 reconstruction of `T`;
- `wallHeatFlux` does not include a radiative `qr` column, so HTC/`UA'`
  derived from it are convective-only when radiation is enabled;
- corner and junction losses are not fully represented by straight-span bins;
- some legacy outputs used wall-registered pressure rather than section-mean
  total pressure;
- signed wall shear should be preferred where recirculation can reverse local
  flow;
- any 1D closure fit must cite the locked CFD-to-1D segment-name map.

## Practical Next Steps

1. Keep native `faceZones`, `faceSets`, `cellSets`, and `cellZones` in the
   provenance table for each case.
2. Add a compact machine-readable reduction manifest for every future package:
   source fields, zones used, profile version, station map, quality gates, and
   output columns.
3. Prefer section-mean total-pressure gradients for hydraulic closure fits.
4. Use enthalpy-flux bulk temperature for thermal closure fits.
5. Reserve native `cellZones` for geometry provenance or special region
   summaries unless an explicit ordered 1D mapping is defined for the zone.
