# TODO-CSEM-IN-SCOPE-SCRIPTING-2026-07-21

Role: Implementer / Tester / Writer

Status: Complete.

Task: `TODO-CSEM-IN-SCOPE-SCRIPTING-2026-07-21`

## Objective
Add an in-scope helper so agents can validate the external CSEM thesis local instruction layer without creating ad hoc `/tmp` scripts or needing external write permission for read-only checks.

## Changes Made
- `.agent/BOARD.md`
- `tools/papers/check_csem_local_instruction_layer.py`
- `.agent/status/2026-07-21_TODO-CSEM-IN-SCOPE-SCRIPTING-2026-07-21.md`
- `.agent/journal/2026-07-21/csem-in-scope-scripting.md`
- `imports/2026-07-21_csem_in_scope_scripting.json`

## Validation
- PASS: `python3.11 tools/papers/check_csem_local_instruction_layer.py`.
  - Confirms required CSEM local instruction/build files exist.
  - Confirms no `TODO.md` files exist in the external CSEM thesis or LitRev trees.
  - Confirms no live `enumitem` package use and no live optional list starts.
  - Confirms `masterthesis.log` has no unresolved citation/reference warnings.
  - Reports known `TODO[source]` placeholders in Chapter 3 and two appendices as residual board-scoped evidence-import work.
- PASS: `python3.11 -m py_compile tools/papers/check_csem_local_instruction_layer.py`.
- PASS: `python3.11 -m json.tool imports/2026-07-21_csem_in_scope_scripting.json`.

## Guardrails
No external papers files, CSEM thesis source, LitRev source, CFD outputs, registry/admission state, scheduler state, Fluid source, or generated docs indexes are edited by this helper. External mutation still requires an approved command prefix or a widened writable root; this script is deliberately read-only.
