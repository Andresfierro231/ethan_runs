#!/usr/bin/env python3
"""Pure salt-property functions for the TAMU molten-salt loop (READ-ONLY replicas).

WHY THIS EXISTS
---------------
`tools/analyze/derive_segment_friction.py` derives an apparent Darcy friction
factor per segment but leaves Re / f_lam / excess-factor as NaN because the
dynamic viscosity mu(T) is not present in the section-mean JSON. This module
exposes side-effect-free property functions so a Reynolds number can be computed
from the salt property model WITHOUT editing the existing property source files.

PROVENANCE OF THE COEFFICIENTS (cited, not fabricated)
------------------------------------------------------
All coefficients below are REPLICATED from the case_config.yaml `fluid_properties`
blocks that drive the OpenFOAM runs, and are evaluated with the SAME functional
forms used by the production code in
`tools/analyze/ethan_salt_hardening_common.py` (functions `exp_inv_t_eval`,
`polynomial_eval`, `evaluate_mu`, etc., lines ~125-158). We do not edit that file;
we replicate the math with citations so the friction tool can stay decoupled.

  * Jin viscosity (mu_spec.type = expInvT), shared by Salt 2/3/4 Jin cases.
    Source files (all identical):
      tmp/2026-06-23_salt_last20_checkpoint/salt{2,3,4}_cont/case_config.yaml
      tmp_extract/ethan_section_transport/viscosity_screening_salt_test_3_jin_coarse_mesh/case_config.yaml
    mu_spec:
      type: expInvT
      coeffs: [0.001149, -810.896, 780600]
    The production `exp_inv_t_eval` (ethan_salt_hardening_common.py:131-138)
    evaluates type=expInvT as:
        mu(T) = a * exp( sum_{i>=1} coeffs[i] / T**i )
              = coeffs[0] * exp( coeffs[1]/T + coeffs[2]/T**2 )
    so for Jin:  mu(T) = 0.001149 * exp(-810.896/T + 780600/T**2)   [Pa*s].

  * Kirst viscosity (mu_spec.type = expInvT), single-term exponent.
    Source file:
      tmp_extract/ethan_section_transport/viscosity_screening_salt_test_1_kirst_coarse_mesh/case_config.yaml
    mu_spec:
      type: expInvT
      coeffs: [6.757e-05, 2247.11]
    Same exp_inv_t_eval form:  mu(T) = 6.757e-05 * exp(2247.11/T)   [Pa*s].

  * Density rho(T) (rho_coeffs, polynomial). Source: same case_config.yaml files.
    rho_coeffs: [2293.6, -0.7497, 0]  ->  rho(T) = 2293.6 - 0.7497*T   [kg/m^3].
    Inverting:  T = (2293.6 - rho) / 0.7497   (used by temperature_from_rho).

  * Specific heat cp(T) (Cp_coeffs, polynomial). Source: same files.
    Cp_coeffs: [1423.47, 0, 0, ...]  ->  cp(T) = 1423.47   [J/(kg*K)] (constant).

  * Thermal conductivity k(T) (kappa_spec, polynomial). Source: same files.
    kappa_spec.coeffs: [0.78, -0.00125, 1.6e-06, 0, ...]
        k(T) = 0.78 - 0.00125*T + 1.6e-06*T**2   [W/(m*K)].

UNCERTAINTY DISCLOSURE
----------------------
The functional forms and coefficients are transcribed faithfully from the repo's
case_config.yaml and the production evaluator. They have NOT been independently
validated against the primary Jin / Kirst literature here, and the temperature
inferred from the section-mean rho (via the linear EoS) inherits all of the
section-mean coarse-mesh / hydrostatic-removal caveats documented in
derive_segment_friction.py. Treat the resulting Re/excess numbers as
indicative, not closure-grade.

All functions are NaN-guarded: a non-finite or out-of-domain input yields NaN
(never a raised exception, never a fabricated number).
"""
from __future__ import annotations

import math

NAN = float("nan")

# ---- Replicated coefficients (see module docstring for provenance) ---------- #
# Jin: mu(T) = a * exp(b/T + c/T^2)
_JIN_MU_COEFFS = (0.001149, -810.896, 780600.0)
# Kirst: mu(T) = a * exp(b/T)
_KIRST_MU_COEFFS = (6.757e-05, 2247.11)
# rho(T) = 2293.6 - 0.7497*T
_RHO_A = 2293.6
_RHO_B = -0.7497
# cp(T) = 1423.47 (constant)
_CP_COEFFS = (1423.47,)
# k(T) = 0.78 - 0.00125*T + 1.6e-06*T^2
_K_COEFFS = (0.78, -0.00125, 1.6e-06)


def _exp_inv_t(coeffs: tuple[float, ...], temperature_k: float) -> float:
    """mu = coeffs[0] * exp(sum_{i>=1} coeffs[i]/T**i).

    Mirrors `exp_inv_t_eval` in tools/analyze/ethan_salt_hardening_common.py.
    Returns NaN for non-finite or zero temperature.
    """
    if not math.isfinite(temperature_k) or temperature_k == 0.0 or not coeffs:
        return NAN
    a = float(coeffs[0])
    exponent = 0.0
    for power_index, coeff in enumerate(coeffs[1:], start=1):
        exponent += float(coeff) / (temperature_k ** power_index)
    return float(a * math.exp(exponent))


def _polynomial(coeffs: tuple[float, ...], temperature_k: float) -> float:
    """sum_i coeffs[i] * T**i. Mirrors `polynomial_eval` in the common module."""
    if not math.isfinite(temperature_k):
        return NAN
    return float(sum(float(c) * (temperature_k ** i) for i, c in enumerate(coeffs)))


def jin_mu(temperature_k: float) -> float:
    """Jin dynamic viscosity mu(T) in Pa*s.

    mu(T) = 0.001149 * exp(-810.896/T + 780600/T**2).
    Coefficients from case_config.yaml mu_spec (type=expInvT) of the Salt 2/3/4
    Jin cases; see module docstring for exact source files. NaN-guarded.
    """
    return _exp_inv_t(_JIN_MU_COEFFS, temperature_k)


def kirst_mu(temperature_k: float) -> float:
    """Kirst dynamic viscosity mu(T) in Pa*s.

    mu(T) = 6.757e-05 * exp(2247.11/T).
    Coefficients from the kirst case_config.yaml mu_spec (type=expInvT); see
    module docstring. NaN-guarded.
    """
    return _exp_inv_t(_KIRST_MU_COEFFS, temperature_k)


def salt_rho(temperature_k: float) -> float:
    """Salt density rho(T) in kg/m^3:  rho = 2293.6 - 0.7497*T (rho_coeffs)."""
    return _RHO_A + _RHO_B * temperature_k if math.isfinite(temperature_k) else NAN


def salt_cp(temperature_k: float) -> float:
    """Salt specific heat cp(T) in J/(kg*K):  cp = 1423.47 (constant, Cp_coeffs)."""
    return _polynomial(_CP_COEFFS, temperature_k)


def salt_k(temperature_k: float) -> float:
    """Salt thermal conductivity k(T) in W/(m*K):  k = 0.78 - 0.00125*T + 1.6e-06*T**2."""
    return _polynomial(_K_COEFFS, temperature_k)


def temperature_from_rho(rho_kg_m3: float) -> float:
    """Invert the linear density EoS to recover bulk temperature (K).

    rho = 2293.6 - 0.7497*T  =>  T = (2293.6 - rho) / 0.7497.
    Returns NaN for a non-finite input.
    """
    if not math.isfinite(rho_kg_m3):
        return NAN
    return (_RHO_A - rho_kg_m3) / (-_RHO_B)
