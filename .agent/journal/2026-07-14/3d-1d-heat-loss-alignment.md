---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/fixed_mdot_parity_results.csv
  - work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/section_heat_balance.csv
  - work_products/2026-07/2026-07-13/2026-07-13_cfd_bc_no_radiation_1d_parity/section_heat_loss_comparison.csv
  - work_products/2026-07/2026-07-14/2026-07-14_3d_1d_heat_loss_alignment/summary.json
tags: [thermal-parity, heat-loss, cfd-to-1d, methodology, thesis-source]
related:
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - reports/thesis_dossier/README.md
task: AGENT-350
date: 2026-07-14
role: Implementer/Tester/Writer
type: journal
status: complete
---
# 3D / 1D Heat-Loss Alignment

## Why This Exists

The user asked for a study comparing where the 3D model loses heat and where
the 1D model loses heat, starting from the same assumptions Ethan uses: same
heater input places and same heat-removal places. Prior work had the necessary
pieces, but not one consolidated study package.

## Method

I built a diagnostic parity package from existing postprocessed evidence only.
The package compares:

- CFD imposed setup heat by segment and role.
- CFD realized wallHeatFlux by segment and role.
- 1D fixed-Q replay paths from the patch-boundary fixed-mdot package.
- Radiation-off sensitivity rows from the no-radiation package, explicitly
  labeled as sensitivity-only.

No native CFD solver outputs were mutated. No heavy OpenFOAM command or Slurm
job was run.

## Assumptions Preserved

- Positive heat means heat enters the fluid; negative heat leaves the fluid.
- `B3_imposed_setup_roles` is the same-setup fixed-Q replay lane.
- `B2_realized_wallflux_roles` is heat-accounting evidence only.
- Radiation is embedded inside CFD `rcExternalTemperature` total wallHeatFlux;
  there is no separate exported `qr` ledger.
- Radiation-off rows are not Ethan-CFD parity.
- CFD mdot and realized wallHeatFlux remain diagnostic, not setup-only
  predictive runtime inputs.

## Results

The generated package reports 90 segment alignment rows, 63 role/lane rows,
21 assumption rows, and 18 case/path summaries.

The main diagnostic result is that the imposed setup replay (`B3`) preserves
heater/test-section/cooler setup placement, but it does not reproduce realized
CFD wall-transfer locations. The upcomer/test-section lane is the largest
same-assumption discrepancy because setup heat is positive while realized CFD
wallHeatFlux is a sink. Downcomer and junction passive losses are missing from
the imposed setup replay.

This is exactly the distinction needed for thesis writing: the current evidence
can say where setup heat is placed, where CFD actually transfers heat, and
which 1D paths are expressible today. It cannot yet claim a predictive heat-loss
closure.

## Validation

Commands run:

```bash
python3.11 -m unittest tools.analyze.test_3d_1d_heat_loss_alignment
python3.11 tools/analyze/build_3d_1d_heat_loss_alignment.py
```

The unit tests passed and the package generated successfully.

## Next Work

- Add figures: stacked signed heat bars by case/segment and role/lane.
- Add a first-class Fluid external-boundary API lane so passive
  h/Ta/Tsur/emissivity/layer assumptions can be replayed directly.
- Keep this package as diagnostic support for the thermal parity and
  predictive boundary/HX blockers.
