# Implementer journal — F4 stub mapping fix

Date: 2026-07-07
Agent role: Implementer
Task ID: AGENT-199

---

## Files inspected

- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/AGENTS.md`
- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/.agent/BOARD.md` (AGENT-199 row confirmed)
- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/.agent/FILE_OWNERSHIP.md`
- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/.agent/ROLES.md`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py` (lines 526–548)
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/geometry.py` (Segment class + loop_geometry function)
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_friction_closures.py`
- `work_products/2026-07-07_friction_forms_comparison/run_mdot_comparison.py` (lines 58–75, runtime patch)

---

## Segment names found in geometry

Confirmed from `geometry.py` (lines 214, 218, 220, 222):

| Segment name | parent_name | Notes from geometry |
|---|---|---|
| `top_horizontal_inlet` | `top_horizontal_inlet` | "1 inch horizontal run between the upcomer and the cooled incline." |
| `top_horizontal_exit` | `top_horizontal_exit` | "1 inch horizontal run between the cooled incline and TP1." |
| `bottom_horizontal_inlet` | `bottom_horizontal_inlet` | "1 inch horizontal run between TP2 and the heated incline." |
| `bottom_horizontal_exit` | `bottom_horizontal_exit` | "1 inch horizontal run that closes the loop back to TP3." |

Names match the task brief exactly. No name adjustment needed.

---

## Leg-class assignment decision

The task brief (AGENT-199) suggested:
- `top_horizontal_inlet` → "cooler"
- `top_horizontal_exit` → "cooler"
- `bottom_horizontal_inlet` → "downcomer"
- `bottom_horizontal_exit` → "heater"

AGENT-195's runtime patch (`run_mdot_comparison.py`, line 67–73) used:
- `top_horizontal_inlet` → "cooler"
- `top_horizontal_exit` → "downcomer"
- `bottom_horizontal_inlet` → "heater"
- `bottom_horizontal_exit` → "upcomer"

### Analysis

The TAMU loop flow direction (buoyancy-driven CCW from left side up):

```
TP3 → left_lower_vertical (upcomer) → test_section → left_upper_vertical → TP6
     → top_horizontal_inlet → cooled_incline_* (cooler) → top_horizontal_exit → TP1
     → right_vertical (downcomer) → TP2
     → bottom_horizontal_inlet → heated_incline (heater) → bottom_horizontal_exit → TP3
```

The AGENT-195 values follow a **downstream-classification principle**: each stub takes
the `leg_class` of the main segment it feeds into. This is physically consistent:
- `top_horizontal_inlet` → feeds into cooled_incline → "cooler"
- `top_horizontal_exit` → feeds into right_vertical (downcomer) → "downcomer"
- `bottom_horizontal_inlet` → feeds into heated_incline (heater) → "heater"
- `bottom_horizontal_exit` → feeds into left_lower_vertical (upcomer) → "upcomer"

The AGENT-199 brief rationale has internal inconsistencies:
- "top_horizontal_inlet/exit: near the cooler → 'cooler'" groups both stubs on the same "cooler"
  class even though top_horizontal_exit leads to the downcomer, not the cooler.
- "bottom_horizontal_exit: exits to heater" is factually wrong — bottom_horizontal_exit goes from
  heater_end to TP3 (the upcomer), not TO the heater.
- The brief appears to use UPSTREAM classification for 3 of 4 stubs and DOWNSTREAM for 1,
  producing inconsistent results.

### Decision

Adopted the AGENT-195 (downstream-classification) values. Rationale:
1. Physically consistent: each stub inherits the thermal character of the main segment it
   transitions the flow into.
2. Already used in the comparison run that produced the AGENT-195 mdot results; changing to
   different values would create inconsistency with reported comparison outputs.
3. The "provisional" label applies equally to both schemes; downstream is at least internally
   consistent.

---

## Files changed

### `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`

Added 11 lines after line 534 (after `"cooled_incline_post_hx": "cooler"`):

```python
    # horizontal manifold stubs — leg_class follows the downstream main segment; provisional
    # Flow direction: upcomer → top_horizontal_inlet → cooled_incline
    #                → top_horizontal_exit → right_vertical (downcomer)
    #                → bottom_horizontal_inlet → heated_incline (heater)
    #                → bottom_horizontal_exit → left_lower_vertical (upcomer)
    # Each stub inherits the thermal character of the main segment it feeds into.
    # This matches the AGENT-195 runtime patch (2026-07-07) used in run_mdot_comparison.py.
    "top_horizontal_inlet":    "cooler",     # upcomer → (stub) → cooled_incline_pre_hx
    "top_horizontal_exit":     "downcomer",  # cooled_incline_post_hx → (stub) → right_vertical
    "bottom_horizontal_inlet": "heater",     # right_vertical → (stub) → heated_incline
    "bottom_horizontal_exit":  "upcomer",    # heated_incline → (stub) → left_lower_vertical (TP3)
```

### `../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_friction_closures.py`

- Added `from unittest.mock import MagicMock` import.
- Added `from tamu_loop_model_v2.solver import _F4_LEG_CLASS_BY_PARENT_SEGMENT, _friction_closure_kwargs_for_segment` import.
- Added `_mock_segment(parent_name)` helper function.
- Added `TestF4StubMapping` class with 7 test methods:
  - `test_top_horizontal_inlet_maps_to_cooler`
  - `test_top_horizontal_exit_maps_to_downcomer`
  - `test_bottom_horizontal_inlet_maps_to_heater`
  - `test_bottom_horizontal_exit_maps_to_upcomer`
  - `test_stub_segments_present_in_dict`
  - `test_unknown_stub_still_raises_ValueError`
  - `test_non_f4_form_returns_empty_dict_for_stub`

---

## Commands run

```bash
# Verify segment names
grep -r "top_horizontal\|bottom_horizontal" \
  ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/geometry.py

grep -r "top_horizontal\|bottom_horizontal" \
  work_products/2026-07-07_friction_forms_comparison/run_mdot_comparison.py

# Run Fluid test suite
cd ../cfd-modeling-tools && python -m pytest \
  tamu_first_order_model/Fluid/tests/test_friction_closures.py -v

# Run ethan_runs test suite
python -m pytest tools/analyze/test_*.py tools/extract/test_*.py -q
```

---

## Results

- Fluid tests: **52/52 passed** (7 new tests from TestF4StubMapping).
- ethan_runs tests: **299/299 passed**.

---

## Incomplete lines of investigation

- The AGENT-195 comparison script still contains the runtime patch
  (`S._F4_LEG_CLASS_BY_PARENT_SEGMENT.update(_STUB_LEG_CLASS_PATCH)`). Since solver.py now has
  canonical values, the patch is a no-op but is not harmful. A future cleaner pass could remove it.
- Buoyancy effects on horizontal stubs: F4 uses leg-class-specific friction multipliers derived
  from CFD. Short horizontal stubs at low Re may not exhibit the same buoyancy-modified friction
  as the inclined main segments. The "provisional" flag should be surfaced in any F4 paper claim.

## Next steps

- AGENT-200 (F5_ri_corrected) can proceed; it reads solver.py for F4 and will see the complete
  12-entry `_F4_LEG_CLASS_BY_PARENT_SEGMENT`.
- If corrected Salt perturbation runs (3275448–3275451) yield new Re points, the stub
  leg_class assignments should be revisited with buoyancy-informed evidence.
