# Fluid Reset/Development API

Date: 2026-07-14

## Decision

Implemented the HYD-RESET-API slice as a narrow backward-compatible Fluid API
change. `MinorLosses` now accepts a separate `reset_development_k_by_segment`
mapping, parsed from `campaigns.yaml` minor-loss presets and charged separately
from localized fixed K inside `distributed_and_minor_losses`.

This is an API bridge, not an admitted H1 closure. Current AGENT-349 evidence
still has `0` fit-admissible component/cluster K rows, and reset/development
terms still need admitted pressure evidence before a faithful H1 rerun.

## External Files Edited

- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/config_loader.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_solver_contracts.py`

## Interface

Minor-loss presets may now include:

```yaml
reset_development_k_by_segment:
  heated_incline: 3.0
```

Keys follow the same direct-segment or parent-segment convention as
`localized_fixed_k_by_segment`; parent keys are distributed by child segment
fraction under refined geometry.

## Guardrails

- Default `MinorLosses()` behavior remains unchanged.
- Reset/development K remains separate from localized fixed K.
- No thermal fitting, native CFD mutation, scheduler action, or global
  multiplier was used.
- This does not admit H1; it only unblocks the Fluid API path for a later gated
  faithful H1 screen.

## Verification

- `python3.11 -m py_compile tamu_loop_model_v2/solver.py tamu_loop_model_v2/config_loader.py tests/test_solver_contracts.py`
- `python3.11 -m pytest tests/test_solver_contracts.py -k "minor_losses_default_has_no_localized_fixed_k or minor_losses_support_direct_and_parent_localized_fixed_k or minor_losses_support_separate_reset_development_k or minor_loss_preset_parses_localized_fixed_k"`

The broader `tests/test_solver_contracts.py tests/test_friction_closures.py`
run was started and interrupted after slow progress; no failure was observed
before interruption, but it is not counted as passed.
