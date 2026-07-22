# Wall-Layer / Bulk-Temperature Mapping Recommendations

Task: `AGENT-281`
Date: 2026-07-13
Parent package: `AGENT-279`

## Purpose

The no-radiation parity package showed that imposing CFD heater and cooler
setup terms together closes most of the first-order mean-temperature mismatch.
The remaining problem is not just a scalar heat-loss multiplier. The CFD
external boundary acts on wall and near-wall temperatures, while the current 1D
external loss replay applies each `hA/Ta` row directly to the segment bulk
temperature:

```text
q_ext_1D = hA * max(T_bulk_1D - Ta, 0)
```

That is a useful diagnostic, but it is not a wall-layer-equivalent mapping.
The next implementation should make the driving-temperature convention explicit
before fitting any external `hA`, internal `Nu`, or heat-loss correction.

## Recommended Temperature Definitions

Use separate temperatures for separate physical questions.

| Symbol | Definition | Primary use | Fit status |
| --- | --- | --- | --- |
| `T_mix_signed` | Signed mass-flux/mixing-cup bulk temperature at a cut plane, `sum(rho*u_n*T)/sum(rho*u_n)` when `cp` is effectively constant. | Segment enthalpy balance and energy-conserving bulk march. | Fit-safe only when net mass flux is well supported and recirculation is low. |
| `T_fwd_bulk` | Forward-dominant mass-flux-weighted temperature using only cells/faces with positive dominant-flow normal velocity. | Local thermal state in recirculating sections, especially upcomer diagnostics. | Diagnostic or guarded fit input when recirculation is material. |
| `T_path_bulk(s)` | Streamwise interpolation of supported inlet/outlet cut-plane bulk temperatures along the 1D path. | Segment-level 1D state comparison and probe interpolation. | Fit-safe when endpoint planes pass support and sign gates. |
| `T_wall_inner` | Area-weighted inner wall temperature on the wetted CFD patch or nearest available wall-face proxy. | Internal effective `h`, `Nu`, and wall-to-bulk resistance. | Diagnostic until sign and mesh gates pass. |
| `T_wall_shell` | Near-wall fluid shell temperature from first-cell/near-wall samples adjacent to the heat-transfer patch. | Wall-layer mapping between bulk fluid and wall boundary. | Needed before fitting external hA multipliers. |
| `T_ext_drive` | Effective temperature that would reproduce CFD realized non-radiative external flux from `hA`: `Ta + q_realized/hA` for loss-positive rows. | Inverse check for external boundary parity. | Diagnostic; use to evaluate mapping candidates, not as direct per-case hack. |

## Mapping Ladder

### 1. Energy Balance Mapping

For control-volume heat accounting, use `T_mix_signed` at well-supported inlet
and outlet planes. This is the right first choice because the 1D energy march is
an enthalpy balance:

```text
Delta h_cv ~= cp * (T_mix_signed,out - T_mix_signed,in)
Q_cv ~= mdot * cp * Delta T_mix_signed
```

Gate it:

- Require nonzero signed mass-flux denominator.
- Require enough faces after geometric masking.
- Require low-to-moderate recirculation, or report a paired forward-only
  diagnostic.
- Do not use it for `h_eff` when `T_wall - T_mix_signed` changes sign or is
  near zero.

### 2. Recirculation-Aware Local Bulk Mapping

When recirculation is high, signed mixing-cup temperature can become numerically
fragile or physically misleading for local wall transfer. For those sections,
especially the upcomer, report both:

```text
T_mix_signed
T_fwd_bulk
```

Suggested gates:

- `recirculation_ratio < 0.10`: use `T_mix_signed` for energy and wall-transfer
  diagnostics.
- `0.10 <= recirculation_ratio < 0.50`: report both; use for fitting only if
  sign, support, and sensitivity checks agree.
- `recirculation_ratio >= 0.50`: use `T_fwd_bulk` as a local-state diagnostic,
  but mark scalar 1D bulk thermal closure as blocked for that section.

### 3. Pathwise Bulk Mapping

The 1D model needs a continuous section temperature. Build `T_path_bulk(s)` from
interface or station samples:

```text
T_path_bulk(s) = linear_or_piecewise_interpolation(T_bulk at supported stations)
```

Use this for comparing the 1D segment state against CFD, not as the wall
boundary driving temperature by default. The interpolation should carry support
metadata: station ids, selected temperature rule, face counts, recirculation
ratio, and whether the station is fit-safe.

### 4. Internal HTC / Nu Mapping

For internal effective CFD quantities, keep the conventional postprocessed form:

```text
DeltaT_internal = T_wall_inner - T_bulk_selector
h_eff = q_wall / DeltaT_internal
Nu_eff = h_eff * D_h / k_bulk
```

Recommended selector:

- Use `T_mix_signed` for ordinary, low-recirculation spans.
- Use `T_fwd_bulk` only as a diagnostic sensitivity in recirculating spans.
- Do not fit `Nu_eff` where `abs(DeltaT_internal)` is small, where heat-flux
  sign conflicts with `DeltaT_internal`, or where mesh/time-window gates are
  missing.

This keeps internal Nu errors separate from external/HX boundary errors.

### 5. External hA Mapping

For non-cooler `hA/Ta` rows, the external boundary should not be driven directly
by the segment bulk temperature until wall-layer mapping is checked. Evaluate
three candidates in order:

```text
E0_bulk:
q_ext = hA * (T_path_bulk - Ta)

E1_wall_shell:
q_ext = hA * (T_wall_shell - Ta)

E2_low_dimensional_blend:
T_drive = T_path_bulk + beta_family * (T_wall_shell - T_path_bulk)
q_ext = hA * (T_drive - Ta)
```

Use `E0_bulk` only as the baseline diagnostic currently represented by N2.
Prefer `E1_wall_shell` if near-wall samples are robust. If near-wall samples are
noisy but consistently biased relative to bulk, use `E2_low_dimensional_blend`
with a small number of section-family parameters:

- `heated_incline`
- `vertical_ambient` for upcomer/downcomer if they pass recirculation gates
- `junction`
- optionally `cooling_branch_non_hx_shell` for non-HX ambient patches

Do not fit one beta per case.

### 6. Cooler / HX Mapping

Keep cooler duty separated from passive external hA. In the current CFD setup,
cooler imposed and realized duties agree numerically, so the setup-parity model
should continue using imposed cooler duty. Predictive work should later replace
that fixed duty with a low-dimensional HX model:

```text
Q_cooler = UA_HX * DeltaT_lm_or_epsilon_NTU(...)
```

Do not use passive wall-layer hA multipliers to hide cooler/HX mismatch.

### 7. Heater and Test-Section Mapping

Keep heater and test-section source terms separated from passive external loss.

Recommended representation:

```text
heater:
Q_to_fluid = eta_heater_global * Q_heater_imposed

test_section:
Q_net = Q_test_imposed - hA_test * (T_drive_test - Ta_test)
```

The heater efficiency should remain a global or family-level parameter unless
new evidence shows a section-specific mechanism. The test section should not be
treated as a pure source because realized CFD wall flux is a net sink in the
current Salt2-4 rows.

## Fit-Safe Gates

A row should not be admitted for thermal fitting unless it passes these gates:

- boundary role is unambiguous,
- source/sink sign is physically consistent,
- bulk-temperature selector is documented,
- recirculation support is acceptable or explicitly diagnostic-only,
- `abs(T_wall - T_bulk_selector)` is not near zero,
- mesh and time-window uncertainty are available,
- cooler/HX residual is not mixed into passive external hA,
- radiation policy is explicit.

For this AGENT-279 package, the correct status is still diagnostic. The package
identifies the next implementation target; it does not admit an external hA or
internal Nu closure.

## Recommended Fluid API Shape

Add a first-class external boundary dictionary to the 1D model rather than
encoding every correction as a mode-specific hack:

```text
external_boundary_rows = [
  {
    parent_segment,
    role,
    hA_W_per_K,
    Ta_K,
    radiation_on,
    drive_temperature_selector,
    beta_family_id,
    imposed_Q_W,
    fit_status,
    provenance_path
  }
]
```

The first implemented selectors should be:

- `bulk_path`: use `T_path_bulk`.
- `wall_shell`: use sampled near-wall shell temperature when replaying CFD.
- `bulk_wall_shell_blend`: use `T_path_bulk + beta_family*(T_wall_shell - T_path_bulk)`.
- `fixed_realized_q`: diagnostic only, for heat accounting and tests.

This makes the model testable and prevents per-case hidden corrections.

## Immediate Next Step

Build a small extraction package for Salt2-4 that emits, by section and station:

- `T_mix_signed`,
- `T_fwd_bulk`,
- recirculation ratio,
- `T_wall_inner`,
- available near-wall `T_wall_shell`,
- `T_ext_drive = Ta + q_realized/hA`,
- sign/support flags,
- and a recommended selector.

Then rerun the no-radiation parity modes with `E0`, `E1`, and `E2` external
drive choices. The comparison should be judged by section heat parity first and
mean bulk temperature second.
