# Presentation Readiness and ROM Agenda

Date: `2026-07-01`  
Task: `AGENT-169`  
Status: generated from existing reports; no OpenFOAM execution

## Purpose

This package collects what can be shown in tomorrow's meeting and separates it
from what still needs more work before it becomes paper-ready. It also creates
reusable comparison tables for future 1D model forms, coefficients, figures,
and experimental-validation planning.

Work products: `work_products/2026-07-01_presentation_readiness_and_rom_agenda`

## Meeting-Ready Headline

- The post-processing pipeline now has explicit geometry, pressure/friction,
  and thermal-audit tables instead of mixing `p_rgh`, apparent resistance, and
  closure-grade quantities.
- OF13 T reconstruction unlocked thermal closures for Salt 2/3/4 Jin: lower-leg
  HTC rises from 252 to 288 W/m2-K; upcomer Nu rises from 3.11 to 4.99.
- Current 1D validation is useful but not final: the defended baseline gives
  about 11.27 percent mean energy error and
  26.69 percent mass-flow relative error against
  the CFD latest-window reference.
- Local hydraulic replay is a strong diagnostic but not a predictive result:
  probe replay is near 0.000255 kg/s mean mdot error,
  while major-only and endpoint forms fail by orders of magnitude.

## Generated Tables

- `paper_readiness_matrix.csv`: what is paper-ready, meeting-ready, blocked, or
  future validation.
- `figure_inventory.csv`: figures that can be used in the meeting and their
  readiness caveats.
- `model_form_inventory.csv`: current and future 1D model forms with assumptions,
  metrics, and credibility boundaries.
- `coefficient_inventory.csv`: thermal coefficients and diagnostic hydraulic
  replay metrics that can be compared against future fits.
- `future_model_forms.csv`: candidate closure/model forms to fit next.
- `run_and_package_inventory.csv`: provenance and status for current packages
  and run families.
- `experimental_validation_next_steps.md`: what is needed to validate the 1D
  model against physical experiment data.

## Credibility Boundary

The strongest paper-facing material today is methods/provenance and diagnostic
mechanism evidence. The full predictive 1D model is still in development because
mesh independence is blocked, perturbation runs are false-steady, and pressure
gradients still need variable-density buoyancy decomposition before being fit as
mechanical losses.
