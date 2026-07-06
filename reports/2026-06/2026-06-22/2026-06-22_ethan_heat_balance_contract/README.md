# Ethan Heat-Balance Contract

Generated: `2026-06-22`

## Conclusion

The current readable Ethan 3D cases were **not** all staged under a simple
input-level rule that nominal heater power equals nominal cooler power plus a
fixed ambient-loss constant.

Instead, the readable setup mixes:

- explicit fixed-`Q` heater sources
- a separate fixed test-section source in the salt family
- fixed-`Q` cooling-branch sink patches
- temperature-dependent ambient-style losses on the rest of the loop

## What has been true so far

- Some preserved runs do show near-zero late-time signed wall-heat closure.
  Salt 2 already has a documented late-tail example with net total near zero.
- That is an observed runtime balance result, not a DOE staging invariant.
- The current June 19 Salt bracket jobs changed heater power but inherited the
  parent cooling-branch fixed sinks unchanged, so they are not
  balance-by-construction under a strict heater/cooler DOE policy.

## Practical rule for future Salt DOE children

Use the reference-state bookkeeping form

`Q_in - Q_lost = 0`

with

`Q_lost = Q_removed + Q_ambient`.

If the cooler branch remains fixed-`Q`, future DOE children must preserve a
documented parent-reference heat ledger:

- compute a parent late-window signed heat balance
- choose the new heater target
- solve the child cooling-branch fixed sink as the residual needed to keep
  `Q_in - Q_lost ≈ 0` at the chosen reference state
- record that arithmetic before submission

Do not use metadata `bc_params.cooler.h` as if it were the live cooler control,
and do not add `ambient_proxy_w` on top of full cooling removal when closing
the budget.
