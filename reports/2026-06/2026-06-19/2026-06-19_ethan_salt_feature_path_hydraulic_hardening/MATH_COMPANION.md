# Math Companion

Current available feature quantities:

- `dp_feature_p_pa = p_start - p_end`
- `dp_feature_p_abs_pa = |p_start - p_end|`
- `dp_feature_prgh_pa = |p_rgh,start - p_rgh,end|`
- `dp_feature_loss_prgh_endpoint_pa = |p_rgh,start - p_rgh,end|`
- `dp_feature_hydro_endpoint_proxy_pa = |(p_start - p_end) - (p_rgh,start - p_rgh,end)|`
- `dp_feature_hydro_correction_pa = dp_feature_hydro_endpoint_proxy_pa`
- `adjacent_straight_friction_subtracted_pa = proxy local straight reference from the existing June 19 feature package`
- `feature_excess_proxy_pa = dp_feature_loss_prgh_endpoint_pa - adjacent_straight_friction_subtracted_pa`

Intentionally *not* claimed here:

- a defended `dp_feature_loss_hydro_pa`
- a defended full-path `K_eff`

Reason:

The preserved additive artifacts do not retain a direct feature-path density
integral or equivalent pathwise hydro correction strong enough to replace the
endpoint proxy method.
