# Slide Equation Block

Use this when you need a compact presentation version of the friction forms.

```text
F1: fully developed laminar friction

f_D = 64/Re
DeltaP = f_D * (L/D) * (0.5*rho*v^2)
```

```text
F3 Hagenbach: F1 plus asymptotic entry defect

DeltaP = DeltaP_F1 + K_H * (0.5*rho*v^2)
K_H = 1.33
```

```text
F3 Shah apparent: laminar developing-flow apparent friction

x_plus = L/(D*Re)

(f_app*Re)_Fanning =
    3.44/sqrt(x_plus)
    + (16.0 + 0.244)/(1 + 0.000212/x_plus^2)

(f_app*Re)_Darcy = 4*(f_app*Re)_Fanning
f_D,app = (f_app*Re)_Darcy/Re
DeltaP = f_D,app * (L/D) * (0.5*rho*v^2)
```

```text
F4 leg-class empirical fit

f/f_lam = max(a_leg + b_leg/Re, 1.0)
f_lam   = 64/Re
f_D     = (f/f_lam) * f_lam
DeltaP  = f_D * (L/D) * (0.5*rho*v^2)
```

| Leg class | a | b |
| --- | ---: | ---: |
| heater | 3.113314 | -31.8183 |
| cooler | 2.549138 | -20.1248 |
| downcomer | 4.361424 | -134.0506 |
| upcomer | 1.548087 | -19.6165 |

Presentation caveat:

```text
F3_shah_apparent is the strongest current literature-backed baseline.
F4_leg_class is implemented but provisional; the Ri-based F4 screen is diagnostic
only and is not a validated production correlation.
```
