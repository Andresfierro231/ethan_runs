# Friction Correlation Math Reference

Date: 2026-07-09  
Task: AGENT-229  
Role: Writer  
Purpose: thesis-facing record of the implemented and candidate friction-correlation equations used in the TAMU 1D loop closure studies.

## Bottom Line

Use this package as the durable in-repo reference for the equations behind `F1`,
the two `F3` forms, the implemented `F4_leg_class` empirical fit, and the
diagnostic Ri-based F4 candidate.

For thesis or presentation wording:

- `F1` is the fully developed laminar Darcy friction baseline.
- `F3_hagenbach` is `F1` plus a one-time asymptotic entrance pressure defect.
- `F3_shah_apparent` is the current best literature-backed baseline because it
  accounts for both developing-flow wall-shear elevation and the velocity-profile
  momentum defect through one apparent friction factor.
- `F4_leg_class` is the implemented data-fitted leg-class multiplier, but it is
  provisional and training-set diagnostic only.
- The Ri-based F4 candidate is a failed/diagnostic screen, not a validated or
  implemented production correlation.

## Notation

| Symbol | Meaning |
| --- | --- |
| `Re` | Reynolds number using local bulk properties |
| `rho` | local density |
| `v` | bulk velocity |
| `L` | segment or section length |
| `D` | hydraulic diameter |
| `q_dyn` | dynamic pressure, `0.5 * rho * v^2` |
| `f_D` | Darcy friction factor |
| `f_lam` | fully developed laminar Darcy friction factor, `64/Re` |
| `x_plus` | hydrodynamic entry-length coordinate, `L/(D*Re)` |

The distributed pressure-drop convention used by the code is:

```text
DeltaP = f_D * (L/D) * q_dyn
q_dyn  = 0.5 * rho * v^2
```

Minor/local losses and hydrostatic buoyancy are handled outside these friction
closure functions. Do not embed buoyancy in the friction term when quoting these
forms.

## F1: Fully Developed Laminar Friction

Source implementation: `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`, `dp_F1`.

```text
f_D = 64 / Re

DeltaP_F1 = (64/Re) * (L/D) * (0.5*rho*v^2)
```

Interpretation:

- Analytic Hagen-Poiseuille laminar pipe result.
- No entrance/developing-flow correction.
- No minor losses.
- No buoyancy term.
- This remains the solver default baseline in the July 7 closure comparison.

## F3 Hagenbach: F1 Plus Entry Momentum Defect

Source implementation: `friction_closures.py`, `dp_F3_hagenbach`.

For the first subsegment of a physical pipe section:

```text
DeltaP_F3h = DeltaP_F1 + DeltaP_entry

DeltaP_entry = K_H * q_dyn
K_H          = 1.33
q_dyn        = 0.5*rho*v^2
```

For non-entry subsegments:

```text
DeltaP_F3h = DeltaP_F1
```

The equivalent apparent Darcy friction factor reported by the implementation is:

```text
f_D,app = DeltaP_F3h / ((L/D) * q_dyn)
```

Interpretation:

- `K_H = 1.33` is the asymptotic circular-tube Hagenbach/Boussinesq entry-defect
  constant for uniform inlet flow.
- The term is applied only when `is_segment_entry=True`.
- It captures the one-time momentum defect but not the elevated distributed wall
  shear during hydrodynamic development.
- At TAMU loop `x_plus` values below about 1, this can underpredict total
  developing-flow pressure drop relative to the Shah apparent-friction form.

## F3 Shah Apparent: Developing-Flow Apparent Friction

Source implementation: `friction_closures.py`, `dp_F3_shah_apparent`.

For the first subsegment of a physical pipe section:

```text
x_plus = L / (D * Re)

(f_app * Re)_Fanning =
    3.44 / sqrt(x_plus)
    + (16.0 + 0.244) / (1 + 0.000212 / x_plus^2)

(f_app * Re)_Darcy = 4 * (f_app * Re)_Fanning

f_D,app = (f_app * Re)_Darcy / Re

DeltaP_F3s = f_D,app * (L/D) * (0.5*rho*v^2)
```

For non-entry subsegments:

```text
DeltaP_F3s = DeltaP_F1
```

Constants used in the implementation:

| Constant | Value | Meaning |
| --- | ---: | --- |
| `C1` | `3.44` | leading developing-flow coefficient |
| `f_inf_Re` | `16.0` | fully developed Fanning `f*Re` for circular laminar flow |
| `C_hag` | `0.244` | momentum-defect/Hagenbach contribution in Shah form |
| `D_fit` | `0.000212` | curve-fit denominator constant |

Citation recorded in the source code and July 7 literature-form package:
Shah, R.K. (1978), "A correlation for laminar hydrodynamic entry length
solutions for circular and noncircular ducts," ASME Journal of Fluids
Engineering, Vol. 100, pp. 177-179, Eq. 15, circular-tube row.

Interpretation:

- This is a literature correlation, not a fit to the TAMU CFD data.
- It captures both developing-flow distributed wall-shear elevation and the
  inlet velocity-profile momentum defect.
- It is the strongest current friction baseline in the July 8 rigor review.
- It does not include buoyancy or mixed-convection profile distortion.

## F4 Leg-Class Fit: Implemented Empirical Multiplier

Source implementation: `friction_closures.py`, `F4_LEG_CLASS_FITS` and
`dp_F4_leg_class`.

The fitted model is:

```text
f_over_flam = a_leg + b_leg / Re
f_over_flam = max(f_over_flam, 1.0)

f_lam = 64 / Re
f_D   = f_over_flam * f_lam

DeltaP_F4 = f_D * (L/D) * (0.5*rho*v^2)
```

Fitted coefficients currently implemented:

| Leg class | `a_leg` | `b_leg` | Fit note |
| --- | ---: | ---: | --- |
| `heater` | `3.113314` | `-31.8183` | lower heated inclined leg, `R^2 = 0.88`, `n = 3` |
| `cooler` | `2.549138` | `-20.1248` | upper cooled inclined leg, `R^2 = 0.98`, `n = 3` |
| `downcomer` | `4.361424` | `-134.0506` | right vertical leg, `R^2 = 0.99`, `n = 3` |
| `upcomer` | `1.548087` | `-19.6165` | merged upcomer class, `R^2 = 0.02`, poor fit |

Calibration target and admission:

- Target: de-buoyed CFD friction-factor excess from the Salt 2/3/4 Jin mainline
  momentum-budget rows.
- Form: ordinary least-squares fit of `f_corrected/f_lam = a + b/Re` by leg
  class.
- Salt 1 was excluded due to weak convergence.
- Corrected-Q perturbation runs were excluded pending requalification.
- Validity band recorded by the implementation is approximately `Re = 60-135`.

Interpretation:

- This is the actual implemented fitted `F4` closure.
- It is not an Ri-corrected closure.
- It does not add an entry correction.
- It should not be called thesis-final without validation because the training
  set is small and the upcomer class fit is physically poor.
- In the July 7 mdot comparison it over-stiffened the loop, producing about
  `-23%` to `-25%` mass-flow error for Salt 2/3/4 Jin, even though it matched
  some per-leg training friction factors.

## Ri-Based F4 Candidate: Diagnostic Screen Only

Source report: `work_products/2026-07/2026-07-07/2026-07-07_f4_ri_calibration_and_solver_gate/f4_candidate_fit_report.md`.

Candidate form screened by the July 7 gate package:

```text
M_F4 = clamp(1 + C_group * signed_sqrt(Ri_streamwise), 0.25, 5.0)
```

where `M_F4` multiplies a residual friction ratio against the F3 baseline in
the diagnostic calibration screen.

Interpretation:

- This is not the implemented production solver closure.
- The documented candidate fits had negative or unusable `R^2` values.
- The July 8 rigor review says to cite this as a failed or insufficient
  correction screen, not as support for a validated Ri closure.
- Predictive heater/cooler/Ri model development remains future work.

## Loop-Level Comparison Evidence

The July 7 Salt 2/3/4 Jin comparison at matched insulation reported:

| Form | Salt 2 mdot error | Salt 3 mdot error | Salt 4 mdot error |
| --- | ---: | ---: | ---: |
| `F1` | `+9.70%` | `+16.21%` | `+17.97%` |
| `F3_hagenbach` | `+3.50%` | `+6.69%` | `+5.69%` |
| `F3_shah_apparent` | `-0.93%` | `+3.33%` | `+3.75%` |
| `F4_leg_class` | `-23.19%` | `-23.57%` | `-24.66%` |

This comparison is a loop-level solver result, not a primary-source literature
validation. It supports the current working conclusion that `F3_shah_apparent`
is the best available baseline for current presentations and thesis drafting,
while `F4_leg_class` remains diagnostic/provisional.

## Thesis Wording Recommendation

Suggested defensible phrasing:

```text
The baseline one-dimensional pressure-loss model used the fully developed
laminar Darcy friction factor, f_D = 64/Re. Two developing-flow corrections
were evaluated: an asymptotic Hagenbach entry defect, DeltaP_entry = 1.33 q_dyn,
and the Shah apparent-friction correlation for laminar hydrodynamic entry flow.
The Shah form was retained as the strongest current literature-backed baseline
because it represents both the entry momentum defect and the enhanced distributed
wall shear during profile development. A separate leg-class empirical multiplier,
f/f_lam = a + b/Re, was also implemented from de-buoyed CFD segment-friction
targets, but that fitted F4 form is treated as provisional because it was trained
on only the Salt 2-4 Jin points and performed poorly in loop-level mdot replay.
```

Avoid saying:

```text
F4 is the final mixed-convection friction law.
```

More accurate:

```text
F4_leg_class is an implemented empirical screening closure; a validated
Ri-corrected mixed-convection closure remains future work.
```

## Source Map

Primary implementation:

- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
  - `dp_F1`
  - `dp_F3_hagenbach`
  - `dp_F3_shah_apparent`
  - `F4_LEG_CLASS_FITS`
  - `dp_F4_leg_class`

In-repo evidence and interpretation:

- `work_products/2026-07/2026-07-07/2026-07-07_f_lit_forms/README.md`
- `work_products/2026-07/2026-07-07/2026-07-07_friction_forms_comparison/README.md`
- `work_products/2026-07/2026-07-07/2026-07-07_f4_buoyancy_friction/README.md`
- `work_products/2026-07/2026-07-07/2026-07-07_f4_ri_calibration_and_solver_gate/f4_candidate_fit_report.md`
- `operational_notes/07-26/08/2026-07-08_claude_literature_closure_fit_rigor_review.md`
- `journals/2026-07/2026-07-09_ethan_runs.md`

## Open Thesis Follow-Ups

1. Verify the Shah constants and validity wording directly against the primary
   article before final thesis submission.
2. Keep `F3_shah_apparent` as the current defensible baseline unless later
   thermal/interface sampling or mesh-refinement gates materially change the
   evidence.
3. Do not promote `F4_leg_class` beyond provisional status until more operating
   points, wall-bulk temperature information, and independent validation are
   available.
4. Keep any future Ri-corrected friction law separate from this July 7 diagnostic
   Ri screen unless it is newly fit, validated, and documented.
