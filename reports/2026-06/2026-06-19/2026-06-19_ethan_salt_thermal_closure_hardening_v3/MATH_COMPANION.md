# Math Companion

This package uses the same retained-time formulas as the June 19 v2 thermal
hardening package, but with one intentional policy change:

- `residual_fraction_of_wall_heat <= 0.45`

All other gate definitions remain unchanged:

- `support_fraction >= 0.90`
- `|Twall - Tbulk| >= 0.25 K`
- `grouped_reconstruction_fraction <= 0.05`

This is a reporting-policy change, not a hidden formula change.
