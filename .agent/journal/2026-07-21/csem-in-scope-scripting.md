# CSEM In-scope Scripting

Task: `TODO-CSEM-IN-SCOPE-SCRIPTING-2026-07-21`

Attempted: added a stable, repo-local validation helper for the external CSEM thesis local instruction layer so future agents do not need to create temporary scripts for routine checks.

Observed: scripts under `ethan_runs/` can run without external write approval when they only read external files or write under `ethan_runs/`. They cannot bypass filesystem restrictions for mutations in `../papers`.

Inferred: the useful split is to keep read-only validators and package/runbook generation in this repository, while any command that mutates the external thesis must use a stable approved prefix or a broader writable root.

Next: use `python3.11 tools/papers/check_csem_local_instruction_layer.py` for routine checks. For external CSEM edits, prefer stable scripts already under `../papers/UTexas_Research/csem-Masters_dissertation/scripts/` or request one stable approved prefix rather than using one-off `/tmp` scripts.

Validation: `python3.11 tools/papers/check_csem_local_instruction_layer.py`, `python3.11 -m py_compile tools/papers/check_csem_local_instruction_layer.py`, and `python3.11 -m json.tool imports/2026-07-21_csem_in_scope_scripting.json` passed. The validator reports known `TODO[source]` placeholders as notes, not failures.
