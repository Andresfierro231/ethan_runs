---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_label_mesh_family_generation/same_label_mesh_family_generated_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_label_mesh_family_inventory_and_generation_contract/generation_contract.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus/same_qoi_temporal_uq_case_rows.csv
  - work_products/2026-07/2026-07-09/2026-07-09_salt_mesh_refinement_followon_readiness/endpoint_postprocessing_family_coverage.csv
  - /home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs/salt/medium
  - /home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs/salt/fine
tags: [s13, upcomer-exchange, medium-fine, mesh-gci, same-label]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-MEDIUM-FINE-SAME-LABEL-SAMPLING-2026-07-22.md
  - .agent/journal/2026-07-22/s13-upcomer-exchange-medium-fine-same-label-sampling.md
task: TODO-S13-UPCOMER-EXCHANGE-MEDIUM-FINE-SAME-LABEL-SAMPLING-2026-07-22
date: 2026-07-22
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# S13 Medium/Fine Same-Label Sampling Preflight

Decision: `medium_fine_runs_exist_exact_s13_rows_absent_sampling_contract_ready`.

The medium and fine Salt2/Salt3/Salt4 source runs are present and readable.
The missing item is narrower: exact S13 medium/fine rows have not yet been
sampled for the four labels, masks, formula/sign basis, and window policy used
by the current-coarse S13 evidence.

- Medium/fine source run rows inventoried: `6`
- Existing source runs available: `6`
- Medium/fine exact S13 sampling need rows: `24`
- Need rows with terminal primitive fields ready: `24`
- Need rows with strict coarse-contract windows already present: `0`
- Existing exact S13 medium/fine rows: `0`
- Mesh/GCI ready now: `false`
- Scheduler/sampler launched: `false`

How to use the postprocessing already done:

1. Treat it as source/provenance and sanity-check evidence for available fields,
   stationarity, and endpoint behavior.
2. Do not relabel pipeleg mdot, velocity profiles, probe means, wall gross/net
   duty, or July 9 endpoint GCI rows as S13 exchange rows.
3. Use the medium/fine native fields at the listed terminal candidate windows
   to run the exact S13 sampler over mesh-level trusted wall, exchange
   interface, recirculation CV, and wall/core/bulk masks.

The next row should run compute-node sampling from `sampling_command_contract.csv`.
If exact target-window directories remain absent for medium/fine, that row must
either prove a terminal-window mesh-time equivalence gate or publish a
fail-closed mesh/GCI result with only temporal UQ accepted.
