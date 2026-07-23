---
provenance:
  - tools/analyze/build_passive_h2_salt1_junction_patchset_reconciliation.py
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_patchset_reconciliation/junction_patch_delta_table.csv
tags: [journal, passive-h2, salt1, junction, mesh-area]
related:
  - .agent/status/2026-07-22_TODO-PASSIVE-H2-SALT1-JUNCTION-PATCHSET-RECONCILIATION-2026-07-22.md
  - operational_notes/07-26/22/2026-07-22_PASSIVE_H2_SALT1_JUNCTION_PATCHSET_RECONCILIATION.md
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_patchset_reconciliation
task: TODO-PASSIVE-H2-SALT1-JUNCTION-PATCHSET-RECONCILIATION-2026-07-22
date: 2026-07-22
role: Forward-pred / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# Passive-H2 Salt1 Junction Patchset Reconciliation

## Attempted

Audited the Salt1 PASSIVE-H2 junction area mismatch exposed by the mesh-area
preflight. The row compared patch-level direct setup-mesh areas against the
recovered junction patch inventory, then grouped the deltas by core junction
body, stub, and extension patches.

No Fluid solve, scheduler action, native-output edit, registry/admission
mutation, source/property release, fit, freeze, or protected score was
performed.

## Observed

- All `18` junction/stub patches were available in the prior setup-mesh
  evidence.
- Four patches failed tolerance: `junction_lower_left`,
  `junction_lower_right`, `junction_upper_right`, and `junction_upper_left`.
- Those four patches are the `core_junction_body` subgroup.
- The core junction-body subgroup accounts for essentially all of the
  family-area delta: `9.533943148655466e-06 m2`.
- Stub and extension subgroup deltas are roundoff-scale:
  `1.6213159287348233e-14 m2` and `1.6431439542330395e-12 m2`.

## Inferred

The remaining Salt1 area blocker is not a missing junction/stub patch or an
incorrect 18-patch family membership. It is a recovered-area mismatch on the
four core junction-body patches. A direct setup-mesh area replacement for the
same patchset clears the area-only diagnostic gate.

This matters because it narrows the release path. The next useful candidate
work does not need another junction patch search; it needs source/property and
same-QOI UQ gates for a five-family candidate whose area basis is direct setup
mesh.

## Contradictions Or Caveats

- The corrected five-family CSV is diagnostic. It changes area provenance only
  and does not prove physical source/property validity.
- The h values still originate from the upstream recovered operator evidence;
  this row did not release or refit heat-transfer coefficients.
- No train, validation, holdout, or external-test score was emitted.

## Next Useful Actions

1. Open a source/property gate row for the five-family direct-setup-mesh-area
   diagnostic candidate.
2. Require same-QOI release UQ and provenance labels before any S11/S15 freeze.
3. If source/property gates still fail, document the remaining blocker as h
   provenance rather than area provenance.
