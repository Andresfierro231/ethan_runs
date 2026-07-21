---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/README.md
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/paper_methods_pressure_basis.md
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/paper_results_current_evidence.md
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/pressure_velocity_basis_audit.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/endpoint_recirculation_metrics.csv
tags: [thesis-section, current-section, two-tap, pressure-ledger, recirculation, section-effective]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/04_upcomer_recirculation_modeling.md
  - reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md
task: TODO-TWO-TAP-RECIRC-SECTION-EFFECTIVE-MODEL
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: thesis-section
status: current-draft
supersedes: []
superseded_by:
---
# Two-Tap Recirculating Section-Effective Pressure Model

## Why Ordinary Component K Is Blocked

The current Salt2/Salt3/Salt4 `corner_lower_right` two-tap rows have finite
endpoint pressure and velocity fields, but they do not satisfy ordinary
component-loss admission gates. All three current rows fail material
reverse-flow gates, route to `apparent_cluster_only` rather than a clean
component-isolated feature, and lack a same-label/same-formula/same-sign
mesh/time uncertainty family.

The static endpoint pressure differences are also not local component losses by
themselves. They are approximately the same size as the hydrostatic correction,
so the static apparent `K` values are hydrostatic/buoyancy-dominated diagnostic
quantities. The `p_rgh` endpoint differences are small under the preserved
downstream-minus-upstream sign convention. The paper should therefore avoid any
sentence that implies the static apparent `K` has already been locally corrected
for buoyancy or admitted as component `K`.

## Recirculation-Aware Model Form

The scientific way to continue is to stop treating recirculation as a failed
ordinary-pipe row and instead model it explicitly. The current package defines
a section-effective pressure residual:

```text
Delta_p_resid = Delta_p_rgh - Delta_p_kin - Delta_p_straight - Delta_p_dev
K_eff_recirc = Delta_p_resid / q_ref
```

`q_ref` is a same-window throughflow dynamic-pressure basis from net positive
mass flux across the endpoint surfaces. If the throughflow denominator is near
zero, the row must return a no-fit diagnostic status rather than a large
coefficient. This keeps the recirculation pressure term separate from ordinary
straight-pipe friction, clean component losses, and F6 promotion.

## Paper-Safe Claims

- Current `corner_lower_right` two-tap rows are diagnostic evidence for
  pressure-basis review, recirculation gating, and model-form selection.
- Current rows do not admit ordinary `component_K`, ordinary single-stream `K`,
  or F6 fits.
- The next hydraulic model form should be a throughflow lane plus a named
  recirculating section-effective pressure-residual lane.
- A non-recirculating anchor and same-QOI mesh/time uncertainty family are
  required before ordinary component `K` can be revisited.

## Figure And Table Hooks

The paper-ready source package provides a pressure-basis decomposition table,
current-row recirculation/admission table, model-form decision table, claim and
limitation ledger, artifact crosswalk, and figure/table manifest. Use those
tables before drafting results prose so every claim carries its admission state
and caveat.

## Open Needs

- same-QOI mesh/time uncertainty for the section-effective residual;
- a future non-recirculating anchor row if ordinary component `K` is revisited;
- split-safe scoring that shows a named recirculation pressure penalty improves
  pressure residual prediction without using held-out pressure at runtime;
- continued separation between hydrostatic basis correction, local residuals,
  component isolation, and F6 promotion.
