# Worker Task Guidance And Heat Ledger Boundary

Date: `2026-07-08`
Role: Coordinator / Writer
Owner: codex

## Observed Facts

The July 8 packages now provide:

- a canonical observation-table contract:
  `work_products/2026-07-08_closure_observation_table/`
- a hardened pressure-term ledger:
  `work_products/2026-07-08_pressure_term_ledger/`
- a patchwise wall-flux heat ledger:
  `work_products/2026-07-08_patchwise_heat_ledger/`

The heat ledger is not a final mechanistic heat-transfer closure. It is good
enough for sanity checks on imposed heat input, cooler removal, passive wall
exchange, junction exchange, wallHeatFlux sign convention, and gross boundary
energy balance. It is not yet good enough to support final mechanistic closure
claims because inlet/outlet enthalpy-flow changes and a resistance-network
decomposition are still missing.

## Inferred Interpretation

Hydraulic closure claims remain thermally contaminated until the heat ledger can
reconcile:

- heater imposed duty by patch/region;
- cooler removed duty;
- passive wall heat leak/gain;
- enthalpy-flow change by segment;
- wallHeatFlux integral by segment;
- residual;
- boundary-condition type and sign convention;
- radiation status, with radiation treated as absent only if OpenFOAM output
  does not expose a `qr` term.

The existing Salt heat-loss separation remains case-level/audit-style. It does
not resolve internal convection, wall conduction, external convection/radiation,
and junction losses into a complete resistance network.

## Blockers

- `enthalpy_change_W` cannot be computed from the current July 8 heat package
  because the available HTC source provides one span bulk temperature, not
  inlet/outlet bulk temperatures.
- `wallHeatFlux_vs_enthalpy_residual_W` is therefore intentionally blank.
- A final resistance network requires additional patch/layer data and explicit
  treatment of internal convection, wall conduction, external convection, and
  any radiation term exposed by OpenFOAM.

## Worker Task Templates

- `pressure_term_ledger`: produce per-segment pressure decomposition with
  buoyancy correction and residuals.
- `patchwise_heat_ledger`: reconcile imposed Q, wall flux, enthalpy change,
  cooler sink, passive losses.
- `time_window_uncertainty`: tag quasi-steady windows, drift, amplitude, and
  early-stop flags.
- `observation_table_contract`: one canonical CFD observation schema for 1D
  model fitting.
- `targeted_litrev_forms`: convert literature lessons into candidate
  equations/features, not prose.
- `minor_loss_two_tap`: extract bend/reducer/junction losses with local
  normalization.
- `model_form_bakeoff`: compare closure families before committing to one.
- `upcomer_onset`: characterize when the upcomer becomes a recirculation-cell
  problem instead of a pipe-friction problem.
- `mesh_uncertainty`: define what minimum mesh evidence is needed before
  publication claims.

## Closeout Rule For Workers

Every task should end with:

1. observed facts;
2. inferred interpretation;
3. blockers;
4. exact files used;
5. recommended next action.

This requirement was added to `.agent/BOARD.md` under the Planned / Unclaimed
queue guidance on `2026-07-08`.

## Recommended Next Action

Open a follow-up heat task for enthalpy-flow extraction at physical segment
interfaces. The follow-up should fill `enthalpy_change_W` and residual columns
in a new patchwise heat-ledger package rather than editing the July 8 wall-flux
foundation package in place.
