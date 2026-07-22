# Span Endpoint Temperatures

Generated: `2026-07-08`
Task: `AGENT-203`
Author: claude

## Purpose

Extract mass-flux-weighted bulk temperature at span endpoint stations (s00, s04) for
Salt 2/3/4 Jin mainline cases. Enables computing `enthalpy_change_W` per span for
heat ledger cross-checks without re-running foamPostProcess.

## Method

Input: existing `secmeanSurfaces` 8-column XY cut-plane files from
`tmp/2026-06-30_claude_action_items/recon_salt{2,3,4}_of13/postProcessing/secmeanSurfaces/{time}/`

Key technique: T derived from density inversion of the linear EOS:
```
rho = 2293.6 − 0.7497 × T  →  T = (2293.6 − rho) / 0.7497
```

With constant cp (= 1423.47 J/kg/K for Salt Jin), the mass-flux-weighted bulk T simplifies to:
```
T_bulk = Σ(ρ·u_n·T) / Σ(ρ·u_n)
```
where u_n is the velocity component along the mean flow direction at each cut plane.

Pipe core detection: faces in the top 20th percentile by velocity magnitude are used to
estimate the pipe centre, then faces within leg_radius = 0.015 m of that centre are
used for bulk T computation. This handles diagonal cut planes that span multiple pipes.

## Recirculation findings

The upcomer (left_lower_leg, test_section_span, left_upper_leg) has **85–98%
recirculation** at endpoint cut planes. The standard mixing-cup T (T_bulk_k) is
thermodynamically correct for energy balance but numerically diverges (e.g. 1012 K at
left_lower_leg s04). We report both:

- `T_fwd_bulk_k`: forward-flow-only mass-flux-weighted T — physically realistic (~444–490 K)
- `T_bulk_k` (mixing-cup): used only for spans with recirculation_ratio < 0.5

The `T_in_bulk_k` and `T_out_bulk_k` (and delta_T) columns use `T_fwd_bulk_k` when
recirculation_ratio > 0.5, `T_bulk_k` otherwise.

## Key results

### Heater (lower_leg): s04→s00 (downcomer junction → upcomer junction)

| Case | T_in (s04) | T_out (s00) | dT | Energy balance error |
|---|---|---|---|---|
| Salt 2 | 444.4 K | 459.7 K | +15.35 K | +8.5% vs Q/mdot·cp |
| Salt 3 | 457.2 K | 473.0 K | +15.79 K | −0.3% |
| Salt 4 | 472.5 K | 489.0 K | +16.44 K | −8.5% |

Energy balance reference: mdot = 0.013198 kg/s (from AGENT-194 heat ledger).
Error ≤ 8.5% — consistent with 28.7% recirculation at lower_leg s00 causing T measurement bias.

### Cooler (upper_leg): s00→s04 (upcomer top → downcomer top)

| Case | T_in (s00) | T_out (s04) | dT | Coverage of Q_cooler |
|---|---|---|---|---|
| Salt 2 | 447.9 K | 444.6 K | −3.26 K | 45% |
| Salt 3 | 461.0 K | 457.1 K | −3.89 K | 48% |
| Salt 4 | 476.6 K | 471.9 K | −4.62 K | 51% |

Coverage ~45-51%: the upper_leg cut planes s00/s04 do not bracket the full cooler
(cooler includes reducers and multiple upper patches extending beyond the span).

### Upcomer spans (left_lower_leg, test_section_span, left_upper_leg)

Not usable for energy balance — recirculation 85–98%. T_fwd values reported for
characterization only:
- Upcomer fluid T_fwd ≈ 445–484 K depending on case
- test_section dT ≈ −0.4 to +0.1 K (isothermal within measurement uncertainty)
- left_upper_leg shows dT = +7.5–8.2 K but this is unreliable at high recirculation

## Limitations

1. T derived from rho inversion — exact for linear EOS but any rho contamination propagates
2. Upcomer T_fwd_bulk uses mean_U direction as flow axis — unreliable when recirculation > 80%
3. Cooler cut planes (upper_leg) don't bracket full cooler extent
4. No face-area weighting — assumes uniform face area at each cut plane
5. right_leg (downcomer) T values affected by recirculation at s04 (76.3%) and bend geometry at s00

## Files

- `span_endpoint_temperatures.csv`: 18 rows (6 spans × 3 cases), all T and dT values
- `summary.json`: machine-readable metadata and counts
- Tool: `tools/extract/sample_span_endpoint_temperatures.py`
- Tests: `tools/extract/test_sample_span_endpoint_temperatures.py` (17 tests, all passing)
