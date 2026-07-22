# Coefficient Naming Policy For Upcomer Recirculation

Date: 2026-07-14

Task: AGENT-339

## Required Names

`Nu_section_effective_upcomer_diagnostic` means the row is an effective diagnostic for the extracted upcomer section. It is not a true fit Nu row and must not be consumed by internal-Nu fitting or forward-runtime calibration.

`Nu_section_effective_upcomer_validation` means the row is complete enough for validation-only comparison but still fails at least one fit gate.

`Nu_fit_admissible_upcomer_single_stream` is the only allowed name for a true fit-admissible upcomer Nu row. It can be used only after the extraction/admission contract passes every fit criterion.

## Invalid Single-Stream Conditions

Single-stream `Nu`, `f_D`, and `K` labels are invalid when any of these conditions hold:

- `reverse_area_fraction >= 0.10`
- `reverse_mass_fraction >= 0.10`
- `Ri >= 1.0`
- explicit recirculation flag is `yes`

Rows meeting any of those conditions must use section-effective or diagnostic labels such as `Nu_section_effective_upcomer_diagnostic`, `f_D_section_effective_upcomer_diagnostic`, or `K_section_effective_upcomer_diagnostic`.

## Reopening Internal-Nu Fitting

Internal-Nu fitting may reopen only when a later gate has at least three admitted upcomer rows satisfying `fit_admissible_Nu`, including one ordinary-pipe non-recirculating anchor and one near-transition or higher-Re row. These rows must have matched inlet/mid/outlet extraction, exact time windows, accepted mesh/time uncertainty, clean sign and heat-balance checks, finite mid/outlet Gz, and no heater, cooler, wall, storage, radiation, branch-mixing, or recirculation residual assigned to Nu.

CFD `rcExternalTemperature` wallHeatFlux includes radiation where that boundary condition is used. There is no separate exported `qr` term to add to internal Nu, and no radiation residual may be hidden inside Nu.
