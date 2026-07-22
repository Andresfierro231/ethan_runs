---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_candidate_cp_mu_k_train_support_sensitivity_preflight/README.md
tags: [journal, property-sensitivity, train-support, source-envelope]
related:
  - .agent/status/2026-07-22_TODO-CANDIDATE-CP-MU-K-TRAIN-SUPPORT-SENSITIVITY-PREFLIGHT-2026-07-22.md
  - imports/2026-07-22_candidate_cp_mu_k_train_support_sensitivity_preflight.json
task: TODO-CANDIDATE-CP-MU-K-TRAIN-SUPPORT-SENSITIVITY-PREFLIGHT-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Tester / Writer / Reviewer
type: journal
status: complete
---
# Candidate cp/mu/k Train/Support Sensitivity Preflight

## Attempted

Claimed the property sensitivity unlock as a bounded preflight and opened the
current property package gate, strict source-envelope recovery, MF12 formula
gate, model-form roster, and source/property pressure-basis preflight.

## Observed

The named property family is `jin_viscosity_parida_cp_santini_k`, but the
current release decision is sensitivity-only. MF12 is a high-value thermal
projection candidate, but it requires source-bounded source terms, cp release,
reset/source labels, and same-QOI projection support. Strict source-envelope
repair reports `0` strict-pass rows and `0` source/property release rows.
CAND001 pressure endpoint readiness is still blocked by a running scheduler job.

## Inferred

The useful work now is to lock the algebraic sensitivity pathways and split
policy, not to run final calibration. First-order effects are well-defined:
`Re ~ 1/mu`, `Pr ~ cp*mu/k`, `Gz ~ cp/k` under a fixed-flow basis, source
temperature rise scales as `1/(mdot*cp)`, and wall/layer conduction resistance
scales as `1/k`.

## Caveats

Salt3/Salt4 split labels conflict across current packages. This preflight does
not resolve the split or score those rows; it treats them as support/context
metadata where needed and blocks protected scoring.

## Next Useful Actions

1. Repair row-specific source-envelope evidence until at least one strict-pass
   row exists.
2. Publish candidate-specific cp/mu/k source paths and validity intervals.
3. Wait for CAND001 terminal handoff before pressure endpoint readiness.
4. Only after those pass, run train/support property sensitivity with fixed
   candidate equations and no protected-row model selection.
