# `piv_slab_velocity` Math Note

Date: `2026-06-25`
Authoring task: `AGENT-132`

## Scope

This note explains how the OpenFOAM `piv_slab_velocity` monitor is computed in
the Ethan CFD cases, using the representative case:

- `jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/system/functions`
- `jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/system/topoSetDict`
- `jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/postProcessing/piv_slab_velocity/0/volFieldValue.dat`

An `rg` scan across staged Salt and Water case trees shows the same
`piv_slab_magU` plus `piv_slab_velocity` pattern is reused across the family.

## 1. What region is sampled?

The monitor does not sample a face or a line. It samples a `cellZone` named
`piv_slab`, created in `system/topoSetDict` with:

```text
{
    name    piv_slab;
    type    cellZoneSet;
    action  new;
    source  boxToCell;
    box     (-0.00112500 0.35613975 -0.01050000) (0.00112500 0.54213975 0.01050000);
}
```

So the sampled region is an axis-aligned rectangular slab:

- `x in [-0.001125, 0.001125] m`
- `y in [0.35613975, 0.54213975] m`
- `z in [-0.0105, 0.0105] m`

The same geometry is recorded in the Salt 2 setup summary as
`measurements.piv_slab_box_m`.

The comment in `topoSetDict` and `system/functions` labels this as the PIV
laser-sheet slab, widened to `2.25 mm` thickness from the nominal experimental
`1.00 mm`.

For the representative Salt 2 continuation case, the output header reports:

- `Cells = 9240`
- `Volume = 9.661896242e-06 m^3`

## 2. What fields are averaged?

The function-object chain in `system/functions` is:

```text
piv_slab_magU
{
    type            mag;
    field           U;
    result          magU;
    executeControl  timeStep;
    writeControl    none;
}

piv_slab_velocity
{
    type            volFieldValue;
    writeControl    outputTime;
    log             false;
    writeFields     false;

    select          cellZone;
    cellZone        piv_slab;

    operation       volAverage;
    fields          (U magU T);
}
```

This means:

1. OpenFOAM first constructs a scalar helper field
   `magU(x, t) = |U(x, t)| = sqrt(Ux^2 + Uy^2 + Uz^2)`.
2. At each output time, OpenFOAM volume-averages `U`, `magU`, and `T` over the
   `piv_slab` cell zone.

## 3. Exact math

Let the slab cell set be `S`, with cell volumes `V_i`.

Let:

- `U_i = (Ux_i, Uy_i, Uz_i)` be the cell velocity in cell `i`
- `T_i` be the cell temperature in cell `i`
- `|U_i| = sqrt(Ux_i^2 + Uy_i^2 + Uz_i^2)`

Define the slab volume:

```text
V_slab = sum_{i in S} V_i
```

Then the reported monitor values are:

```text
<U>_slab = (1 / V_slab) * sum_{i in S} V_i U_i
```

so that:

```text
<Ux>_slab = (1 / V_slab) * sum_{i in S} V_i Ux_i
<Uy>_slab = (1 / V_slab) * sum_{i in S} V_i Uy_i
<Uz>_slab = (1 / V_slab) * sum_{i in S} V_i Uz_i
```

and:

```text
<|U|>_slab = (1 / V_slab) * sum_{i in S} V_i |U_i|
```

```text
<T>_slab = (1 / V_slab) * sum_{i in S} V_i T_i
```

Important implications:

- `piv_slab_velocity` is a volume-weighted average.
- It is not area-weighted.
- It is not density-weighted.
- It is not a direct mass-flow calculation.

## 4. What appears in `volFieldValue.dat`?

The output header is:

```text
# Time            volAverage(U)    volAverage(magU)    volAverage(T)
```

So the columns mean:

- `volAverage(U)` -> vector `(<Ux>_slab, <Uy>_slab, <Uz>_slab)`
- `volAverage(magU)` -> scalar ` <|U|>_slab`
- `volAverage(T)` -> scalar ` <T>_slab`

The registry aggregation therefore maps these to:

- `Ux`
- `Uy`
- `Uz`
- `magU`
- `T`

under dataset `piv_slab_velocity`.

## 5. Crucial distinction: `⟨|U|⟩` is not `|⟨U⟩|`

This is the easiest place to misread the monitor.

At `t = 1 s` in the representative Salt 2 case, the output line is:

```text
volAverage(U)    = (3.383876674e-08 8.484909658e-04 4.614687301e-09)
volAverage(magU) = 1.358190695e-03
```

From the averaged vector,

```text
|<U>_slab| = sqrt((3.383876674e-08)^2 + (8.484909658e-04)^2 + (4.614687301e-09)^2)
           ≈ 8.484909665e-04 m/s
```

but the reported `volAverage(magU)` is:

```text
<|U|>_slab = 1.358190695e-03 m/s
```

These are different because:

- `|⟨U⟩|` lets directional cancellation happen before the magnitude is taken.
- `⟨|U|⟩` takes each cell's local speed first, then averages those positive
  speeds.

So if there is recirculation, cross-flow, or strong local variation inside the
slab, `⟨|U|⟩` can materially exceed `|⟨U⟩|`.

## 6. How does this relate to the experimental-style PIV surrogate?

The comment in `system/functions` says:

```text
Reis et al. compute mdot from the area-weighted PIV velocity magnitude;
recover with mdot = rho * <|U|> * pi * R^2
```

Interpreted carefully, that means the intended downstream surrogate is:

```text
mdot_PIV_surrogate = rho_ref * <|U|>_slab * A_pipe
```

with:

```text
A_pipe = pi * R^2
```

and for this geometry the profile definitions indicate `R ≈ 0.0105 m`.

Important boundary:

- `piv_slab_velocity` itself does **not** compute `mdot`.
- It only provides `⟨U⟩`, `⟨|U|⟩`, and `⟨T⟩` over the slab.
- Any later `mdot` conversion requires an explicit density choice
  `rho_ref` outside this function object.

## 7. Interpretation boundaries

Use `piv_slab_velocity` as:

- a compact monitor of mean vector velocity in the slab via `Ux`, `Uy`, `Uz`
- a compact monitor of mean local speed in the slab via `magU = ⟨|U|⟩`
- a compact monitor of mean slab temperature via `T`

Do not over-interpret it as:

- a direct face flux
- a direct area average
- a direct bulk-pipe average over an exact circular cross section
- a direct mass flow unless a separate `rho * A` conversion is applied
- the same thing as the magnitude of the average vector

## 8. Bottom line

`piv_slab_velocity` is an OpenFOAM `volFieldValue` monitor over a
`boxToCell`-defined slab:

```text
piv_slab_velocity(t) = {
    <Ux>_slab(t),
    <Uy>_slab(t),
    <Uz>_slab(t),
    <|U|>_slab(t),
    <T>_slab(t)
}
```

with all averages taken as volume-weighted cell-zone averages over the
`piv_slab` box at each output time.
