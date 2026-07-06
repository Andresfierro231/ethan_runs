# AGENT-122 Raw Journal — Latest-Window 1D Retarget

- date: `2026-06-23`
- role: `Coordinator / Implementer / Writer`
- task ID: `AGENT-122`
- purpose:
  - rebuild the local 1D-vs-CFD validation surfaces against the June 23
    latest-window frozen contract
  - keep the readable external `Fluid` boundary explicit while publishing
    current CFD-last-window comparison tables
- questions accumulating:
  - Do we want the latest-window validation package to keep the old two-tier
    `comparison_candidate` versus `convergence_audit_required` framing, or is
    the nominal four-case Jin-only surface better treated as one bounded
    provisional comparison class?
- progress notes:
  - The validation and bakeoff builders now follow the chosen frozen directory
    name in their README and import-manifest wording, so the latest-window
    refresh will not keep citing the June 22 package after retargeting.
  - Smoke outputs against the current June 22 frozen package succeeded in the
    dedicated tmp roots and confirmed that the dated CFD-last-window tables and
    setup note still regenerate after the dynamic-label changes.
