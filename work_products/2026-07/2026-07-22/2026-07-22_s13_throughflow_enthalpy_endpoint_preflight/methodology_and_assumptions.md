# Methodology And Assumptions

This package is a preflight/readiness pass for the S13 residual-complete
open-CV equation. It does not sample native solver output, run OpenFOAM,
compute `R_E_combined_W`, release cp/Qwall/source values, fit coefficients, or
score protected rows.

Method:

1. Treat the completed S13 residual contract as authoritative for required
   labels and sign convention.
2. Define the throughflow endpoint pair as the composite upcomer open CV:
   inlet `left_lower_leg:s00`, outlet `left_upper_leg:s04`, positive in the
   nominal main-throughflow direction.
3. Audit completed evidence for exact same-basis labels. Historical coarse
   endpoint temperatures and postProcessing mdot/probe statistics are allowed
   as diagnostic support only.
4. Fail closed unless every case has same-window endpoint masks, normals,
   `T_in_bulk_K`, `T_out_bulk_K`, `mdot_throughflow_kg_s`, released cp,
   storage, named-loss lanes, and same-window heat-flow rows.
5. Emit a command contract for a future staged compute row, but do not launch
   that row here.

Assumptions:

- Historical coarse endpoint samples are useful for geometry/method sanity but
  are not current S13 residual rows.
- Existing postProcessing mdot values describe loop stability and uncertainty
  context, but CFD mdot remains forbidden as a predictive runtime input.
- Existing S13 exact-label rows describe exchange-cell QOIs; they do not
  substitute for throughflow endpoint enthalpy.
- Missing storage or named-loss terms keep the residual incomplete rather than
  being absorbed into internal Nu or a hidden multiplier.
