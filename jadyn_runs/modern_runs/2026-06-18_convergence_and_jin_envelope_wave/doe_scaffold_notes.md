# DOE scaffold notes

This wave does not submit DOE children immediately. DOE submission is gated on:

1. at least one clean new write in the parent continuation;
2. no bootstrap/runtime failure in the parent continuation log.

Planned Salt Jin child labels:

- `ethan_s1j_hotret`
- `ethan_s1j_coldleak`
- `ethan_s2j_hotret`
- `ethan_s2j_coldleak`
- `ethan_s3j_hotret`
- `ethan_s3j_coldleak`
- `ethan_s4j_hotret`
- `ethan_s4j_coldleak`

Planned hot-retaining envelope:

- lower-heater `Q` patches scaled by `+10%`
- cooling-branch fixed `Q` sink reduced after an explicit reference-state
  heat-balance recalculation
- insulation outer thickness increased by `0.40 in`

Planned cold-leaking envelope:

- lower-heater `Q` patches scaled by `-10%`
- cooling-branch fixed `Q` sink increased after an explicit reference-state
  heat-balance recalculation
- insulation outer thickness decreased by `0.40 in`

For this first DOE wave:

- mutate the lower-heater patches tied to case-level `heater_power_W`
- leave the separately powered `pipeleg_left_04_test_section` patch fixed
- keep Jin properties, laminar mode, mesh, numerics, and decomposition frozen
- do not treat `bc_params.cooler.h` as a live DOE knob unless the authoritative
  `0/T` cooler branch is first converted into a readable `h`/`Ta` contract
- when using the current fixed-`Q` cooler surrogate, compute the child
  cooling-branch `Q` from a parent late-window signed heat ledger so the
  documented reference-state residual remains near zero
