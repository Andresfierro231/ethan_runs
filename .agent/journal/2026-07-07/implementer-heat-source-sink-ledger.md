# Implementer Journal — Heat Source/Sink Ledger

Date: 2026-07-07
Agent role: Implementer
Task ID: AGENT-194
Owner: claude

---

## Files Inspected

- `AGENTS.md` — repo rules (no login-node jobs, claim board row first, etc.)
- `.agent/BOARD.md` — confirmed AGENT-194 row is active; scope is narrow
- `.agent/FILE_OWNERSHIP.md` — tools/analyze/* owned by Implementer
- `.agent/ROLES.md` — Implementer role: work only assigned paths
- `tools/analyze/build_ethan_steady_state_heat_flow_audit.py` — understood format of wallHeatFlux.dat reader
- `work_products/2026-06-30_claude_thermal_htc/segment_htc_uaprime_*.csv` — T_bulk, wall_duty_Q_w per span
- `jadyn_runs/.../salt2_jin/.../postProcessing/wallHeatFlux/5398/wallHeatFlux.dat` — data format
- `jadyn_runs/.../salt2_jin/.../0/T` — BC type for all patches (1277 lines)
- `jadyn_runs/.../salt2_jin/.../postProcessing/mdot_pipeleg_lower_05_straight/5397/surfaceFieldValue.dat`
- `tools/case_analysis_profiles.py` — span/segment definitions, patch lists per span
- `tools/common.py` — helper functions (not used directly; kept standalone)

---

## Data Format Notes

### wallHeatFlux.dat
Tab/space-separated. Each line: `time  patch_name  min_W/m2  max_W/m2  Q_W  q_W/m2`
- Column 5 (Q_W) is already area-integrated in Watts — no need to multiply by area
- Sign convention: positive Q = heat INTO fluid (heater), negative Q = OUT of fluid (cooler/ambient)
- File accumulates multiple time steps (each restart segment appends)
- Latest time step is the last block of patch records in the highest-numbered time directory

### 0/T BC types (salt2 representative)
- Heater patches (pipeleg_lower_04/05/06): `rcExternalTemperature` with `Q = constant 88.57W`
- Test section (pipeleg_left_04): `rcExternalTemperature` with `Q = constant 37.0W`
- Cooler (pipeleg_upper_05): `externalTemperature` with `Q = constant -104.07W`
- Reducers (pipeleg_upper_04/06): `externalTemperature` with `Q = constant -16.14W`
- All passive walls: `rcExternalTemperature` with `h` and `Ta` but no Q
- Junction stubs: `externalTemperature` with only `h` and `Ta`
- NCC coupling faces: `zeroGradient` → always Q=0, skipped

### mdot_pipeleg_lower_05_straight surfaceFieldValue.dat
Format: `time  sum(phi)` where sum(phi) is mass flow rate in kg/s (negative convention)
Latest values (absolute): salt2=0.01320, salt3=0.01499, salt4=0.01711 kg/s

### HTC CSV T_bulk values per span
Single mid-span T_bulk per span (not inlet/outlet):
- lower_leg: salt2=444.5K, salt3=457.3K, salt4=472.5K
- upcomer: salt2=456.7K, salt3=469.5K, salt4=484.9K
- downcomer: thermally blocked (no data)

---

## Commands Run

```bash
# Exploration
ls work_products/2026-06-30_claude_thermal_htc/
find jadyn_runs/.../salt2_jin/ -name "wallHeatFlux.dat" | head -5
head -60 postProcessing/wallHeatFlux/5398/wallHeatFlux.dat
tail -60 postProcessing/wallHeatFlux/5398/wallHeatFlux.dat  # shows t=7915s latest
ls postProcessing/  # found mdot_* directories
tail -5 mdot_pipeleg_lower_05_straight/5397/surfaceFieldValue.dat  # mdot format
grep "Q " 0/T | head -5  # heater/cooler Q values
head -80 work_products/2026-06-30_claude_thermal_htc/segment_htc_uaprime_*.csv  # T_bulk

# Build and test
python tools/analyze/build_heat_source_sink_ledger.py
python -m pytest tools/analyze/test_heat_source_sink_ledger.py -v  # 36 passed
python -m pytest tools/analyze/test_*.py tools/extract/test_*.py -q  # 288 passed
```

---

## Results and Observations

### wallHeatFlux_integral_W per patch_group (latest time step)

| Source | Heater (lower_leg) | Cooler (cooling_branch) | Test_section (upcomer) | Net balance |
|---|---|---|---|---|
| salt_2 | +243.5 W | -136.4 W | -5.7 W | +0.1 W (0.052%) |
| salt_3 | +273.2 W | -150.8 W | -10.5 W | +0.3 W (0.105%) |
| salt_4 | +310.5 W | -169.2 W | -16.8 W | +0.1 W (0.026%) |

Heater Q in CFD (243–311 W) < BC-specified Q (266–338 W); difference is heat lost
through insulation to ambient before reaching the fluid.

HTC CSV `wall_duty_Q_w` for lower_leg: salt2=236.85W, salt3=265.83W, salt4=302.33W.
This is the SUM of all lower_leg patches (heater + passive ambient). Verification:
- heater + ambient_wall(lower_leg) = 243.5 + (-6.7) = 236.8 W ≈ 236.85 W in HTC ✓

### Test section paradox (documented in README)
pipeleg_left_04_test_section has Q=37W electrical in BC but wallHeatFlux is NEGATIVE
(-5.7 to -16.8 W). The upcomer fluid is hot (456–485K), external h is low (7.5 W/m²K),
and internal convection is strong. Net heat flow is from fluid → quartz → ambient.
bc_sign_convention = "imposed_into_fluid" (design intent), but actual Q < 0 for all cases.
This is physically consistent and documented.

### Junction losses
Four corners together lose 39–48 W per case. This is the largest single passive loss.
Includes: stubs (calibrated high h), extensions (rcExternalTemperature), and junction faces.

### Net balance
Salt 2/4: < 0.1% → PASS. Salt 3: 0.105% → just above threshold (quasi-steady CFD).
All three cases are within 1% gate used in tests.

---

## Files Changed

**Created:**
- `tools/analyze/build_heat_source_sink_ledger.py`
- `tools/analyze/test_heat_source_sink_ledger.py`
- `work_products/2026-07-07_heat_source_sink_ledger/heat_source_sink_ledger.csv`
- `work_products/2026-07-07_heat_source_sink_ledger/heat_source_sink_ledger.json`
- `work_products/2026-07-07_heat_source_sink_ledger/README.md`
- `work_products/2026-07-07_heat_source_sink_ledger/summary.json`
- `.agent/status/2026-07-07_AGENT-194.md`
- `.agent/journal/2026-07-07/implementer-heat-source-sink-ledger.md` (this file)

**No files modified** (only new files created within claimed scope).

---

## Incomplete Lines of Investigation

- enthalpy_change_W: would require T_bulk at span interfaces (NCC stations TW2/TW4/TW6/TW8);
  these are available in postProcessing/temperature_probes but not extracted for this task
- Resistance network decomposition: wall thickness and per-layer conductivity data is in 0/T
  (thicknessLayers, kappaLayerCoeffs) but parsing and decomposition is a future task
- Salt 3 net balance at 0.105%: could improve by averaging over a time window rather than
  using a single latest time step; would require re-reading all time steps in the dat file
- NCC patch areas: ncc_* junction patches in junction_other group contribute Q=0 but inflate
  the patch_names list; could be filtered for display clarity without changing results

---

## Next Steps

1. To enable enthalpy_change_W: extract T_bulk at NCC interface stations from
   `postProcessing/temperature_probes/` or cut-plane tools
2. Resistance network decomposition: read `thicknessLayers` + `kappaLayerCoeffs` from 0/T
   per patch, compute R_wall per unit area, then decompose the total resistance
3. If needed for paper: recompute with time-averaged wallHeatFlux rather than single
   latest time step (average over the stationary window)
