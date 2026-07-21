# Session Journal: Ri Audit + Span Endpoint Temperatures

Date: `2026-07-08`
Agent Role: Implementer / Writer
Tasks: AGENT-203, AGENT-204

---

## Files Inspected

- `jadyn_runs/.../system/functions` — dimensionlessFields FO source; hardcoded D, TRef, rhoRef
- `jadyn_runs/.../0/T` (S2) — all BC types, layer thicknesses, Q values, emissivity
- `jadyn_runs/.../constant/momentumTransport` — simulationType laminar
- `jadyn_runs/.../constant/thermophysicalTransport` — laminar Fourier model
- `jadyn_runs/.../constant/fvModels` — empty (heater in BC, not fvModels)
- `jadyn_runs/.../case_config.yaml` — heater_power_W per case
- `work_products/2026-07-08_cfd_scenario_contract/scenario_contract.csv` — AGENT-202 output
- `tmp/2026-06-30_claude_action_items/recon_salt{2,3,4}_of13/postProcessing/secmeanSurfaces/{time}/`
- `work_products/2026-07-07_heat_source_sink_ledger/heat_source_sink_ledger.csv`
- `tools/extract/sample_segment_htc_uaprime.py` — reference for XY file patterns

## Files Changed

### New files
- `operational_notes/07-26/08/2026-07-08_ri_characteristic_length_audit.md`
- `tools/extract/sample_span_endpoint_temperatures.py` (AGENT-203 primary tool)
- `tools/extract/test_sample_span_endpoint_temperatures.py` (17 tests)
- `work_products/2026-07-08_span_endpoint_temperatures/span_endpoint_temperatures.csv`
- `work_products/2026-07-08_span_endpoint_temperatures/summary.json`
- `work_products/2026-07-08_span_endpoint_temperatures/README.md`
- `.agent/status/2026-07-08_AGENT-203.md`
- `.agent/status/2026-07-08_AGENT-204.md`

### BOARD.md modified
Added AGENT-203 and AGENT-204 rows (fixed "modified since read" error on first attempt).

## Commands Run

```bash
# Inspection
head -12 tmp/.../recon_salt2_of13/postProcessing/secmeanSurfaces/7915/plane_lower_leg__s00.xy
python3 -c "import numpy as np; data=np.loadtxt(... # rho diagnostics

# Tests
python -m pytest tools/extract/test_sample_span_endpoint_temperatures.py -v -s  # all 17 pass
python -m pytest tools/analyze/test_*.py tools/extract/test_*.py -q  # 331 pass

# Extraction
python tools/extract/sample_span_endpoint_temperatures.py \
  --recon-root tmp/2026-06-30_claude_action_items \
  --heat-ledger work_products/2026-07-07_heat_source_sink_ledger/heat_source_sink_ledger.csv \
  --output-dir work_products/2026-07-08_span_endpoint_temperatures
```

## Key Results and Observations

### AGENT-204: Ri characteristic length — confirmed correct

- CFD uses D_h = 22.098 mm globally for ALL cells (hardcoded in system/functions)
- This is correct for internal pipe flow mixed convection (Ri = Gr/Re² with D_h)
- Test section actual bore = 20.9 mm → 5.7% Ri overestimate, ~2% bias on upcomer median Ri
- Grashof uses exact density-difference form (not Boussinesq), < 1% difference at operating T
- TRef = 447 K, rhoRef = 1958.48 kg/m³ (consistent)
- Test section is net heat sink: 2.2 mm quartz only, ε=0.95, no insulation

### AGENT-203: Span endpoint T extraction

**Algorithm validated**: T = (2293.6 − rho) / 0.7497 from 8-col XY files (exact for linear EOS).
T_bulk = Σ(ρ·u_n·T) / Σ(ρ·u_n) (mass-flux-weighted, valid for constant cp).

**Critical finding: upcomer recirculation**

The upcomer (left_lower_leg, test_section_span, left_upper_leg) has 85–98% recirculation
at endpoint cut planes. The standard mixing-cup T diverges to 370–1012 K (outside physical range).

Solution: report both `T_bulk_k` (mixing-cup, energy-balance correct) and `T_fwd_bulk_k`
(forward-flow only, physically realistic). Use T_fwd when recirculation_ratio > 0.5.

**Pipe-centre masking issue**

The lower_leg and right_leg cut planes are diagonal/long — faces span up to 0.88 m in y.
Fixed by using the 80th-percentile velocity faces as pipe centre estimate (velocity-based
clustering), rather than the centroid of all faces.

**Flow direction correction**

lower_leg FLOW_DIRECTION was initially set to +1 (wrong). Correct is -1: fluid flows
from s04 (downcomer junction, x~0.8) to s00 (upcomer junction, x~0.1).

**Heater energy balance**

| Case | Q_heater W | dT K | Error vs Q/mdot·cp |
|---|---|---|---|
| S2 | 265.7 | +15.35 | +8.5% |
| S3 | 297.5 | +15.79 | −0.3% |
| S4 | 337.6 | +16.44 | −8.5% |

Error bounded within ±8.5% — consistent with 28.7% recirculation at lower_leg s00 (heater exit).

**Cooler energy balance**: only 45-51% of Q_cooler captured — upper_leg cut planes don't bracket
the full cooler (reducers extend beyond the span boundaries).

## F5 Ri correction failure — root cause documented this session

Written to `operational_notes/07-26/08/2026-07-08_friction_ri_failure_and_path_forward.md`.

Summary: F5 failed because:
1. phi varies only 15–27% within each leg class across 3 operating points — smaller than
   the noise level with 0 DOF (3-point forced-intercept OLS)
2. phi trend is not monotone (cooler phi decreases with Ri — wrong direction)
3. Ri and Re change together across S2/S3/S4 (both driven by Q); can't separate them
4. Self-consistent Ri not implemented in 1D solver (circularity)
5. The dominant ~2× phi offset above F3_shah is NOT Ri-driven — likely entry-length +
   geometry effects + buoyancy-driven secondary flow

Recommended path: fit phi vs Re (Option A), add per-segment insulation BCs,
add self-consistent Ri to solver, pursue wider Re range via T13 onset campaign.

## Incomplete Lines of Investigation

1. Full cooler coverage requires cut planes at the actual pipeleg_upper_04/05/06 reducer endpoints
2. Right_leg (downcomer) T values are ambiguous due to recirculation at s04 (76.3%) and bend at s00
3. Upcomer energy balance requires volume-averaged T approach or finer cut plane placement

## Next Steps

- AGENT-204: present Ri audit findings at tomorrow's meeting (fully documented)
- AGENT-203: heater dT values are ready for heat ledger cross-check table
- Per-segment insulation BCs for 1D model (needed to physically match CFD setup)
- Check corrected Salt Q perturbation job status (gate job 3280969)
