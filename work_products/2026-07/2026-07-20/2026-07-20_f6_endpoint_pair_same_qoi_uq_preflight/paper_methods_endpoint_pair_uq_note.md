# Endpoint Pair and Same-QOI UQ Note

For the non-upcomer F6 branch path, endpoint planes were chosen from clean interior mesh-centerline stations rather than fitting-end stations.
Both `right_leg` and `test_section_span` use `s03->s01`, with the sign convention `p_upstream - p_downstream` set by the measured negative `u_along_tangent` in the section-pressure tables.

The current package computes same-label, same-formula, same-sign section-pressure deltas for Salt2/Salt3/Salt4 and a Salt2 coarse/medium/fine diagnostic mesh spread.
This is not yet an admitted GCI or F6 fit: the raw face-level `RAF`/`RMF` reverse-flow metrics and same-QOI time-window sensitivity remain missing.

Endpoint pairs selected: `6`. Diagnostic Salt2 mesh-spread rows: `2`.
No scheduler, registry, native CFD-output, component-K, or F6 admission mutation was performed.
