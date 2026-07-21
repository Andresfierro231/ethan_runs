---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/pressure_basis_decision.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/stage_b_pair_reconstructed_static_deltas.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/f6_gate_refresh.csv
tags: [f6, pressure-basis, p-rgh, hydrostatic, diagnostic, no-admission]
related:
  - .agent/status/2026-07-21_TODO-F6-STATIC-P-BASIS-RECONSTRUCTION-AUDIT.md
  - imports/2026-07-21_f6_static_p_basis_reconstruction_audit.json
task: TODO-F6-STATIC-P-BASIS-RECONSTRUCTION-AUDIT
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Reviewer / Tester / Writer
type: journal
status: complete
---

# F6 Static Pressure Basis Reconstruction Audit

## Attempted

I claimed the open F6 static-pressure audit row and first tried to add reusable
`tools/analyze/` scripts. The task preflight rejected that scope because another
open row owns broad `tools/analyze/` paths. I narrowed this task to
package-local scripts under the F6 work product, reran preflight, and proceeded
without overlapping the other row.

I then built a reproducible audit that joins the combined Stage A/B face QA with
the Stage A and Stage B endpoint coordinate matrices. The script inventories
available fields and `constant/g`, evaluates two hydrostatic sign conventions,
validates them against Stage A static-pressure pair deltas, and applies the
validated convention to coarse Stage B rows only as diagnostic evidence.

## Observed

Stage A medium/fine has `8` validation faces with sampled `p`, `p_rgh`, `rho`,
and station coordinates. Stage B coarse has `12` candidate faces with sampled
`p_rgh` and `rho` but no sampled `p`. All inspected case roots parse
`g=(0 -9.81 0)`.

The OpenFOAM-style convention `p = p_rgh + rho * (g dot x)` passes all `4/4`
Stage A pair-delta checks. Its max absolute pair-delta error is
`4.38272935163 Pa`, below the adopted threshold for each pair. The opposite sign
passes `0/4` and fails by thousands of Pa.

Applying the validated convention to Stage B gives finite diagnostic static
pressure deltas for Salt2/Salt3/Salt4 right-leg and test-section-span pairs.
Those rows remain `diagnostic_reconstructed_not_admitted`.

## Inferred

The missing coarse static-`p` basis can be reconstructed for pairwise diagnostic
pressure comparisons. This resolves the sign/gravity basis question for the
current F6 coarse rows, but it does not change the admission outcome.

The decisive scientific limitation is no longer merely missing static `p`.
F6 still fails ordinary-flow gating: the prior Stage A/B gate refresh reports
`0/10` endpoint pairs passing RAF/RMF, and same-QOI mesh/UQ is still blocked.
Therefore, reconstructed coarse static pressure is useful for explanation and
publication audit trails, not for F6 fitting or component/cluster `K`.

## Contradictions Or Caveats

Absolute pressure reconstruction is less important than pair deltas because CFD
pressure references can carry arbitrary offsets. In this dataset the selected
convention also gives small face errors, but the audit decision is deliberately
based on pairwise deltas.

This audit does not prove ordinary one-dimensional loss behavior in recirculating
F6 endpoint regions. It only shows that the hydrostatic reconstruction from
`p_rgh` is internally consistent where sampled `p` exists.

## Next Useful Actions

Use `TODO-PRESSURE-F6-PUBLICATION-CLAIM-FREEZE` to update the publication-facing
F6 pressure claim boundary with this diagnostic static-pressure-basis result.
The claim should say that coarse static pressure is reconstructable for
diagnostic pair deltas, but F6/component-K admission remains closed.

The next admission-relevant scientific work is still an ordinary-flow/source
family search or low-recirculation anchor study. Do not fit F6, clip negative
loss, introduce a global multiplier, or promote these reconstructed values to
component/cluster `K`.
