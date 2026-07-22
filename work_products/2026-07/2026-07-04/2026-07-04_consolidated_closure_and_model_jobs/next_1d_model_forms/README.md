# Next 1D Model-Form Job Output

Generated: `2026-07-04T09:50:23-05:00`

This is a lightweight local/Slurm-safe screen built from existing consolidated CFD closure tables.
It does not run OpenFOAM and does not edit external Fluid repositories.

## Current Result

- Best prior per-leg/global trial row here: `global_mean_mult` with mean |mdot error| `3.662%`.
- f(Re) span/method groups screened: `12`.
- f(Re) rows remain screen-only because the canceled perturbation runs are false-steady and excluded.

## Files

- `next_1d_model_form_scores.csv`
- `per_leg_re_power_law_screen.csv`
- `next_model_form_backlog.csv`
- `summary.json`
