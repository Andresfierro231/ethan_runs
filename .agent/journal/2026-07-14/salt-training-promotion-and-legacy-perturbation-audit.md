---
provenance:
  task: AGENT-355
  generated_by: codex
tags: [journal, cfd-pp, salt, admission, split-policy]
related:
  - .agent/status/2026-07-14_AGENT-355.md
  - work_products/2026-07/2026-07-14/2026-07-14_salt_training_promotion_and_legacy_perturbation_audit/README.md
---
# Salt Training Promotion And Legacy Perturbation Audit

## Work Performed

Built a reproducible audit package for the requested Salt training-data
promotion and perturbed-Q split decisions. The package joins existing terminal
harvest, steady-state, postprocessing, BC-summary, mutation-manifest, and
matched-plane readiness evidence.

Also added documentation-focused structure to
`tools/analyze/build_submitted_cfd_run_steady_state_table.py` so future agents
can reuse the submitted-run steady-state table builder without re-discovering
its label assumptions.

## Observed Evidence

- Salt1 terminal review reports terminal harvest evidence and stationary final
  windows for nominal, lo10q, and hi10q.
- Salt2/Salt4 +/-5Q harvest job `3295437` completed and produced registered
  thermal aggregates.
- Salt4 nominal was previously treated as holdout in some tables, but the user
  explicitly moved it to training for current closure progress.
- June 19 campaign manifest reports `hiQ_balQ_baselineIns` and
  `insulation_delta_in=0.00` for `salt3_jin_hiq_hiins` and
  `salt4_jin_hiq_hiins`; those names should not be interpreted as actual
  high-insulation cases.
- The matched-plane compute runner currently does not include the harvested
  +/-5Q rows, so no valid pressure/upcomer extraction job was submitted.

## Interpretation

The package admits more thermal closure evidence without hiding remaining
gates. Salt4 nominal and Salt4 +/-5Q can be used as training rows under the
current policy. Salt2 +/-5Q can be held out. Salt1 nominal and lo10q can support
training under caveats; Salt1 hi10q requires a small conflict-resolution review
because older inventory evidence disagrees with the terminal-harvest review.

Legacy Salt4 `balq`/`hiins` rows remain sensitivity-only unless a future policy
explicitly overrides the false-steady operating-point gate. `salt3_jin_hiq_hiins`
needs continuation and source/BC restoration before use.

## Validation

Commands passed:

- `python3.11 tools/analyze/build_salt_training_promotion_and_legacy_perturbation_audit.py`
- `python3.11 -m unittest tools.analyze.test_salt_training_promotion_and_legacy_perturbation_audit`
- `python3.11 -m unittest tools.analyze.test_submitted_cfd_run_steady_state_table`

## Guardrails

No native CFD solver outputs, registry aggregate inputs, scheduler jobs, or
external `../cfd-modeling-tools` files were mutated.
