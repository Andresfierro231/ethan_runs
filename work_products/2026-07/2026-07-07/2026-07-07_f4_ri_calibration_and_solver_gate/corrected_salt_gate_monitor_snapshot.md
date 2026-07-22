# Corrected Salt Gate Monitor Snapshot

Gate job checked: `3279646`.

Raw observations:

- `3279646` is `saltq_gate_0707` and is pending on corrected Salt solver jobs.
- `squeue` reported dependency `afterany:3275448(unfulfilled),afterany:3275449(unfulfilled),afterany:3275560(unfulfilled)`.
- Existing live-monitor rows carry latest solver times, fatal/error counts, scrutiny flags, and case-level recommendations.

Interpretation:

- Overall recommendation: hold the corrected Salt operating-point gate until dependencies finish; investigate Salt 3 high-Q canceled rows; keep Salt 1 rows out of closure fitting until the missing nominal-mdot-reference issue is resolved.
- No corrected Salt Q row is closure-fit admissible in this AGENT-191 package.

| row_type | case_key | job_id | partition | job_state | dependency | latest_solver_time_s | fatal_error_count | needs_special_gate_scrutiny | recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gate_job | corrected_salt_operating_point_gate | 3279646 | NuclearEnergy | PENDING | afterany:3275448(unfulfilled),afterany:3275449(unfulfilled),afterany:3275560(unfulfilled) |  |  |  | hold_pending_dependencies |
| solver_case | salt1_jin_lo10q_corrected | 3275448 | NuclearEnergy | RUNNING |  | 5440.123376623 | 0 | True | hold_for_coordinator_review |
| solver_case | salt1_jin_hi10q_corrected | 3275448 | NuclearEnergy | RUNNING |  | 4010.590361446 | 0 | True | hold_for_coordinator_review |
| solver_case | salt2_jin_lo10q_corrected | 3275448 | NuclearEnergy | RUNNING |  | 9430.902439024 | 0 | False | hold_running_wait_for_formal_gate |
| solver_case | salt2_jin_lo5q_corrected | 3275448 | NuclearEnergy | RUNNING |  | 9432.94047619 | 0 | False | hold_running_wait_for_formal_gate |
| solver_case | salt2_jin_hi5q_corrected | 3275449 | NuclearEnergy | RUNNING |  | 9110.3125 | 0 | False | hold_running_wait_for_formal_gate |
| solver_case | salt2_jin_hi10q_corrected | 3275449 | NuclearEnergy | RUNNING |  | 9039.811111111 | 0 | False | hold_running_wait_for_formal_gate |
| solver_case | salt3_jin_lo10q_corrected | 3275449 | NuclearEnergy | RUNNING |  | 8777.988636364 | 0 | False | hold_running_wait_for_formal_gate |
| solver_case | salt3_jin_lo5q_corrected | 3275449 | NuclearEnergy | RUNNING |  | 8757.243093923 | 0 | False | hold_running_wait_for_formal_gate |
| solver_case | salt3_jin_hi5q_corrected | 3275450 | NuclearEnergy | CANCELLED by 890970 |  | 7639.476190476 | 3 | True | investigate |
| solver_case | salt3_jin_hi10q_corrected | 3275450 | NuclearEnergy | CANCELLED by 890970 |  | 7637.875696673 | 4 | True | investigate |
| solver_case | salt4_jin_lo10q_corrected | 3275560 | NuclearEnergy | RUNNING |  | 11044.886010363 | 0 | False | hold_running_wait_for_formal_gate |
| solver_case | salt4_jin_lo5q_corrected | 3275560 | NuclearEnergy | RUNNING |  | 11079.934343434 | 0 | False | hold_running_wait_for_formal_gate |
| solver_case | salt4_jin_hi5q_corrected | 3275560 | NuclearEnergy | RUNNING |  | 10879.091346154 | 0 | False | hold_running_wait_for_formal_gate |
| solver_case | salt4_jin_hi10q_corrected | 3275560 | NuclearEnergy | RUNNING |  | 10967.613207547 | 0 | False | hold_running_wait_for_formal_gate |
