# Water Extension TODO

1. Rebuild the feature hydraulic hardening package on the preserved water-family
   raw case-analysis roots using the same local-boundary-reference method.
2. Rebuild the thermal closure package with the exact water-side `rho*u*cp`
   property convention already established in the June 17 pressure / HTC /
   boundary-layer package.
3. Reapply the same closure gates used here:
   - no derived overlapping branches in defended fitting
   - explicit branch support and `|Twall - Tbulk|` thresholds
   - explicit enthalpy-vs-wall residual threshold
   - explicit direct-vs-shear hydraulic disagreement reporting
4. Publish a water-family dependency package only after the closure-supported
   water rows are counted and sensitivity-tested separately from Salt.
