# Presentation Brief

## One-Sentence Takeaway

The current best 1D predictive-style model releases about the right total heat
only by cancellation: it loses too much heat in pipe legs and too little in
junction/stub connector regions.

## What This Study Adds

- A patch-level CFD external-boundary/source contract.
- Segment-equivalent h/Ta/Tsur/emissivity/layer rows for 1D setup parity.
- A radiation policy that prevents double-counting.
- A leg-by-leg comparison for Salt2 train, Salt3 validation, and Salt4 holdout.
- A thermal-profile drive diagnosis showing where bulk temperature is likely
  the wrong external-loss driver.

## Slide-Ready Claims

- CFD `rcExternalTemperature` includes radiation; radiation-off replay is only a
  sensitivity.
- Realized CFD `wallHeatFlux` is diagnostic evidence, not a runtime predictive
  input.
- The biggest model-form issue is heat-loss placement, especially missing
  junction/stub loss and over-loss in pipe legs.
- Next 1D refinement should use external-boundary dictionaries and wall-adjacent
  drive tests before fitting internal Nu.

## Figure Suggestions

1. Stacked bar: CFD realized loss vs best 1D loss by leg for Salt2-4.
2. Residual bar: model-minus-CFD heat loss by leg.
3. External boundary circuit schematic: h/Ta/Tsur/emissivity/layers to
   environment, with realized wallHeatFlux kept separate.
4. Thermal drive diagnostic: bulk/path temperature vs wall-shell proxy by leg.
