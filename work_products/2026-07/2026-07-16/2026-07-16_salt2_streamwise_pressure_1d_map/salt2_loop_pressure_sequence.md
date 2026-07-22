# Salt2 Streamwise Pressure / 1D Segment Map

This package filters the July 15 station pressure ladder to `salt2_mainline` and orders it by physical loop flow.
The station values are diagnostic harvested averages, not fit-admitted `f_D` or component `K` evidence.

## Branch Averages In Loop Order

| CFD span | Physical location | 1D segment(s) | flow stations | mean p [Pa] | mean p_rgh [Pa] | end-start p [Pa] | max reverse proxy |
|---|---|---|---|---:|---:|---:|---:|
| lower_leg | heater / bottom heated incline | `heated_incline` | lower_leg__s04 -> lower_leg__s00 | -6344.227 | 4.621 | -7085.588 | 0.5406 |
| left_lower_leg | lower upcomer below test section | `left_lower_vertical` | left_lower_leg__s00 -> left_lower_leg__s04 | -3284.413 | -3.637 | -4703.276 | 0.6406 |
| test_section_span | test section / middle upcomer | `test_section` | test_section_span__s00 -> test_section_span__s04 | -8629.364 | -2.372 | 3803.700 | 0.3359 |
| left_upper_leg | upper upcomer above test section | `left_upper_vertical` | left_upper_leg__s00 -> left_upper_leg__s04 | -14453.701 | -3.735 | -5501.058 | 0.8446 |
| upper_leg | cooled leg / top cooled incline | `top_horizontal_inlet;cooled_incline_pre_hx;cooled_incline_hx_active;cooled_incline_post_hx;top_horizontal_exit` | upper_leg__s00 -> upper_leg__s04 | -7339.549 | -0.979 | 6955.108 | 0.5783 |
| right_leg | right downcomer / cold vertical return | `right_vertical` | right_leg__s00 -> right_leg__s04 | -4409.427 | -2.632 | -14054.234 | 0.6757 |

## Labeling Guardrails

- `lower_leg` is the physical heater and maps to 1D `heated_incline`; traverse `lower_leg__s04 -> lower_leg__s00`.
- `right_leg` is the physical downcomer and maps to 1D `right_vertical`; traverse `right_leg__s00 -> right_leg__s04`.
- `upper_leg` is the cooled top leg and maps to the Fluid top/HX composite: `top_horizontal_inlet`, `cooled_incline_pre_hx`, `cooled_incline_hx_active`, `cooled_incline_post_hx`, `top_horizontal_exit`.
- `left_lower_leg`, `test_section_span`, and `left_upper_leg` map to the upcomer/test-section path.

## Station-Level Sequence

| loop index | station | CFD span | physical location | 1D parent | mean p [Pa] | mean p_rgh [Pa] |
|---:|---|---|---|---|---:|---:|
| 0 | lower_leg__s04 | lower_leg | heater / bottom heated incline | `heated_incline` | -450.959 | -0.681 |
| 1 | lower_leg__s03 | lower_leg | heater / bottom heated incline | `heated_incline` | -9777.697 | 6.265 |
| 2 | lower_leg__s02 | lower_leg | heater / bottom heated incline | `heated_incline` | -6858.457 | 8.446 |
| 3 | lower_leg__s01 | lower_leg | heater / bottom heated incline | `heated_incline` | -7097.472 | 8.703 |
| 4 | lower_leg__s00 | lower_leg | heater / bottom heated incline | `heated_incline` | -7536.547 | 0.371 |
| 5 | left_lower_leg__s00 | left_lower_leg | lower upcomer below test section | `left_lower_vertical` | -932.651 | -3.442 |
| 6 | left_lower_leg__s01 | left_lower_leg | lower upcomer below test section | `left_lower_vertical` | -2114.128 | -3.688 |
| 7 | left_lower_leg__s02 | left_lower_leg | lower upcomer below test section | `left_lower_vertical` | -3284.520 | -3.694 |
| 8 | left_lower_leg__s03 | left_lower_leg | lower upcomer below test section | `left_lower_vertical` | -4454.840 | -3.663 |
| 9 | left_lower_leg__s04 | left_lower_leg | lower upcomer below test section | `left_lower_vertical` | -5635.927 | -3.698 |
| 10 | test_section_span__s00 | test_section_span | test section / middle upcomer | `test_section` | -10532.390 | -2.259 |
| 11 | test_section_span__s01 | test_section_span | test section / middle upcomer | `test_section` | -9577.573 | -2.298 |
| 12 | test_section_span__s02 | test_section_span | test section / middle upcomer | `test_section` | -8624.570 | -2.325 |
| 13 | test_section_span__s03 | test_section_span | test section / middle upcomer | `test_section` | -7683.596 | -2.400 |
| 14 | test_section_span__s04 | test_section_span | test section / middle upcomer | `test_section` | -6728.690 | -2.577 |
| 15 | left_upper_leg__s00 | left_upper_leg | upper upcomer above test section | `left_upper_vertical` | -11699.171 | -3.387 |
| 16 | left_upper_leg__s01 | left_upper_leg | upper upcomer above test section | `left_upper_vertical` | -13084.529 | -5.682 |
| 17 | left_upper_leg__s02 | left_upper_leg | upper upcomer above test section | `left_upper_vertical` | -14457.075 | 5.767 |
| 18 | left_upper_leg__s03 | left_upper_leg | upper upcomer above test section | `left_upper_vertical` | -15827.501 | 4.377 |
| 19 | left_upper_leg__s04 | left_upper_leg | upper upcomer above test section | `left_upper_vertical` | -17200.229 | -19.748 |
| 20 | upper_leg__s00 | upper_leg | cooled leg / top cooled incline | `cooled_incline_composite` | -13145.692 | -14.882 |
| 21 | upper_leg__s01 | upper_leg | cooled leg / top cooled incline | `cooled_incline_composite` | -3833.058 | -9.091 |
| 22 | upper_leg__s02 | upper_leg | cooled leg / top cooled incline | `cooled_incline_composite` | -6697.709 | 3.066 |
| 23 | upper_leg__s03 | upper_leg | cooled leg / top cooled incline | `cooled_incline_composite` | -6830.700 | 7.706 |
| 24 | upper_leg__s04 | upper_leg | cooled leg / top cooled incline | `cooled_incline_composite` | -6190.584 | 8.306 |
| 25 | right_leg__s00 | right_leg | right downcomer / cold vertical return | `right_vertical` | 2614.867 | -0.797 |
| 26 | right_leg__s01 | right_leg | right downcomer / cold vertical return | `right_vertical` | -889.281 | -3.424 |
| 27 | right_leg__s02 | right_leg | right downcomer / cold vertical return | `right_vertical` | -4411.496 | -3.664 |
| 28 | right_leg__s03 | right_leg | right downcomer / cold vertical return | `right_vertical` | -7921.857 | -2.374 |
| 29 | right_leg__s04 | right_leg | right downcomer / cold vertical return | `right_vertical` | -11439.367 | -2.898 |
