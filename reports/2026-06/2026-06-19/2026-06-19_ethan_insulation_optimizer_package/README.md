# Ethan Insulation Optimizer Package

Generated: `2026-06-19T16:34:02-05:00`

## Purpose

This package uses the read-only Ethan wall-loss model to infer the effective insulation thickness that drives
`Q_unaccounted = Q_heater + Q_test_section - Q_cooler(air-side) - Q_total_loss` toward zero for each experimental
Salt and Water case. It then compares those inferred effective thicknesses against the known outer insulation
thicknesses already recorded for the 3D CFD cases in the June 17 nondimensional dashboard package.

## Method boundary

- The optimizer reuses `../cfd-modeling-tools/tamu_first_order_model/Ethan_wall_and_heat_losses/first_order_model_tamu_loop.py` as-is.
- The cooler term is still the measured air-side enthalpy balance from Ethan's model, not a predictive cooler HTC closure.
- The reported optimum is an effective thickness for the measured-state heat-loss model. It is not, by itself, a validated redesign recommendation for a new geometry or a new ambient closure model.

## Current state

- experimental cases optimized: `8`
- known salt screening CFD cases quantified: `8`
- known salt validation CFD cases compared: `1`
- known water CFD cases compared: `4`

## Family summary

- Salt effective mean optimum: `1.907` in
- Salt recommended uniform thickness: `1.90` in
- Salt known 3D mean thickness: `1.428` in
- Water effective mean optimum: `0.393` in
- Water recommended uniform thickness: `0.40` in
- Water known 3D mean thickness: `0.400` in

## Case-by-case thickness tables

The report now includes explicit case tables in `case_thickness_tables.md`.

### Solver optimum by experimental case

| Experimental case | Solver optimum [in] | Legacy solver default [in] | Within uncertainty? | Current CFD thicknesses |
| --- | --- | --- | --- | --- |
| Salt 1 | 2.4000 | 1.650 | no | Salt 1 Jin (1.400 in); Salt 1 Kirst (1.400 in) |
| Salt 2 | 1.7291 | 1.650 | yes | Salt 2 Jin (1.400 in); Salt 2 Kirst (1.400 in); Salt 2 Val (1.650 in) |
| Salt 3 | 1.6696 | 1.650 | yes | Salt 3 Jin (1.400 in); Salt 3 Kirst (1.400 in) |
| Salt 4 | 1.8277 | 1.650 | yes | Salt 4 Jin (1.400 in); Salt 4 Kirst (1.400 in) |
| Water 1 | 0.3724 | 0.500 | yes | Water 1 (0.400 in) |
| Water 2 | 0.4062 | 0.500 | yes | Water 2 (0.400 in) |
| Water 3 | 0.4062 | 0.500 | yes | Water 3 (0.400 in) |
| Water 4 | 0.3878 | 0.500 | yes | Water 4 (0.400 in) |

### Current CFD thickness by run

| CFD case | Matched experimental case | Current CFD thickness [in] | Solver optimum [in] | CFD - optimum [in] |
| --- | --- | --- | --- | --- |
| Salt 1 Jin | Salt 1 | 1.400 | 2.4000 | -1.0000 |
| Salt 1 Kirst | Salt 1 | 1.400 | 2.4000 | -1.0000 |
| Salt 2 Jin | Salt 2 | 1.400 | 1.7291 | -0.3291 |
| Salt 2 Kirst | Salt 2 | 1.400 | 1.7291 | -0.3291 |
| Salt 2 Val | Salt 2 | 1.650 | 1.7291 | -0.0791 |
| Salt 3 Jin | Salt 3 | 1.400 | 1.6696 | -0.2696 |
| Salt 3 Kirst | Salt 3 | 1.400 | 1.6696 | -0.2696 |
| Salt 4 Jin | Salt 4 | 1.400 | 1.8277 | -0.4277 |
| Salt 4 Kirst | Salt 4 | 1.400 | 1.8277 | -0.4277 |
| Water 1 | Water 1 | 0.400 | 0.3724 | 0.0276 |
| Water 2 | Water 2 | 0.400 | 0.4062 | -0.0062 |
| Water 3 | Water 3 | 0.400 | 0.4062 | -0.0062 |
| Water 4 | Water 4 | 0.400 | 0.3878 | 0.0122 |

## Interpretation boundary

Read `thickness_scientific_analysis.md` before using these numbers in a redesign or paper claim. That note explains
which conclusions are directly supported by the effective-thickness fit, which conclusions only compare against the
current 3D setup choices, and which questions still belong to the coupled 1D fluid model or to new CFD runs.
