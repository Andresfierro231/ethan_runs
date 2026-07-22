# Presentation Brief

## Slide Title

Where the current 1D model loses heat versus where CFD loses heat

## One-Sentence Takeaway

The best current predictive-style model (`F1_heater_only`) has a near-closed
aggregate heat balance, but the heat is lost in the wrong places: pipe legs
over-lose heat while junction/stub regions under-lose heat.

## Numbers to Show

- `salt_2`: model total loss `265.701 W`, CFD realized total loss `243.393 W`, largest discrepancy `junction:-35.694251959374995`.
- `salt_3`: model total loss `297.501 W`, CFD realized total loss `272.869 W`, largest discrepancy `junction:-39.328731678156`.
- `salt_4`: model total loss `337.601 W`, CFD realized total loss `310.408 W`, largest discrepancy `junction:-43.98897682842`.

## Main Visual to Make

Use `best_predictive_leg_heat_loss_discrepancy.csv` to make a grouped bar chart:

- x-axis: lower leg, upcomer/test-section, cooling branch, downcomer, junction.
- bars: model total loss, CFD realized loss.
- annotate: model-minus-CFD realized loss.

## Speaker Notes

- This is the current best executable predictive-style model, but not final
  predictive HX because imposed cooler duty is still consumed.
- The model over-loses heat in lower leg, upcomer, cooling branch, and downcomer.
- The model under-loses heat most strongly in junction/stub/horizontal
  connector regions.
- The next 1D refinement should add junction heat-loss coverage and replace
  bulk-driven ambient losses with wall/shell external-boundary dictionaries.
- Do not present this as validation of the 1D heat-loss model. Present it as a
  diagnostic that tells us exactly what to fix.
