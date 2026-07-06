# AGENT-123 Raw Journal — Latest-Window Discrepancy Explainer

- date: `2026-06-23`
- role: `Coordinator / Implementer / Writer`
- task ID: `AGENT-123`
- purpose:
  - quantify persistent 1D-vs-CFD discrepancies on the refreshed June 23
    latest-window surface
  - separate supported explanations from still-uncertain hypotheses
- questions accumulating:
  - Does the current evidence justify treating the upcomer only as a
    convection-cell-style residual branch in the discrepancy write-up, or do we
    have enough branchwise evidence to recommend a more specific reduced-order
    closure shape already?
- progress notes:
  - The first discrepancy-builder draft assumed the defended case rows lived in
    the validation package. That was wrong: they live under the bakeoff
    package’s `defended_full_coverage_surface`, and the script now reads them
    from there.
  - The script also now falls back to the validation package’s
    `cfd_branch_profile_summary.csv` when a frozen package lacks the newer
    `branch_development_summary.csv`, which made the smoke path work against
    the older June 22 stack while preserving the direct latest-window path for
    the new freeze package.
