# Math Companion

For each retained-time feature row:

- `Delta p_feature,prgh = |p_rgh,end - p_rgh,start|`
- `g_start = mean(nearest finite boundary-bin dp_major_gradient on the start side)`
- `g_end = mean(nearest finite boundary-bin dp_major_gradient on the end side)`
- `Delta p_ref,local = 0.5 * L_feature * (g_start + g_end)`
- `Delta p_excess,local = Delta p_feature,prgh - Delta p_ref,local`
- `q_dyn = 0.5 * rho_local * U_local^2`
- `K_eff,local = Delta p_excess,local / q_dyn`

Sign convention:

- `Delta p_feature,prgh` is stored as a positive loss magnitude.
- Positive `Delta p_excess,local` means the feature patch-to-patch `p_rgh` loss
  exceeds the adjacent straight-reference estimate.
- Negative `Delta p_excess,local` is excluded from defended feature fitting.

Validity gates:

- both feature sides must resolve local boundary support
- case-level positive-time fraction must be at least `0.75`
- case-level mean excess loss must remain positive
- local dynamic head and effective Reynolds number must be finite and positive
