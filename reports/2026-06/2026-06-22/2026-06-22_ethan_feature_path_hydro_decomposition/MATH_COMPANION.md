# Math Companion

For each retained feature time:

- `dp_feature_p_pa = p_end - p_start`
- `dp_feature_prgh_pa = p_rgh,end - p_rgh,start`
- `dp_feature_hydro_path_pa = dp_feature_p_pa - dp_feature_prgh_pa`
- `dp_feature_prgh_abs_pa = |dp_feature_prgh_pa|`
- `feature_excess_path_pa = |dp_feature_prgh_pa| - local_boundary_reference_dp_pa`
- `keff_effective_path = feature_excess_path_pa / dynamic_head_local_pa`

The path decomposition is exact with respect to the preserved patch extractor.
The `path_vs_proxy_*_residual_pa` fields are a provenance cross-check against
the June 19 feature hardening package and should remain numerically zero within
floating-point noise.

The wall-window hydro probe remains useful only as a sensitivity comparison:

- `window_hydro_correction_abs_pa`
- `window_vs_path_hydro_gap_fraction`

Those fields quantify how much the June 22 wall-window hydro surrogate differs
from the exact patch-endpoint path decomposition.
