---
provenance:
  - .agent/status/2026-07-22_TODO-PASSIVE-H2-SALT1-JUNCTION-PATCHSET-RECONCILIATION-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_patchset_reconciliation/summary.json
tags: [passive-h2, salt1, junction, start-here, no-release]
related:
  - operational_notes/07-26/22/2026-07-22_PASSIVE_H2_CONTEXT_HANDOFF.md
  - operational_notes/07-26/22/2026-07-22_PASSIVE_H2_SALT1_MESH_AREA_PROVENANCE_REPAIR_PREFLIGHT.md
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_patchset_reconciliation/README.md
task: TODO-PASSIVE-H2-SALT1-JUNCTION-PATCHSET-RECONCILIATION-2026-07-22
date: 2026-07-22
role: Forward-pred / Implementer / Tester / Writer / Reviewer
type: operational_note
status: complete
---
# PASSIVE-H2 Salt1 Junction Patchset Reconciliation

## Why This Exists

The Salt1 PASSIVE-H2 mesh-area preflight found complete setup patch coverage
but failed the `junction` family-area tolerance gate. This note records the
follow-up that determines whether the mismatch is missing patch membership,
bad grouping, or stale recovered areas.

## Files To Open First

- `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_patchset_reconciliation/README.md`
- `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_patchset_reconciliation/junction_subgroup_area_delta.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_patchset_reconciliation/five_family_mesh_area_candidate_diagnostic_only.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight/family_area_reconciliation.csv`

## Result

The same 18 junction/stub patches are the correct working patchset for the
area-only diagnostic candidate. The mismatch localizes to the four core
junction-body patch areas. Stubs and extensions are already consistent with the
direct setup mesh.

The direct setup-mesh junction area is `0.04248832812746472 m2`; the recovered
operator area was `0.042478794186 m2`. The resulting hA change is
`9.218894588086668e-05 W/K`.

## Output Contract

Use this package only for area-provenance reasoning. It may support a future
source/property gate by showing that Salt1 five-family area coverage is no
longer the controlling blocker when direct setup-mesh area is used.

Do not cite it as a Fluid result, fitted model, source/property release,
Qwall/q-loss release, validation score, holdout score, external-test score,
coefficient admission, or frozen predictive candidate.

## Next Task Sequence

1. Candidate-specific source/property gate for the five-family direct
   setup-mesh-area diagnostic candidate.
2. Same-QOI release UQ check for the same candidate.
3. Only after both gates pass, open a freeze/scoring row under the legal
   split policy.
