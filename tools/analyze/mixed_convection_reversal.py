#!/usr/bin/env python3
"""Hand-estimate buoyancy parameters for mixed-convection flow reversal in a
vertical pipe (upcomer convection-cell onset), independent of the CFD groups.

PURPOSE
-------
Route B of operational_notes/06-26/30/2026-06-30_next_scope_branch_closures_and_cfd_design.md
section 4: an INDEPENDENT, literature-based desk estimate of the Reynolds number
(and Richardson number) at which the upcomer mixed-convection recirculation
("convection cell") turns on/off, to bracket the data-extrapolation estimate
(Route A) that put lower-upcomer shutoff near Re ~ 240-260.

This module is PURE python (math only). It contains NO OpenFOAM dependency and
does NOT read the solver Ri/Ra fields; it recomputes characteristic buoyancy
groups from first principles using the salt properties + leg geometry + a
defensible Delta T. It is intentionally decoupled from the (NEEDS-AUDIT) solver
group definitions so it can serve as an independent check.

LITERATURE BASIS AND DEFINITIONS (state every choice)
-----------------------------------------------------
Two classical mixed-convection criteria are relevant:

1. Richardson screen  Ri = Gr / Re^2.
   * Gr here is the Delta-T (Gr_T) Grashof number,
         Gr_T = g * beta * dT * Lc^3 / nu^2,
     with beta the volumetric thermal expansion coefficient, dT a characteristic
     temperature difference, Lc a characteristic length, nu the kinematic
     viscosity. Re = rho U Lc / mu = U Lc / nu (same Lc).
   * Then Ri = Gr_T / Re^2 = g beta dT Lc / U^2 -- a buoyancy-vs-inertia ratio
     INDEPENDENT of nu and of Lc^3 scaling (only one power of Lc survives).
   * Rule of thumb (textbook, e.g. Incropera; LitRev ch.14 "Ri screen"):
     forced-dominated for Ri << 1, free-dominated for Ri >> 1, mixed for Ri ~ 1.
     Recirculation/reversal is EXPECTED for Ri >~ O(1).

2. Laminar buoyancy-aided/-opposed near-wall velocity reversal.
   In fully developed laminar mixed convection in a vertical pipe the axial
   velocity profile distorts; for buoyancy AIDING the flow the velocity peaks
   off-axis and, past a threshold buoyancy, the CENTRELINE (opposed case) or the
   near-wall (opposed) region reverses. The classical control group is the ratio
       Gr_T / Re   (== Ri * Re)   [for constant-wall-temperature framing],
   or equivalently Ra/Re for the heat-flux framing. The widely quoted laminar
   onset of flow reversal in a vertical pipe occurs at
       Gr_T / Re  ~  O(100)   (buoyancy-opposed; reversal near the wall),
   and a few hundred for buoyancy-aided centreline reversal. We use
   |Gr_T/Re|_crit ~ 100-300 as the literature reversal band. (Order of magnitude;
   exact value depends on whether it is the near-wall or centreline reversal and
   on the thermal boundary condition.)

3. Jackson-Cotton-Axcell (1989) turbulent buoyancy parameter
       Bo* = Gr_q* / (Re^3.425 * Pr^0.8),   Gr_q* = g beta q'' D^4 / (k nu^2),
   with impairment/onset of buoyancy influence at Bo* ~ 6e-7 (turbulent).
   THIS IS A TURBULENT correlation. Our upcomer is LAMINAR (Re ~ 50-150), so the
   Re^3.425 turbulent scaling does NOT apply quantitatively; we cite it for the
   PHYSICS (a Gr/Re^n buoyancy group with a reversal/impairment threshold) but
   use the laminar Ri (n=2) screen for the actual number. This mismatch is
   disclosed in the companion note.

CHOICE OF Lc AND dT (defensible, stated)
----------------------------------------
* Lc = D_h ~ 21.8 mm (measured hydraulic diameter). The TRANSVERSE cell is driven
  by the wall-core temperature difference across the pipe, so the pipe diameter is
  the physically correct length for the transverse buoyancy that rolls the cell.
  (Using the leg length L ~ 0.95 m would describe an axial/loop-scale buoyancy,
  not the transverse cell; we report it as a sensitivity only.)
* dT = wall-core (radial) temperature difference. The cell is driven by cooled
  near-wall fluid sinking relative to the hot core, so the RADIAL dT is the
  driver, not the axial bulk dT. We do not have a measured wall-core dT here, so
  we PARAMETERISE it and report Re_crit(dT). A plausible upcomer wall-core dT is
  a few K (modest wall heat loss through insulation) up to ~20 K (low insulation).

All functions are NaN-guarded and side-effect free.
"""
from __future__ import annotations

import math

NAN = float("nan")

# Salt thermal expansion coefficient from the linear EoS rho = 2293.6 - 0.7497*T
# (tools/analyze/salt_properties.py): beta = -(1/rho) drho/dT = 0.7497 / rho.
_RHO_DT = 0.7497  # |drho/dT| [kg/(m^3 K)]


def beta_salt(rho_kg_m3: float) -> float:
    """Volumetric thermal expansion coefficient beta(T) [1/K].

    beta = -(1/rho)(drho/dT) = 0.7497 / rho, using the linear salt EoS.
    NaN-guarded.
    """
    if not math.isfinite(rho_kg_m3) or rho_kg_m3 <= 0.0:
        return NAN
    return _RHO_DT / rho_kg_m3


def grashof_dt(beta: float, dT: float, Lc: float, nu: float, g: float = 9.81) -> float:
    """Delta-T Grashof number  Gr_T = g*beta*dT*Lc^3 / nu^2.  NaN-guarded."""
    for v in (beta, dT, Lc, nu, g):
        if not math.isfinite(v):
            return NAN
    if nu <= 0.0:
        return NAN
    return g * beta * dT * Lc ** 3 / nu ** 2


def richardson(Gr: float, Re: float) -> float:
    """Ri = Gr / Re^2.  NaN-guarded (Re != 0)."""
    if not math.isfinite(Gr) or not math.isfinite(Re) or Re == 0.0:
        return NAN
    return Gr / Re ** 2


def re_crit_from_ri(Gr: float, Ri_crit: float) -> float:
    """Re at which Ri = Gr/Re^2 drops to a target Ri_crit:  Re_crit = sqrt(Gr/Ri_crit).

    This is the forced Reynolds number at which the buoyancy screen falls to the
    reversal threshold for a FIXED Grashof (fixed dT, Lc, properties). NaN-guarded.
    """
    if not math.isfinite(Gr) or not math.isfinite(Ri_crit) or Ri_crit <= 0.0 or Gr < 0.0:
        return NAN
    return math.sqrt(Gr / Ri_crit)


def re_crit_from_gr_over_re(Gr: float, ratio_crit: float) -> float:
    """Re at which Gr/Re reaches the laminar reversal threshold:  Re_crit = Gr/ratio_crit.

    Uses the laminar near-wall reversal group Gr_T/Re ~ O(100-300). NaN-guarded.
    """
    if not math.isfinite(Gr) or not math.isfinite(ratio_crit) or ratio_crit <= 0.0:
        return NAN
    return Gr / ratio_crit


def reynolds(rho: float, U: float, Lc: float, mu: float) -> float:
    """Re = rho*U*Lc/mu.  NaN-guarded."""
    for v in (rho, U, Lc, mu):
        if not math.isfinite(v):
            return NAN
    if mu <= 0.0:
        return NAN
    return rho * U * Lc / mu
