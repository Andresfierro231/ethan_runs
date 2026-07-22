# Diagnostic CFD-Realized Heat-Loss Replay And Predictive Loss Plan

Task: AGENT-410  
Generated: 2026-07-15

## Direct Answers

**Did we try running the 1D model with heat losses placed exactly where the CFD
model realizes them?** Yes. The prior heat-loss alignment package contains the
`B2_realized_wallflux_roles` lane, and this addendum extracts it into
`diagnostic_forced_cfd_heat_loss_replay.csv`. It forces each 1D section net heat
path to match the CFD-realized `wallHeatFlux` location for Salt2, Salt3, and
Salt4.

**Can we present it as predictive?** No. It is valuable as a leakage diagnostic
and physical limit case, but it consumes realized CFD `wallHeatFlux`, which is a
target/output. The proper label is `diagnostic_only_not_predictive`.

**Can we train on Salt1, Salt2, Salt3, Salt4 and test on other CFD runs?** Not
yet as a thesis-strength generalization claim. A user-policy training table
exists for Salt1/Salt4-family rows with Salt2 +/-5Q as holdout screening, but
that policy must not be mixed with the older Salt2 train / Salt3 validation /
Salt4 holdout split. Other CFD runs need matching heat-loss ledgers, source/sink
contracts, boundary dictionaries, and admission labels before they become an
independent test set.

**Can we test on val_salt2?** Not yet for the section heat-loss variant. The
val_salt2 lineage and Jin-vs-val comparison report exists, but a current
AGENT-350-style thermal section heat-loss replay/admission package for val_salt2
was not found in this addendum's scoped evidence. It is a good future test after
that extraction lands.

**Did we produce a Jin Salt2 versus val Salt2 report?** Yes. AGENT-354 produced
`work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/`,
including `salt2_jin_comparison.csv`.

## Forced-Replay Result

- Forced replay rows: 15
- Cases covered: 3
- Segments per case: lower leg, upcomer, cooling branch, downcomer, junction.
- Maximum segment net residual after forcing: 0 W.
- Predictive rows admitted from this replay: 0.

The forced replay proves that exact location matching is possible if we use CFD
outputs. The scientific task is now to predict those losses from setup
quantities: junction/stub coverage, wall/shell drive, external h/Ta/Tsur/
emissivity/layers, and setup-only HX/cooler behavior.

## Files

- `diagnostic_forced_cfd_heat_loss_replay.csv`
- `diagnostic_forced_replay_case_summary.csv`
- `train_test_data_sufficiency.csv`
- `jin_vs_val_salt2_report_status.csv`
- `predictive_heat_loss_variant_plan.csv`
- `source_manifest.csv`
- `summary.json`
