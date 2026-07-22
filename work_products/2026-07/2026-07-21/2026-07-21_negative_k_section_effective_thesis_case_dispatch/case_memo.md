---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/pressure_corner_extraction_findings.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/pressure_corner_basis_recovery_audit.csv
  - work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/section_effective_pressure_scorecard.csv
tags: [negative-k, section-effective, component-k-gate, thesis]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_negative_k_section_effective_thesis_case_dispatch/README.md
task: TODO-NEGATIVE-K-SECTION-EFFECTIVE-THESIS-CASE-DISPATCH-2026-07-21
date: 2026-07-21
role: Writer/Reviewer
type: memo
status: complete
---
# Case For Stopping Component-K Attempts On Current Corner Rows

## Claim

The current Salt2/Salt3/Salt4 `corner_lower_right` two-tap rows should not be
used to fit, admit, or tune ordinary component `K`. They should be used as:

- a clean negative result for component/coefficient admission;
- a pressure-basis and recirculation diagnostic;
- thesis evidence motivating a throughflow-plus-recirculation
  section-effective pressure term named `Delta_p_recirc_section`.

## Reasoning

The literature review did not license a negative component loss coefficient for
the TAMU lower-right corner. It gave a stricter interpretation rule: separate
static pressure rise from hydrostatic head, kinetic pressure change, source
definition, pressure recovery, straight/developing reference, and component
isolation before naming a coefficient.

That rule changes the scientific question. The current rows no longer ask,
"what negative component `K` should be fit?" They ask, "what residual remains
after the admissible pressure-basis terms are separated, and can that residual
be carried as section-effective evidence without pretending it is a universal
minor-loss coefficient?"

The current evidence answers the second question but not the first.

## Observed Evidence

All three rows have gross static pressure rise of about `3.0 kPa`, but the rise
is hydrostatic dominated. After hydrostatic and kinetic correction, the
available signed residual is small and negative:

- Salt2: `-1.25366731683 Pa`;
- Salt3: `-1.84957005859 Pa`;
- Salt4: `-1.67833900273 Pa`.

The rows also have material reverse-flow diagnostics:

- reverse area fraction about `0.763`;
- reverse mass fraction about `0.500`;
- secondary velocity fraction about `0.800`.

The ordinary gates therefore fail: no same-basis straight/developing reference,
no component isolation, no same-QOI UQ, and no low-recirculation condition.

## What The Hybrid Term Does

The allowed section-effective term is:

```text
Delta_p_recirc_section = q_ref * K_eff_recirc
```

This is a diagnostic residual term tied to the recirculating section. It is not
ordinary component `K`, not F6, not a global friction multiplier, and not a
sign-clipped loss.

The current no-refit performance check uses Salt2 `K_eff_recirc` as a frozen
diagnostic transfer to Salt3/Salt4. It gives sub-Pa residual errors relative to
the already-small section residual. This makes the term thesis-useful as
quantified model-form evidence, while still falling short of predictive
candidate admission.

## Thesis Framing

The thesis should present this as a negative result with a constructive
consequence:

1. Ordinary component `K` was attempted and rejected because the required
   pressure basis, isolation, recirculation, and UQ gates did not pass.
2. The negative apparent `K` is not clipped or reinterpreted as energy
   generation.
3. The remaining signed residual is preserved as section-effective evidence.
4. That evidence motivates a hybrid pressure route where recirculating sections
   get an explicit residual ledger instead of being forced into single-stream
   coefficient form.

## Still Forbidden

The current rows must not be used for component `K`, cluster `K`, ordinary
single-stream `K`, F6 fitting, hidden/global multipliers, coefficient tuning,
protected split scoring, validation evidence, holdout evidence, or external-test
generalization.
