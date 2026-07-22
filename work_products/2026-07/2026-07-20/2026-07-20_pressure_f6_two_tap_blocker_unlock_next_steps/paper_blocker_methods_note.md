# Paper Methods Note: Pressure/F6/Two-Tap Blocker Unlock

The current `corner_lower_right` two-tap rows are not ordinary component-loss
measurements. Face-level flux extraction shows material reverse flow at both
endpoint surfaces, so the net-throughflow denominator is not a stable ordinary
minor-loss reference. The rows also remain `apparent_cluster_only`, not clean
component K, and no same-label/same-formula/same-sign mesh/time uncertainty
family exists for the pressure residual or K formulas.

The unlock strategy is therefore split. Ordinary K requires a future
same-topology, non-recirculating anchor from the `CAND-001` Salt4 high-heat /
no-recirculation source family after terminal review and fresh staged-copy
sampling. Recirculating rows are retained as a separate section-effective
pressure-residual model lane using explicit buoyancy/`p_rgh`, kinetic,
straight/development, and face-level `q_pos/q_neg/q_abs` terms. These rows can
support diagnostic interpretation of lower apparent K, but they cannot be used
to claim admitted lower component K or fit F6.
