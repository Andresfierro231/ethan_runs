# Thesis and Presentation Notes

## Suggested slide claim

The 3D and 1D models can now be compared by heat path rather than only by mean
temperature error. The same-assumption ledger shows which sections receive
heater/test-section input, which section removes cooler duty, and where passive
wall/junction losses and realized wall-flux residuals sit.

## Caveated result wording

Use: "A fixed-mdot diagnostic alignment was built for Salt2-4. It separates
imposed setup heat, realized CFD wall heat, and current 1D replay heat by
section. It identifies heat-path mismatches without promoting CFD wallHeatFlux
or CFD mdot to predictive runtime inputs."

Avoid: "The 1D thermal model is validated" or "radiation-off replay matches
Ethan CFD."

## Current key observation

The largest setup-vs-realized case residual in B3 is salt_2 at 0.626 of heater power.

The package should be read by segment first, then by case total. Case totals can
hide wrong-location heat transfer.

## Figures to make later

- Stacked signed heat bars by case and segment: CFD imposed, CFD realized, B3
  setup replay, and B2 realized-wallFlux replay.
- Role/lane bars: heater, test section, cooler, passive wall, junction.
- One residual waterfall per Salt case normalized by heater power.
