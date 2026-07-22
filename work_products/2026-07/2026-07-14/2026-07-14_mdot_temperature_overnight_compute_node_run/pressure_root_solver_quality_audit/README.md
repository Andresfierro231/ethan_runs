# Pressure-Root Solver Quality Audit

This local QA diagnostic re-runs AGENT-360 pressure-root modes and records the
fast-scan root residual and pressure residual at CFD mdot. It is intended to
flag modes where the root search, not the physics closure, may dominate error.
