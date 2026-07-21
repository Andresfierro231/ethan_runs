# Journal: Pressure Ledger Entry Flag Fix (AGENT-197)

Date: 2026-07-07
Agent role: Implementer
Task ID: AGENT-197
Owner: claude

---

## Problem

`build_pressure_term_ledger.py` called `dp_F3_shah_apparent(..., is_segment_entry=True)`
for every span unconditionally. For the three contiguous upcomer sub-spans:

```
left_lower_leg → test_section_span → left_upper_leg
```

`left_lower_leg` correctly receives fresh entry flow (after the lower-left bend).
But `test_section_span` and `left_upper_leg` receive already-developed flow from
the preceding sub-span. Applying the Shah flat-inlet entry assumption to them is
physically incorrect. The symptom: `dev_frac > 1.0` for `left_upper_leg` in Salt 3/4
(the Shah correction exceeded the distributed friction, which is unphysical).

---

## Files Inspected

- `tools/analyze/build_pressure_term_ledger.py` (full read)
- `tools/analyze/test_pressure_term_ledger.py` (full read)
- `work_products/2026-07-07_pressure_term_ledger/pressure_term_ledger.csv` (head + spot-checks)
- `.agent/BOARD.md` — confirmed AGENT-197 row claimed for claude/Implementer
- `AGENTS.md`, `.agent/FILE_OWNERSHIP.md`, `.agent/ROLES.md` — pre-edit protocol

---

## Changes Made

### `tools/analyze/build_pressure_term_ledger.py`

1. Added `SPAN_IS_ENTRY: Dict[str, bool]` constant after `RECIRCULATION_SPANS`:
   - `lower_leg`, `right_leg`, `left_lower_leg`, `upper_leg` → `True`
   - `test_section_span`, `left_upper_leg` → `False`
   With explanatory comment documenting the physical rationale.

2. Modified `compute_development_loss()` signature:
   - Added `span_name: str = ""` parameter (backward-compatible default)
   - Returns `0.0` immediately when `SPAN_IS_ENTRY.get(span_name, True)` is False
   - Updated docstring to explain entry vs. non-entry logic

3. Updated call site in `build_ledger()`:
   ```python
   development_loss_pa = compute_development_loss(Re, rho, u_bulk, L_m, D_h_m, span_name=span)
   ```

4. Added `flow_reset_flag = SPAN_IS_ENTRY.get(span, True)` to row computation.

5. Added `"flow_reset_flag"` to the row dict and to `CSV_COLUMNS`.

6. Updated README embedded in the script:
   - Added `flow_reset_flag` to the column description table
   - Updated caveat 2 to explain the entry/non-entry distinction
   - Updated `development_loss_pa` column description to note 0.0 for non-entry spans

### `tools/analyze/test_pressure_term_ledger.py`

1. Updated module docstring to mention Tests 10 and 11.
2. Added `"flow_reset_flag"` to `REQUIRED_COLUMNS`.
3. Added module-level constants `NON_ENTRY_SPANS` and `ENTRY_SPANS`.
4. Added **Test 10** (`test_development_loss_zero_for_non_entry_spans`):
   verifies `development_loss_pa == 0.0` (within 1e-12) for `test_section_span`
   and `left_upper_leg` across all 3 salt cases.
5. Added **Test 11** (`test_flow_reset_flag`):
   verifies `flow_reset_flag=False` for `NON_ENTRY_SPANS`,
   `flow_reset_flag=True` for `ENTRY_SPANS`.

---

## Commands Run

```bash
# Regenerate outputs
python tools/analyze/build_pressure_term_ledger.py

# Targeted tests
python -m pytest tools/analyze/test_pressure_term_ledger.py -v

# Full regression suite
python -m pytest tools/analyze/test_*.py tools/extract/test_*.py -q
```

---

## Results and Observations

Script output (diagnostic section):
```
left_upper_leg: dev_frac=+0.000 (all 3 cases)
test_section_span: not listed (not in main_spans diagnostic, but CSV-verified)
```

Spot-check of CSV:
```
salt_test_4/left_upper_leg:  development_loss_pa=0.0  flow_reset_flag=False
salt_test_3/left_upper_leg:  development_loss_pa=0.0  flow_reset_flag=False
salt_test_2/left_upper_leg:  development_loss_pa=0.0  flow_reset_flag=False
salt_*/test_section_span:    development_loss_pa=0.0  flow_reset_flag=False
```

Test results:
- `test_pressure_term_ledger.py`: 11 passed (9 original + 2 new)
- Full suite (`test_*.py` + `tools/extract/test_*.py`): 299 passed, 0 failed, 0 errors

---

## Incomplete Lines of Investigation

None. The fix is complete and physically well-motivated.

Note: the `left_lower_leg` span also participates in the upcomer recirculation zone
(15–33% backflow), so its momentum budget is approximate. The `recirculation_flag`
column already documents this. The entry assumption for `left_lower_leg` is retained
because it genuinely enters after the lower-left bend; the backflow issue is a separate
concern from the entry-length assumption.

---

## Next Steps

- The `flow_reset_flag` column is now available for downstream consumers
  (e.g., the observation table, model-form bakeoff) to correctly exclude Shah-based
  development loss from non-entry spans when computing closure candidates.
- If additional sub-spans are added to the ledger, their entry status should be
  determined from the loop topology and added to `SPAN_IS_ENTRY`.
