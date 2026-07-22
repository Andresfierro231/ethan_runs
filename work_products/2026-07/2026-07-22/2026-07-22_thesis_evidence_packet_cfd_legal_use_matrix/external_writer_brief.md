# External Writer Brief

Use this packet before writing any paragraph that says "CFD shows", "the
OpenFOAM results demonstrate", or "the reduced model uses". The key discipline
is that the same CFD artifact can be strong reference evidence and still be
illegal as a predictive runtime input or closure coefficient.

Recommended placement:

- Chapter 3: use the case matrix, provenance table, Salt heat/azimuthal/
  pressure/thermal figures, and legal-use matrix to introduce the CFD evidence
  database.
- Chapter 4: use the split-role ledger and runtime-leakage audit to explain
  the CFD-to-1D reduction contract.
- Chapter 6: use the allowed/forbidden claims and trust-boundary table to
  explain admission.
- Chapter 7: use figure/table targets and key numbers as diagnostic results,
  with non-admission caveats.

Write CFD as high-fidelity reference evidence, not experiment. Keep Salt Water
scope limits. Do not promote wallHeatFlux, mdot, cooler duty, validation
temperatures, holdout rows, external-test rows, pressure-gradient diagnostics,
or upcomer velocity renders into runtime closures.
