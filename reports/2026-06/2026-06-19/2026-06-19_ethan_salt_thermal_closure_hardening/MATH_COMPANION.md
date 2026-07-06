# Math Companion

For each branch/time row:

- `Q_enthalpy = sum_component_spans(mdot * cp * (T_bulk,out - T_bulk,in))`
- `Q_wall = sum_component_spans(wall_heat_integral)`
- `Q_residual = Q_enthalpy - Q_wall`
- `residual_fraction = |Q_residual| / |Q_wall|`
- `Q_grouped_total = Q_intended_transfer + Q_external_or_loss + other_grouped_terms`
- `Q_junction_or_unresolved = Q_wall - Q_grouped_total`
- `grouped_reconstruction_fraction = |Q_junction_or_unresolved| / |Q_wall|`

Signed interpretation:

- Positive `Q_wall` means wall heat enters the fluid.
- Negative `Q_wall` means wall heat leaves the fluid.
- Positive `Q_enthalpy` means the fluid gains energy along the local branch direction.

The effective HTC / Nu columns are computed from the exact retained-time section
integrals:

- `h = Q_wall / integral_wall(T_wall - T_bulk) dA`
- `Nu = h * D_h / k(T_property)`

The `bulk-vs-centerline correction proxy` is a reporting aid only:

- `Q_bc_proxy = h * A_wall * (T_bulk - T_centerline)`

It is not used as a fitting gate.
