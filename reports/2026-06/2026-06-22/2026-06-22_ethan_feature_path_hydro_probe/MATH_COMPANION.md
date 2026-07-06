# Math Companion

For each retained-time feature row:

- choose the nearest wall-face stations to the feature-side boundary on the
  start adjacent span
- choose the nearest wall-face stations to the feature-side boundary on the end
  adjacent span
- compute area-weighted wall means on each side:
  - `p_start,wall`
  - `p_end,wall`
  - `p_rgh,start,wall`
  - `p_rgh,end,wall`
- compute endpoint-window deltas:
  - `Delta p_window = p_start,wall - p_end,wall`
  - `Delta p_rgh_window = p_rgh,start,wall - p_rgh,end,wall`
- compute the retained-time hydro candidate:
  - `Delta p_hydro,candidate = Delta p_window - Delta p_rgh_window`

Interpretation boundary:

- this is an endpoint-adjacent wall-window probe, not a defended path integral
- it is useful for proving whether the remaining blocker is mostly support,
  mostly hydro-correction magnitude, or mostly method mismatch against the
  existing endpoint proxy
