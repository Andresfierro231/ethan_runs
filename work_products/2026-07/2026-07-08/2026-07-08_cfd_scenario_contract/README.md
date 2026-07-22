# CFD Scenario Contract And Observation Table Audit

Generated: `2026-07-08T10:46:02`

## Scope

Read-only audit for the scientific redo requested on 2026-07-08. This package
separates case setup, available latest solver time, prior extracted windows, and
seed closure observations. It does not run OpenFOAM and does not mutate solver
case trees.

## Key Findings

- Mainline CFD Salt cases with readable `0/T` contain a `0.03556 m` layer, i.e.
  `1.4 in`, in their wall boundary-layer stack. The `0.25 in` / `0.30 in`
  values in the friction mdot comparison are 1D temperature-matching sweep
  settings, not the CFD case insulation label.
- `rcExternalTemperature` patches carry `emissivity 0.95`. No
  `constant/radiationProperties`, `qr`, or `G` field was found in the audited
  case roots, so the safest label is
  `surface_emissivity_bc_present_no_volume_radiation_field`, not simply
  `radiation absent`.
- Salt 1 nominal has a later June 25 base continuation candidate ending at about
  `4026.15625 s`, while several prior evidence products still use the June 18
  Salt 1 window ending at `3756.33125 s`.
- Salt 2/3/4 mainline case trees have later available retained times than the
  June 29 source-contract extraction rows. Any publication or fitting table must
  state whether it uses the current case latest or a frozen older package.
- Corrected Salt Q rows remain non-admitted until formal gate output lands.

## Outputs

- `scenario_contract.csv`: case setup, latest retained solver time, insulation
  label, and radiation label.
- `latest_window_audit.csv`: compares available latest solver time against the
  prior source-contract extraction window.
- `closure_observations_seed.csv`: canonical seed table. One row is one
  observable, with units, source path, eligibility flags, and quality flags.
- `summary.json`: machine-readable counts and recommendations.

## Counts

- Scenario rows: `19`
- Mainline rows with detected 1.4 in layer: `4`
- Prior extraction rows older than available case latest: `5`
- Seed observation rows: `132`

## Immediate Recommendations

1. Treat the actual CFD scenario as `1.4 in wall/insulation layer present` with
   surface-emissivity boundary metadata, pending a deeper review of the custom
   `rcExternalTemperature` implementation.
2. Do not label the CFD as `0.25/0.30 in`; reserve those values for the 1D
   diagnostic matched-temperature scenario.
3. Refresh Salt 1 qualification from the June 25 base continuation before using
   Salt 1 as nominal evidence.
4. Before final closure fitting, rebuild pressure/thermal observations from a
   single declared latest-window contract rather than mixing older frozen
   extraction packages with newer retained solver output.
