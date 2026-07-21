# 2026-06-22 Salt Heat-Balance Contract

## Why this note exists

Future Salt DOE children are currently being staged from readable 3D cases that
use:

- explicit lower-heater `Q` source patches
- a separate fixed test-section `Q` source in the salt family
- fixed-`Q` cooling-branch sink patches
- temperature-dependent ambient-style losses elsewhere through
  `rcExternalTemperature`

That means the usual shortcut

`heater_power_W == cooling_power_W`

is not the real contract for the readable 3D setup.

## What is true in the current repo

- `bc_params.cooler.h` is present in `case_config.yaml`, but it is not the
  authoritative live cooler control in the current 3D Salt cases.
- The authoritative cooling branch in `0/T` is fixed `Q` on:
  - `pipeleg_upper_04_reducer`
  - `pipeleg_upper_05_cooler`
  - `pipeleg_upper_06_reducer`
- The current June 19 Salt bracket jobs changed heater power but kept those
  cooling-branch sink values unchanged.
- Therefore the current bracket family is **not** balance-by-construction under
  a new heater/cooler DOE contract.

## Evidence summary

- Readable Salt 2 metadata says `bc_params.cooler.h = 29.81733062574886`, but
  the authoritative cooler block in `0/T` is:
  - `pipeleg_upper_05_cooler: Q = -104.07353581998868 W`
  - `pipeleg_upper_04_reducer: Q = -16.13860204279952 W`
  - `pipeleg_upper_06_reducer: Q = -16.13860204279952 W`
- The boundary-modeling report shows the full cooling-branch sink is much
  larger than nominal `cooling_power_W` in the salt family.
- The June 10 Salt 2 journal note showed that the preserved late-tail wall-heat
  sum could still be nearly closed (`net total = +0.241 W`), but that is an
  observed late-time result, not a staging invariant.

## Future fixed-`Q` DOE rule

Use the bookkeeping form

`Q_in - Q_lost = 0`

with

`Q_lost = Q_removed + Q_ambient`

at the chosen parent reference state, where:

- `Q_in` is the explicit powered input that remains in the child
- `Q_removed` is the cooling-branch fixed-`Q` sink that will be solved for
- `Q_ambient` is the carried passive/ambient-style loss baseline unless that
  part of the DOE is also being changed

When the cooler branch remains fixed-`Q`, every future Salt DOE child must
carry a parent late-window heat ledger and a documented residual solve:

1. Choose a parent late-window reference time or mean window.
2. Extract signed sectionwise wall-heat totals from that parent.
3. Choose the new powered inputs:
   - lower-heater target `Q`
   - fixed test-section power if retained
4. Keep the non-cooled ambient-style and other passive terms as the reference
   bookkeeping baseline unless the DOE explicitly mutates them too.
5. Solve the child cooling-branch sink as the signed residual needed to keep
   `Q_in - Q_lost ≈ 0` at the reference state.
6. Split that solved cooling sink across the three cooling-branch patches using
   an explicit documented rule.
7. Record the arithmetic in the staging note, journal, or manifest before
   submission.

## Explicit warning

Do **not** use `ambient_proxy_w` as if it were an additional independent sink
 on top of full cooling removal. In the existing audit semantics,
`ambient_proxy_w` already contains cooling-branch excess bookkeeping.

For contract arithmetic, prefer direct signed sectionwise wall-heat totals and
write the solved `Q_removed` term explicitly into the staging note or manifest.
