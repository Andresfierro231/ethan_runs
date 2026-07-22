# TSWFC2 Salt 2 Four-Node Smoke Scenario

- Task: `AGENT-553`
- Decision: `smoke_passed_no_grid`
- Case: `Salt 2`
- Scenario: `tswfc2_smoke_salt2_four_node_v1`
- Model mode: `predictive_airside_hx`
- TSWFC2 mode: `distributed_wall_fluid_nodes_v1`
- Score grid/admission: none; smoke only.

## Result

- Root status: `accepted`
- Accepted for validation metrics: `True`
- Pressure root bracketed: `True`
- Temperature root bracketed: `True`
- mdot: `0.022190917` kg/s
- Temperature periodicity error: `8.84710971e-10` K
- Active TSWFC2 ledger rows: `4`
- Active TSWFC2 node-count sum: `4`
- Expected nodes present: `True`
- Sum |q external|: `43.7432402` W
- Max |TSWFC2 residual|: `0` W

## Files

- `scenario_contract.yaml`: bounded four-node scenario contract.
- `scenario_records.csv`: Fluid parser export for the one scenario.
- `runtime_input_audit.csv`: setup-only guardrails and forbidden runtime inputs.
- `root_status.csv`: root and bracket acceptance flags.
- `finite_output_audit.csv`: finite numeric smoke outputs.
- `tswfc2_segment_ledger.csv`: active nonzero TSWFC2 ledger rows.
- `case_outputs/Salt_2/summary.csv`: Fluid native case summary with no validation record.
- `case_outputs/Salt_2/segment_states.csv`: Fluid native segment-state output.
- `no_admission_review.csv`: explicit no-grid/no-fit/no-admission review.
- `summary.json`: machine-readable task summary.

## Guardrails

This package did not edit Fluid source/configs, native CFD outputs, registry/admission state, scheduler state, or source/property tables. The run is a single smoke acceptance check, not a scored candidate campaign.
