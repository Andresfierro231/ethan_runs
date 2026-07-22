# Pressure-Corner Paper Results Section

## Methods Paragraph

For the lower-right corner endpoint pair, the pressure budget was evaluated using the downstream-minus-upstream static pressure difference across `lower_leg__s04 -> right_leg__s00`. The gross static pressure rise was decomposed into hydrostatic, kinetic, straight/developing-reference, pressure-recovery, and residual terms before assigning any model label. The pressure basis used the available `p_rgh` plus hydrostatic decomposition, while the velocity basis and straight/developing subtraction remained guarded by the measured reverse-flow and missing same-basis reference checks. Rows were therefore evaluated as pressure-budget diagnostics unless all component-isolation, ordinary-flow, same-QOI uncertainty, and source-envelope gates passed.

## Results Paragraph

All three Salt2/Salt3/Salt4 rows show a gross static pressure rise across the endpoint pair, ranging from 3035.099 Pa to 3068.717 Pa. The rise is hydrostatic dominated: the hydrostatic contribution spans 1.000427 to 1.000630 of the gross static change. After hydrostatic and kinetic correction, the signed available residual remains small and negative, from -1.850 Pa to -1.254 Pa. Because the rows also have material reverse flow, apparent-cluster isolation, missing straight/developing reference support, and missing same-QOI uncertainty, the admissible label is `section_effective`; the scientific use is a section-effective pressure diagnostic and pressure-recovery diagnostic.

## Limitations Paragraph

The current evidence does not isolate an ordinary-flow component coefficient. Reverse-area fraction is approximately `0.763` and reverse-mass fraction is approximately `0.500`, so the endpoint velocity basis is not an ordinary throughflow reference. The straight/developing correction is missing a same-basis reference, and same-QOI mesh/time uncertainty is not admitted for these rows. The result should therefore be compared as a signed pressure-budget finding, not converted into a clipped loss coefficient, global multiplier, or F6 fit input.

## Table-Ready Claim Ledger

See `table_ready_claim_ledger.csv`.

## Caption Text

See `caption_text.md`.
