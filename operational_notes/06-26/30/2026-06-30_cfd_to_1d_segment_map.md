# CFD ↔ 1D Segment-Name Map (locked contract)

Date: `2026-06-30`
Owner: claude (AGENT-156)
Machine-checkable companion: `tools/analyze/validate_segment_map.py`
(re-run it after any closure-artifact change; it fails loudly on unmapped tokens).

## Why this exists

The closure artifacts use three different naming schemes for the same physical
legs, and the token `lower_leg` is geometrically misleading. A wrong CFD↔1D
mapping silently applies a closure (e.g. the test-section friction offset
`c=2.92`) to the wrong segment. This note is the authoritative map; the validator
enforces it.

## Authoritative CFD spans + loop roles (owner-confirmed, Ethan 2026-06-30)

NOTE: the probe coordinate frame in `tp_tw_probe_locations.csv` does NOT match
the physical loop orientation, so roles below come from the loop owner, not from
raw xyz. Roles are authoritative.

| CFD span | Loop role | Notes |
| --- | --- | --- |
| `lower_leg` | **Heated leg** (bottom leg) = `heated_incline` | Carries the heater BC. Do NOT confuse with `left_lower_leg`. |
| `right_leg` | **Downcomer** | The descending return leg (= `downcomer`). |
| `left_lower_leg` | **Upcomer** section 1/3 | Lower part of the riser. |
| `test_section_span` | **Upcomer** section 2/3 | The test section. |
| `left_upper_leg` | **Upcomer** section 3/3 | Upper part of the riser. |
| `upper_leg` | Cooled leg | Carries the cooler (`pipeleg_upper_05_cooler`). |

Composite loop groups (owner-defined):
- **`upcomer`** = `left_lower_leg` + `test_section_span` + `left_upper_leg` (the
  riser; analyzed both per-section and all-together).
- **`downcomer`** = `right_leg`.

Circulation: heated `lower_leg` → riser (`upcomer`, 3 left sections) → cooled
`upper_leg` → `downcomer` (`right_leg`) → back to `lower_leg`.

## Alias resolution (closure-artifact names → CFD span)

Confident:
- `test_section` (friction fit) → `test_section_span`
- `left_lower_vertical` (Nu fit) → `left_lower_leg`
- `lower_leg`, `right_leg`, `left_lower_leg`, `left_upper_leg`,
  `test_section_span`, `upper_leg` → themselves (canonical)
- `lower_leg_heater` → `lower_leg`; `cooler_sink_bucket` → `upper_leg`

Residual-bucket tokens (NOT single spans; lumped remainders, by design):
`features`, `cooler_return`, `reducers`, `corners`, `unsupported_walls`,
`cooler_vicinity`, `all_features`, `all_segments`.

**PROVISIONAL — needs domain confirmation (do not treat as final):**
- `heated_incline` (friction fit) → **provisionally** `lower_leg`. Reasoning:
  the heater BC is on `lower_leg` per `case_config.yaml`, so the heated straight
  is `lower_leg`; but the `_incline` wording is not confirmed against the actual
  heated patch list.
- `upcomer` (UA'/HTC targets) → **UNRESOLVED**. The "upcomer" (riser) is
  physically the heated leg where fluid rises; but the closure map groups it with
  the LEFT legs, conflicting with the heater being on the right (`lower_leg`).
  Must be confirmed.

## The collision to watch

`heated_incline` = `lower_leg` = the HEATED leg. It is a DIFFERENT span from
`left_lower_leg` (which is part of the `upcomer` riser). The similar names
(`lower_leg` vs `left_lower_leg`) are the main mis-wiring hazard: friction's
`heated_incline` must wire to `lower_leg`, never to `left_lower_leg`.

## Status: LOCKED (owner-confirmed 2026-06-30)

Both prior open questions are resolved:
1. `heated_incline` = `lower_leg` (heated leg) — confirmed.
2. `upcomer` = `left_lower_leg` + `test_section_span` + `left_upper_leg`;
   `downcomer` = `right_leg` — confirmed.

The validator (`validate_segment_map.py`) reports 0 unresolved / 0 provisional.
