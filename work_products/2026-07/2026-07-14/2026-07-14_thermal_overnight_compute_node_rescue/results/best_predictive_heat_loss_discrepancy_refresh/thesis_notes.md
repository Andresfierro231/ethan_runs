# Thesis Notes

Use this package to explain why a low aggregate temperature error can still hide wrong heat-loss placement.

Best wording: the current best predictive-style model roughly balances total heat because errors cancel by leg; it over-removes heat from several pipe legs and under-removes heat in junction/stub regions.

Model changes needed:

- heater realization plus lower-leg wall loss: Separate heater realization from lower-leg passive loss. Current net heat can look close because heater over-input and ambient over-loss cancel; model heater efficiency/source contract and wall loss separately.
- test-section/upcomer source and wall loss: Keep heater-only/test-section source policy as default, then reduce or remap upcomer external loss using wall-adjacent/external-boundary dictionaries rather than bulk-temperature ambient loss.
- cooler/HX plus upper-leg passive wall loss: Separate active HX/cooler duty from passive upper-leg wall loss. Replace imposed cooler duty with a setup-only UA/effectiveness model, and keep passive cooling-branch wall loss in the external-boundary lane.
- external boundary wall-drive model: Implement first-class external boundary h/Ta/Tsur/emissivity/layer handling with wall/shell drive; current bulk-driven ambient loss over-removes heat in the downcomer.
- junction/stub heat-loss coverage: Add junction/stub/horizontal-connector heat-loss coverage. Current 1D ambient model under-removes junction heat relative to CFD realized wallHeatFlux by the largest W margin.
