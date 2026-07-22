---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_residual_complete_open_cv_energy_balance_contract/throughflow_enthalpy_harvest_contract.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/aggregated_terminal_window_reductions.csv
  - work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/interface_temperature_samples.csv
tags: [journal, s13, throughflow, enthalpy, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-S13-THROUGHFLOW-ENTHALPY-ENDPOINT-PREFLIGHT-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_enthalpy_endpoint_preflight/README.md
  - imports/2026-07-22_s13_throughflow_enthalpy_endpoint_preflight.json
task: TODO-S13-THROUGHFLOW-ENTHALPY-ENDPOINT-PREFLIGHT-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Hydraulics / cfd-pp / Forward-pred / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# S13 throughflow enthalpy endpoint preflight

## Attempted

Converted the completed S13 residual-open-CV contract into a concrete endpoint
preflight. The pass defined the composite upcomer throughflow endpoints,
audited existing exact-label S13 rows, checked source/property cp status, and
summarized compact postProcessing mdot/T support.

## Observed

The historical coarse interface sampler already has upcomer endpoint
temperature rows for Salt2/Salt3/Salt4. Those rows define a practical contract:
`left_lower_leg:s00` to `left_upper_leg:s04`, positive in nominal main
throughflow direction. The inlet endpoint remains strongly recirculating in the
historical data, with maximum endpoint recirculation ratios from about `0.85`
to `0.90`.

The current S13 medium/fine exact-label package has exchange-cell evidence but
does not contain `H_throughflow_net_W`, endpoint `T_bulk`, or
`mdot_throughflow_kg_s`. The postProcessing inventory has mdot and temperature
statistics for all three nominal Jin cases, but those values remain
diagnostic-only and are not endpoint-face enthalpy integrals.

## Inferred

S13 can continue, but not by computing a residual from available tables. The
next scientific row must stage same-window endpoint face masks, normals,
endpoint `T_bulk`, and throughflow `mdot` for the composite upcomer CV. Even
after that sampler lands, residual use remains blocked until cp/source-property
release and storage/named-loss lanes are handled.

## Contradictions Or Caveats

Some existing S13 rows say `Q_wall_W_released=true` inside exact-label sampler
outputs, but this task keeps Qwall predictive/admission release closed because
the formal source/property/GCI/admission gates remain closed. The flag is
treated as sampler-local exact-label availability, not a model-release permit.

## Next Useful Actions

Claim a staged same-window throughflow endpoint sampler row for Salt2, Salt3,
and Salt4. Use a staged case copy, write the endpoint sampling controlDict only
inside that staged copy, run OpenFOAM sampling on a compute node, then parse
endpoint samples. Do not compute `R_E_combined_W` until cp, storage, named-loss,
and same-window heat-flow joins are all ready.
