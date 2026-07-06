# Ethan Salt Straight Hydraulic Sensitivity Refresh

Generated: `2026-06-23`

## Scope

- This package rebuilds the Salt straight-section sensitivity subset from the
  continuation-frozen late windows rather than the older case-mean package
  roots.
- Straight sections are not treated here as automatically fully developed.
  They remain bounded CFD-supported closures on a narrow admitted Salt subset.

## Preserved late windows

- Salt 2 Jin: `5009-5029 s`
- Salt 3 Jin: `4931-4951 s`
- Salt 4 Jin: `7797-7817 s`

## Main result

- The preserved `20 s` late-window rebuild changes the defended straight set.
- Case-mean defended rows: `5`
- Late-window defended rows: `4`
- Dropped relative to the case-mean defended set:
  `Salt 3 Jin / lower_leg`
- Drop reason:
  `support_fraction_below_floor`

## Retained late-window defended rows

- `Salt 2 Jin / test_section_span`
- `Salt 3 Jin / test_section_span`
- `Salt 4 Jin / lower_leg`
- `Salt 4 Jin / test_section_span`

## Stale note closed

- Before this package-level bookkeeping refresh, this report root lacked a
  `README.md` and `summary.json`, and downstream frozen-state reporting was
  still pointing at the older June 19 straight package.
