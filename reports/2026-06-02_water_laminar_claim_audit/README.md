# Water Laminar Claim Audit

Generated: `2026-06-02T10:01:44-05:00`

## Determination

- `val_water_test_1_coarse_mesh_laminar`: `needs_convergence_audit`. No recorded convergence marker; use only for preliminary trend inspection until a convergence audit is completed.
- `val_water_test_2_coarse_mesh_laminar`: `needs_convergence_audit`. No recorded convergence marker; use only for preliminary trend inspection until a convergence audit is completed.
- `val_water_test_3_coarse_mesh_laminar`: `needs_convergence_audit`. No recorded convergence marker; use only for preliminary trend inspection until a convergence audit is completed.
- `val_water_test_4_coarse_mesh_laminar`: `needs_convergence_audit`. Shorter runtime and no recorded convergence marker; not suitable for validation claims without further audit or continuation.

## Interpretation rule used

- `acceptable_current_local_claim`: completed normally and reached the coded convergence monitor.
- `acceptable_with_termination_caveat`: reached the coded convergence monitor before scheduler termination.
- `needs_convergence_audit`: no recorded convergence marker, so validation claims should wait for audit or continuation.

