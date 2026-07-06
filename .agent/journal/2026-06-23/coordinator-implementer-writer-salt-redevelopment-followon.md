# AGENT-115 Raw Journal

Date: `2026-06-23`
Role: `Coordinator / Implementer / Writer`

## Observed output

- Added `reports/2026-06-23_ethan_salt_redevelopment_followon/**`.
- The package publishes `salt_redevelopment_profile_rows.csv` with `14023` retained straight-leg rows and `salt_redevelopment_span_summary.csv` with `54` Salt case/span summaries.
- The package also reuses the June 22 feature-path hydro decomposition and republishes:
  - `feature_class_summary.csv`
  - `feature_exclusion_reason_summary.csv`
- Current bend / transition coverage from the reused feature package:
  - total feature case rows: `45`
  - fit-used case rows: `21`
  - exclusions dominated by `nonpositive_path_feature_excess_loss` with `24` rows

## Inferred interpretation

- The straight-leg lane now has an explicit retained-time overlay of hydrostatic-corrected pressure, kinetic-energy scale, and wall heat loss for all Salt cases. That is enough to discuss redevelopment directly instead of only referring to branch-mean summaries.
- The bend/corner lane is usable at the endpoint-path level, especially for `corner_upper_*` and many `test_section_complex` rows, but it still lacks a continuous density-path integral through the feature interior.
- The main remaining minor-loss limitation is therefore not the endpoint patch extraction itself. It is the absence of a stronger interior path model that would let the feature excess be defended independently of the adjacent-straight reference.

## Contradictions or caveats

- The redevelopment package does not claim that `q_dyn(s)` is a pressure field. It is only an acceleration / kinetic-energy scale plotted on the same legwise coordinate as `p_rgh(s)`.
- Large `q'(s)` on a leg should be interpreted as evidence that both thermal and hydraulic development are still evolving; it is not itself a friction-loss observable.

## Next suggested actions

- Use the per-case figures in `reports/2026-06-23_ethan_salt_redevelopment_followon/figures/**` when discussing where fully developed assumptions are weakest on Salt 2-4.
- If a later pass lands a stronger feature-interior hydro model, append it as a new dated package rather than mutating the June 22 endpoint-path decomposition.
