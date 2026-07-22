# F4 Candidate Fit Report

Fit target: residual `f_corrected/f_F3h` from mainline Salt 2/3/4 Jin rows only.

Candidate form: `M_F4 = clamp(1 + C_group * signed_sqrt(Ri_streamwise), 0.25, 5.0)`.

This is a bounded screen, not a validated correlation. Each physical group has only three points.

## Fit Summary

| fit_group | status | n_points | C_group | rmse | r2 |
| --- | --- | --- | --- | --- | --- |
| cooler | candidate_screen_only | 3 | 1.161 | 0.129893 | -1123.99 |
| downcomer | candidate_screen_only | 3 | 1.464 | 0.58856 | -2.21532 |
| heater | candidate_screen_only | 3 | 1.992 | 0.178037 | -60.2232 |
| test_section | candidate_screen_only | 3 | -0.072 | 0.203486 | -0.100967 |
| upcomer_lower | candidate_screen_only | 3 | 0.219 | 0.139591 | -0.904704 |
| upcomer_upper | candidate_screen_only | 3 | -0.117 | 0.124785 | -0.361308 |

Acceptance interpretation: hold for coordinator review before any publication or ROM closure fitting use.
