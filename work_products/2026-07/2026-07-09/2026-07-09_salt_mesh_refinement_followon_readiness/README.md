# Salt Mesh-Refinement Follow-On Readiness

Generated: `2026-07-09T10:42:32-05:00`

## Summary

This package implements the read-only follow-on plan after AGENT-228. It
reconciles external coarse endpoint sources, merges full-history endpoint
postProcessing monitors, and computes screening GCI diagnostics where complete
triplets exist. It does not stage, register, submit continuations, update
closure observations, or mutate native solver outputs.

## Outputs

- `coarse_reconciliation.csv`: external coarse Salt 2/4 Jin source status versus
  current mainline continuations.
- `endpoint_full_history_monitor_summary.csv`: merged restart-segment monitor
  summaries for Salt 2/4 Jin coarse/medium/fine.
- `endpoint_postprocessing_family_coverage.csv`: postProcessing coverage by
  family, including velocity-profile snapshot coverage.
- `mesh_uq_readiness.csv`: per-QoI readiness and blocker table.
- `gci_results.csv`: numeric screening GCI diagnostics for complete triplets,
  with publication readiness kept separate.
- `closure_observation_mesh_uq_handoff.md`: downstream observation-table update
  guidance.

## Observed Facts

- Coarse reconciliation verdict counts: `{'superseded_by_mainline': 2}`.
- Monitor row count: `90`.
- Mesh-UQ readiness counts: `{'blocked_coarse_superseded_by_mainline': 18, 'blocked_requires_mesh_level_extraction': 6}`.
- Publication-ready GCI rows: `0`.

## Interpretation

The package intentionally keeps numeric screening GCI separate from admitted
mesh uncertainty. Salt 2 has complete endpoint monitor triplets, but its external
coarse source is marked as superseded by the repo's mainline continuation. Salt 4
has complete monitor triplets for some QoIs but medium/fine remain blocked by
the earlier quality gate. Pressure/thermal closure QoIs such as debuoyed
friction and Nu/HTC still require medium/fine extraction before GCI can be
computed.
