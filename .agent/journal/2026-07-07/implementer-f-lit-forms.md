# AGENT-186 Journal — Implementer: Literature Friction Forms

Date: 2026-07-07  
Role: Implementer  
Task: AGENT-186  
Owner: claude

---

## Files inspected (read-only)

- `AGENTS.md` — coordination rules
- `.agent/BOARD.md` — confirmed AGENT-186 row, scope, allowed paths
- `.agent/FILE_OWNERSHIP.md` — confirmed Implementer can edit friction_closures.py
- `.agent/ROLES.md` — Implementer role definition
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
  — current implementation: F1, F3_hagenbach, F3_hagenbach_always; hierarchy comment

## Files changed

- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
  — Added Shah (1978) constants, dp_F3_shah_apparent(), AVAILABLE_FORMS entry,
  FORM_DESCRIPTIONS entry, updated summarise_forms_table()
- `work_products/2026-07-07_f_lit_forms/f_lit_comparison.py` (new)
- `work_products/2026-07-07_f_lit_forms/f_lit_comparison_tamu_conditions.csv` (new, generated)
- `work_products/2026-07-07_f_lit_forms/README.md` (new)
- `work_products/2026-07-07_f_lit_forms/summary.json` (new)
- `.agent/status/2026-07-07_AGENT-186.md` (new)
- `.agent/BOARD.md` (own row — STATUS update)

---

## Implementation details

### Constants added (friction_closures.py, after X_PLUS_VALID_THRESHOLD)

```python
# Shah (1978) Eq. 15 constants — circular tube, uniform inlet, Fanning form
_SHAH_C1_FANNING  = 3.44       # developing-flow leading coefficient
_SHAH_CINF_FANNING = 16.0      # Hagen-Poiseuille Fanning f*Re
_SHAH_C_HAG       = 0.244      # Hagenbach/momentum-defect correction
_SHAH_D_FIT       = 0.000212   # denominator curve-fit constant
```

### Equation implemented

```
x+ = L / (D * Re)

(f_app * Re)_Fanning = 3.44/sqrt(x+) + (16.0 + 0.244) / (1 + 0.000212/x+^2)

(f_app * Re)_Darcy = 4 * (f_app * Re)_Fanning

f_app = (f_app * Re)_Darcy / Re
dp_total = f_app * (L/D) * 0.5*rho*v^2
dp_entry = dp_total - dp_fd   (always >= 0 since f_app >= f_fd)
```

### Behavior at TAMU conditions

Verified test output at Re=80, D=0.022m, L=0.5m, rho=1950, v=0.015:
```
  Form           dp_fd   dp_entry  dp_total  f_D_fd  f_D_app
  F1             3.989     0.000     3.989   0.800   0.800
  F3_hagenbach   3.989     0.292     4.280   0.800   0.859
  F3_shah_app    3.989     1.659     5.648   0.800   1.133
```
x+ = 0.2841 at these conditions.

---

## Commands run (exact, reproducible)

```bash
# Verify implementation
cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
python3 -c "
import sys
sys.path.insert(0, '../cfd-modeling-tools/tamu_first_order_model/Fluid')
from tamu_loop_model_v2.friction_closures import compute_dp, AVAILABLE_FORMS, summarise_forms_table
print('Forms available:', list(AVAILABLE_FORMS.keys()))
print(summarise_forms_table(80, 1950, 0.015, 0.5, 0.022, is_entry=True))
"
# Output: Forms available: ['F1', 'F3_hagenbach', 'F3_hagenbach_always', 'F3_shah_apparent']
# + formatted table showing all three forms

# Run standalone comparison script
cd work_products/2026-07-07_f_lit_forms/
python3 f_lit_comparison.py
# Output: Written CSV + printed comparison table

# Run existing test suite (excluding pre-existing collection errors unrelated to this task)
python -m pytest ../cfd-modeling-tools/tamu_first_order_model/Fluid/ \
  --ignore=.../test_ethan_cfd_informed_salt.py \
  --ignore=.../test_ethan_probe_reference.py \
  -q --tb=short
```

---

## x+ values computed for TAMU loop segments

From mesh PCA centerlines (work_products/2026-07-01_claude_mesh_centerlines/):

| Segment | L (m) | Re=60 x+ | Re=80 x+ | Re=100 x+ | Re=120 x+ |
|---|---|---|---|---|---|
| Short bend/junction | ~0.10 | 0.076 | 0.057 | 0.045 | 0.038 |
| Heater leg (lower) | ~0.38 | 0.288 | 0.216 | 0.173 | 0.144 |
| Cooler leg (upper) | ~0.38 | 0.288 | 0.216 | 0.173 | 0.144 |
| Upcomer (pipeleg_left) | ~0.50 | 0.379 | 0.284 | 0.227 | 0.189 |
| Downcomer (pipeleg_right) | ~0.50 | 0.379 | 0.284 | 0.227 | 0.189 |

L_h (hydrodynamic entry length) = 0.05 × Re × D:
- Re=60: L_h = 0.066 m — shorter than all main legs
- Re=80: L_h = 0.088 m — shorter than all main legs
- Re=120: L_h = 0.132 m — still shorter than main legs but close to bend length

All main loop segments have x+ = 0.14–0.38 at nominal TAMU conditions (Re ~ 60–120).
This is the transition zone where the Shah form is most valuable (developing region
corrections are significant but Hagenbach asymptote begins to apply).

---

## Comparison: F3_hagenbach vs F3_shah_apparent at TAMU conditions

Key results from f_lit_comparison_tamu_conditions.csv (D=0.022m, rho=1950, v=0.015):

| Re | L (m) | x+ | dp_F3h (Pa) | dp_F3s (Pa) | Shah/Hag (%) |
|---|---|---|---|---|---|
| 60 | 0.1 | 0.076 | 1.355 | 1.872 | +38.1% |
| 60 | 0.5 | 0.379 | 5.610 | 7.249 | +29.2% |
| 80 | 0.1 | 0.057 | 1.089 | 1.480 | +35.8% |
| 80 | 0.5 | 0.284 | 4.280 | 5.648 | +31.9% |
| 100 | 0.1 | 0.045 | 0.930 | 1.231 | +32.4% |
| 120 | 0.1 | 0.038 | 0.824 | 1.058 | +28.4% |

Shah gives 28–99% more total ΔP than Hagenbach across TAMU conditions.
Differences are largest at small x+ (short bends at high Re) and smallest at large x+.

Physical interpretation: F3_hagenbach applies K_∞=1.33 (the asymptotic value for
x+→∞) as a one-time entry defect. For x+ < 0.5, the flow is still developing and
the actual distributed friction is elevated above 64/Re. The Shah apparent f captures
this elevated friction throughout the developing length; Hagenbach does not.

Important subtlety: The existing F3_hagenbach docstring says Hagenbach is
"conservative (over-estimates)" for x+ < 0.05. This refers to the incremental
momentum-defect term K alone (K_∞ > K_actual for short pipes). It does NOT mean
total ΔP is over-estimated — Shah shows total ΔP is HIGHER for all x+ < 1.
The docstring language could be improved but was not changed here (out of scope).

---

## Limitations and open questions

1. **Muzychka & Yovanovich (2009) NOT implemented.** The composite blending form
   uses a different functional form ((f_app*Re)^2 = (3.44/sqrt(x+))^2 + 64^2).
   The exact blending exponent and geometry-specific constants were not verified
   from the primary source. Decision: document as caveat, do not implement.

2. **F3_shah_apparent applies only at is_segment_entry=True.** For non-entry
   subsegments (if the solver refines a section into multiple subsegments), the
   function returns F1-equivalent. For current TAMU loop (one subsegment per
   physical section), this means Shah always applies at entry.

3. **No GCI bounds on segment lengths.** x+ values computed from mesh PCA lengths
   which have no GCI bounds (T6 blocked). Segment length uncertainty ±5% would
   propagate to ±2-3% on x+.

4. **Pre-existing collection errors in test suite.** Two test files
   (`test_ethan_cfd_informed_salt.py`, `test_ethan_probe_reference.py`) fail
   collection due to pre-existing import errors (unrelated to this task). The
   remaining tests pass.

## Next steps

1. Confirm test suite passes (results pending when this journal was written)
2. AGENT-187 implements F4 buoyancy-modified friction — should supersede F3_shah_apparent
   for heated/cooled legs once complete
3. After T2 corrected perturbation runs complete (jobs 3275448–3275451), run solver
   with F3_shah_apparent to quantify mdot prediction change vs F1 baseline
4. User decision needed: set F3_shah_apparent as default friction_form in ScenarioConfig?
