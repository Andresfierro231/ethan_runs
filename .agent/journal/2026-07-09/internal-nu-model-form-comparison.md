# Internal Nu / HTC Model-Form Comparison

Date: 2026-07-09
Task: AGENT-243
Role: Coordinator / Writer

## Prompt

The user requested paper-facing documentation explaining how the OpenFOAM CFD
does internal Nusselt/HTC, how the current 1D model does internal Nusselt/HTC,
and a thorough comparison of model forms.

## Observed Evidence

- The representative Salt 2 Jin OpenFOAM continuation dictionary
  `constant/momentumTransport` declares `simulationType laminar`.
- `constant/thermophysicalTransport` declares laminar `model Fourier`.
- `constant/physicalProperties` declares `heRhoThermo`, `sensibleEnthalpy`,
  `icoTabulated` transport, constant Cp coefficients, and tabulated salt
  viscosity/conductivity.
- `0/T` uses `rcExternalTemperature`, `externalTemperature`, and
  `zeroGradient` thermal boundaries; `rcExternalTemperature` rows include
  prescribed `h`, `Ta`, `Tsur`, emissivity, and layer metadata.
- `0/U` uses default `noSlip` walls with selected slip NCC neighbor patches.
- The external Fluid solver implements `internal_nusselt(Re, Pr, L_over_D)`,
  converts it to `h_i = multiplier * Nu*k/D`, and uses `R_i' = 1/(h_i*pi*D)`
  in segment thermal resistance calculations.
- The 1D HX model uses the same internal Nusselt function for the salt side and
  the annular air side before an epsilon-NTU cooler calculation.
- The July 8 patchwise heat-ledger code reconstructs CFD effective internal
  convection from `wallHeatFlux_mean/(wall_T_mean - T_bulk_span)`, and labels
  those rows as validation diagnostics rather than fit targets.
- The GCI helper documents that current apparent `Nu`/`UA`/`HTC` closures do
  not yet carry a discretization-error bound.

## Interpretation

The CFD should not be described as using an internal Nu correlation. It solves
the internal temperature field and produces wall heat flux from that field.
Any CFD-side `Nu`, `h_i`, or internal resistance is a postprocessed effective
diagnostic.

The 1D model does use an explicit internal Nu closure. Its baseline model is a
transparent pipe-flow correlation with optional multipliers/profile descriptors
for CFD-informed variants. Therefore, disagreement between CFD and 1D is a
model-form comparison between a resolved 3D thermal field and a scalar
resistance closure, not a direct comparison of two equivalent Nu formulas.

The outside-wall OpenFOAM setup is also not a resolved coupled outside-air CFD
solve. The external environment enters through boundary-condition coefficients
and layer-resistance metadata.

## Outputs

- `reports/2026-07/2026-07-09/2026-07-09_internal_nu_model_form_comparison/README.md`
- `reports/2026-07/2026-07-09/2026-07-09_internal_nu_model_form_comparison/model_form_comparison.csv`
- `reports/2026-07/2026-07-09/2026-07-09_internal_nu_model_form_comparison/source_index.csv`
- `reports/2026-07/2026-07-09/2026-07-09_internal_nu_model_form_comparison/summary.json`
- `imports/2026-07-09_internal_nu_model_form_comparison.json`

No OpenFOAM extraction, Fluid rerun, native solver-output mutation, registry
edit, external source edit, or scheduler action was performed.
