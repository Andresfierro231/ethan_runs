# Claude Literature Closure-Fit Rigor Review

Date: `2026-07-08`
Role: Reviewer / Writer
Task ID: `AGENT-216`
Owner: codex

## Objective

Review Claude's literature/closure-term fit analyses for scientific rigor,
documentation honesty, post-processing provenance, limitations, and studies
needed before thesis or journal-paper use.

## Files Changed

- `operational_notes/07-26/08/2026-07-08_claude_literature_closure_fit_rigor_review.md`
- `.agent/journal/2026-07-08/claude-literature-closure-fit-rigor-review.md`
- `.agent/status/2026-07-08_AGENT-216.md`
- `journals/2026-07/2026-07-08_ethan_runs.md`
- `.agent/BOARD.md` own row

## Evidence Inspected

The review used the documented work products, status files, journals, and code
paths for:

- `F3_shah_apparent` and literature apparent-friction comparison.
- `F4_leg_class` buoyancy/friction fit.
- F4 Ri calibration and solver gate.
- `F5_ri_corrected`.
- `F6_phi_re`, self-consistent Ri diagnostics, and minor-loss separation.
- Upcomer correlation v2.
- July 8 model-form bakeoff context.
- External Fluid friction-closure implementation and tests.
- `reference/geometry_reference.md`.

The operational note lists the exact paths inspected.

## Assessment

Claude's documentation is generally honest and useful. It records source paths,
formulas, warnings, validation commands, admission boundaries, and negative
results. The work is scientifically acceptable as diagnostic post-processing,
candidate-screen development, and prototype implementation.

It is not yet scientifically acceptable as final publication-grade closure-law
evidence. The recurring blockers are small calibration sets, no held-out
validation, unresolved thermal-state mismatch, possible CFD-to-1D circularity,
no mesh/GCI uncertainty, and an unresolved control-volume issue in the minor
loss separation.

## Main Findings

- `F3_shah_apparent` is the strongest current closure element. It is a defensible
  literature baseline, but still needs primary-source constant verification and
  clear bend-fed-entry caveats.
- `F4_leg_class` is a training-set diagnostic. It fits two-parameter forms to
  three points for several leg classes and should not be treated as a closure
  law.
- The F4 Ri gate is valuable because it documents failed/inconclusive Ri forms
  instead of overclaiming.
- `F5_ri_corrected` is a negative-result scaffold. Its active coefficients are
  zeroed, so it is effectively F3 with warning metadata.
- `F6_phi_re` is useful prototype work, but it is still empirical and
  under-validated.
- Minor-loss separation should be treated only as a sensitivity study because
  the documented method subtracts adjacent bend loss from spans that are also
  described as straight-section control volumes.
- Upcomer correlation v2 is useful regime evidence, not a final closure.

## Required Future Work

Before any empirical closure fit is used for thesis or paper claims:

1. Admit corrected-Q perturbations and Salt 1 continuation data through formal
   gates.
2. Add held-out validation cases.
3. Run end-to-end model-form bakeoff after thermal-state replay is fixed.
4. Rebuild minor-loss separation with explicit physical control volumes.
5. Compare self-consistent 1D Ri diagnostics against CFD-derived Ri summaries.
6. Add mesh/time-window uncertainty bounds.
7. Preserve thermal-interface limitations separately from friction closure
   tuning.

## Validation

This was a documentation/review task. No long jobs or solver-output mutations
were performed. Targeted discoverability checks were run after writing the
documentation and are recorded in the status file.
