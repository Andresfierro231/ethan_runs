# AGENT-121 Raw Journal — Latest-Window Frozen-State Refresh

- date: `2026-06-23`
- role: `Coordinator / Implementer / Writer`
- task ID: `AGENT-121`
- purpose:
  - rebuild the nominal Salt Jin case-analysis roots from the June 23 CFD
    checkpoint windows
  - promote those refreshed roots into a clearly dated frozen-state package
  - remove ambiguity with the older June 15 live-analysis package roots
- questions accumulating:
  - Should the presentation-facing narrative continue to cite the old June 23
    bakeoff package as a bounded surrogate until the latest-window retarget
    lands, or should that package be explicitly superseded in the report text?
  - Is the intended physical interpretation that all representative Salt Jin
    cases should be treated as globally `1.4 in` insulation, or only that the
    current best surrogate does not yet match the likely physical setup?
- progress notes:
  - The exact-time freeze path could not safely use
    `freeze_case_windows.csv` alone because `salt1_jin` rounds
    `3617.6625 -> 3617.66` and `3756.33125 -> 3756.33`. The orchestration
    builder now uses `representative_timesteps.csv` for exact processor labels
    and reserves `freeze_case_windows.csv` for window metadata only.
  - The live refresh is in the expensive retained-time OpenFOAM reconstruction
    phase. At the time of this note it had advanced through the `salt1_jin`
    `0`, `3229`, `3398.45`, and `3470` field reconstructions inside the
    first nominal case refresh.
