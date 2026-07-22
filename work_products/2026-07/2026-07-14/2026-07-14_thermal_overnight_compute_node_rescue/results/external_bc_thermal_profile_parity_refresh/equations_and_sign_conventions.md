# Equations and Sign Conventions

## Heat Loss Sign

This package reports `*_loss_W` as positive when heat leaves the fluid/control
volume. Native OpenFOAM `realized_wallHeatFlux_W` signs are converted only for
diagnostic loss columns:

```text
realized_external_loss_W = -realized_wallHeatFlux_W
```

for passive ambient, junction, and cooler roles. Heater realized heat remains a
source/sink contract quantity and is not treated as passive external loss.

## Leg Discrepancy

```text
model_minus_cfd_realized_loss_W
  = model_total_loss_W - cfd_realized_loss_W
```

Positive means the 1D model loses too much heat in that leg. Negative means it
loses too little heat there.

## External Boundary Contract

The segment-equivalent external boundary preserves the CFD setup fields:

```text
hA = sum_patches(h_patch * A_patch)
Ta = setup ambient temperature
Tsur = setup radiative surroundings temperature
epsilon = setup emissivity
layer metadata = wall/insulation resistance contract
```

Radiation is not added to realized CFD `wallHeatFlux` replay. It belongs in the
setup/predictive external-boundary model.

## Thermal Drive Diagnostic

The wall-profile diagnostic compares bulk/path temperature against existing
wall-shell proxy temperature:

```text
wall_shell_minus_path_bulk_K = T_wall_shell_K - T_path_bulk_K
```

If the 1D model over-loses heat while the wall-shell proxy is cooler than the
bulk/path temperature, that supports testing wall-adjacent or mixed drive
temperatures. It is not, by itself, an admitted internal Nu closure.
