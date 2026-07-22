# AGENT-560 F6/Two-Tap Nonrecirculating Staging

Task: `AGENT-560`

This package consumes the July 20 two-tap nonrecirculating anchor plan and
turns it into the staging handoff requested by AGENT-556. It does not stage,
submit, harvest, postprocess, fit F6, admit component `K`, clip `K`, introduce a
hidden multiplier, or invent endpoint pressures.

## Decision

`staging_complete_no_launch_from_this_row`

The preferred conditional lane remains `CAND-001`: same-topology
`corner_lower_right` sampling from Salt4 high-heat/no-recirculation probe cases
after terminal review. Current Salt2/Salt3/Salt4 `corner_lower_right` rows stay
diagnostic-only because reverse flow is material, component isolation is not
admissible, and same-QOI uncertainty is missing.

## Required Future Row

A future staged-copy sampler row may proceed only after:

- Selected high-heat/no-recirculation source cases are terminal successful or a
  replacement source family is explicitly admitted.
- The future row claims sampler/postprocessing scope and writes only to its own
  staged-copy outputs.
- Endpoint labels `lower_leg__s04` and `right_leg__s00` resolve cleanly.
- Aggregate `RAF < 0.01` and `RMF < 0.01` are computed on the same retained
  window before any ordinary-flow review.
- Same-QOI UQ is declared, or the row remains diagnostic-only.

## Files

- `source_case_selection.csv`
- `staging_contract.csv`
- `endpoint_sampling_contract.csv`
- `same_qoi_uq_family_plan.csv`
- `launch_or_no_launch_decision.json`
- `source_manifest.csv`
- `summary.json`
