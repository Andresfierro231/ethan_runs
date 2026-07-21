---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_resolution/README.md
  - work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_resolution/leg_specific_internal_nu_candidate_rows.csv
  - work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_resolution/mesh_gci_gate_for_admitted_candidates.csv
tags: [closure-qoi, internal-nu, upcomer, blocker-narrowing]
related:
  - .agent/status/2026-07-16_AGENT-455.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/geometry-and-mesh-truth.md
task: AGENT-455
date: 2026-07-16
role: Coordinator/cfd-pp/Internal-Nu/Implementer/Tester/Writer
type: journal
status: complete
---
# Closure-QOI Mesh-GCI Resolution

## Why This Avenue Exists

The current Internal-Nu question had a possible shortcut: omit the recirculating
upcomer and fit separate Nu correlations on other legs. The geometry map blocks
one unsafe version of that shortcut because the test section is in the middle of
the upcomer. AGENT-455 exists to turn that into a row-level admission decision,
not a verbal rule.

## Observed

The generated package confirms `test_section_span` is part of
`upcomer_left_vertical`. It reviewed `50` leg-specific Internal-Nu candidates:
`35` are hybrid recirculation lane only, `5` are validation-only nonfit, `7` are
blocked/diagnostic nonfit, and `3` are waiting on branch rows. Current
fit-admissible Internal-Nu rows remain `0`.

The package also reviewed the `25` Closure-QOI/GCI rows from AGENT-450. There
are `0` publication-ready Closure-QOI/GCI rows and `13` unresolved mesh or
admission rows after diagnostic upcomer/hybrid rows are separated.

## Inferred

The blocker is not removable today by dropping only the upcomer. Dropping the
upcomer also drops the test section from ordinary single-stream Internal-Nu
fitting, and the remaining non-upcomer legs still lack branch-local rows that
pass sign/heat-balance/source ownership, residual separation, recirculation, and
same-QOI mesh/GCI gates.

The LitRev theory is now encoded as a gate sequence: separate boundary/source/
storage/radiation/branch-mixing residuals first, then fit only leg-specific
internal convection on rows admitted for that purpose.

## Blocker Action

`.agent/blockers.yml` keeps `closure-qoi-mesh-gci` open and updates the evidence
to AGENT-455. It also updates `upcomer-onset-data-sparsity` to record that the
test section is an upcomer subspan and the upcomer lane remains hybrid/onset,
not conventional single-stream Nu.

## Next Task Sequence

1. Resolve branch-local sign/enthalpy/source ownership for the heater/lower-leg
   thermal rows without fitting residuals into Internal-Nu.
2. Decide the downcomer/right-leg thermal policy and extract or admit low-
   recirculation non-upcomer rows.
3. Keep cooler/HX in the setup-only UA/effectiveness lane until HX removal and
   shell/boundary residuals are separated from internal convection.
4. Recompute same-QOI mesh/GCI only on rows that pass admission and remain in
   the final closure set.
5. Treat upcomer/test-section rows as hybrid recirculation/onset evidence unless
   a later row explicitly admits a low-recirculation sublane.

## Do-Not-Do Guardrails

Do not use test-section rows as a separate non-upcomer Nu fit. Do not tune
Internal-Nu to absorb heater, cooler/HX, wall/layer, storage, radiation,
passive-boundary, or recirculation residuals. Do not mutate native solver
outputs, registry/admission state, scheduler state, or external Fluid sources
from this package.
