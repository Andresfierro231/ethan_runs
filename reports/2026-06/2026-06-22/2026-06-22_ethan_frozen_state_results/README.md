# Ethan Frozen-State Results

Generated: `2026-06-23T10:23:00-05:00`

## Frozen-state contract

- Primary pseudo-steady basis: retained late-window mean.
- Sensitivity overlay: latest retained-time snapshot.
- Straight sections are **not** assumed fully developed by default here. The
  admitted straight friction rows remain bounded CFD-supported closures on the
  preserved Salt straight subset, with fully developed values used only as
  references elsewhere in the repo.

## Main findings

- The best current direct internal HTC or Nu evidence remains `left_lower_leg`.
- `upcomer` remains sensitivity-only and should be modeled differently from the
  direct straight branches; this package keeps that boundary explicit.
- `right_leg` or downcomer remains blocked for direct Nu, so cooler-adjacent
  return behavior still needs more retained-time branch observables.
- The refreshed Salt straight package now uses the preserved `20 s` windows
  from the continuation roots. The defended straight set moves from
  `5` case-mean rows to
  `4` late-window rows.
- The late-window rebuild drops `Salt 3 Jin / lower_leg` from the case-mean defended set because `support_fraction_below_floor` (support fraction `0.747`).
- Feature `K_eff` is reopened to `provisional_defended` on a
  stable patch-endpoint pathwise basis for `corner_upper_right|test_section_complex`.

## 1D status

Readable Fluid diagnostics exist, but they predate the June 22 feature-path refresh. Example best row: Salt 1 / ethan_cfd_informed_salt_hybrid_ins_1.0in_rad_0 with air-outlet error -14.01 K and mass-flow error -0.50%.

The tracked external Fluid surface is still stale relative to the June 22 closure set: its current bundle snapshot was generated on `2026-06-19`.

The local frozen-state replay package is current, but the external rerun with
the refreshed closure set remains in progress on `AGENT-102` because the
external `Fluid` repo still lacks a producer for a refreshed Ethan CFD-informed
Salt validation bundle.
