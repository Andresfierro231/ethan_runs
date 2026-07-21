# Continuity Protocol and Litrev Predictive Gates

Date: 2026-07-13  
Task: `AGENT-292`  
Role: Coordinator / Implementer / Tester / Writer

## Observed Facts

The board now has `AGENT-292` as the continuity and lit-rev predictive-gate
anchor. `AGENTS.md` and `CLAUDE.md` now share the same required form for new
research avenues: claim a board row, write a dated start-here or package README,
cross-link it, preserve literature provenance by author/title and repo evidence
by path, and close with status/journal/import artifacts.

The new compact handoff note is:

- `operational_notes/07-26/13/2026-07-13_CURRENT_CLOSURE_AND_PREDICTIVE_MODEL_START_HERE.md`

It points future agents to the lit-rev campaign index, lit-rev synthesis,
forward predictive research plan, external research index/blocker audit,
predictive input contract, and forward-v0 package.

The predictive input contract now carries five required pre-score lit-rev gate
rows:

- `source_envelope_gate`
- `property_mode_lane`
- `named_loss_table`
- `heat_loss_admission_table`
- `cfd_coefficient_naming_limits`

The forward-v0 runner now emits:

- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/forward_v0_litrev_gate_reference_audit.csv`

The audit requires all five gate references to exist and pass before score
tables are produced.

## Validation

- `module load python/3.12.11; python3 tools/analyze/test_predictive_input_contract.py`
  passed with 5 tests.
- `module load python/3.12.11; python3 tools/analyze/test_predictive_forward_v0_imposed_cooler.py`
  passed with 6 tests.
- `module load python/3.12.11; python3 tools/analyze/build_predictive_input_contract.py --strict`
  produced a strict-clean package with 32 runtime fields and 0 violations.
- `module load python/3.12.11; python3 tools/analyze/run_predictive_forward_v0_imposed_cooler.py --strict-input-contract --engine fast_scan --sensor-source both`
  produced 5 passing lit-rev gate references and 6 accepted fast-scan result
  rows.

`python3.11` was not usable for this validation because it lacked `yaml`; the
repo's default Python 3.9 has `yaml` but cannot parse the existing Python 3.10+
union syntax in these scripts. The `python/3.12.11` module has both modern syntax
support and `yaml`.

## Inferred Interpretation

The lit-rev synthesis products are now operational gates for predictive model
scoring. This prevents a forward run from treating literature closure forms,
property choices, named losses, heat-loss admissions, or CFD-derived
coefficients as implicitly admissible.

## Blockers

- `TODO-PRED-HX-FIT` remains the next model-building step; forward-v0 is still
  conditional on imposed cooler duty.
- Heater/test-section transfer, wall/storage terms, exact reverse/secondary flow
  diagnostics, and thermal mesh/GCI remain open blockers.
- Active scheduler/repair rows `AGENT-291` and `AGENT-290` remain separate and
  were not modified.

## Exact Files Changed

- `.agent/BOARD.md`
- `.agent/status/2026-07-13_AGENT-292.md`
- `.agent/journal/2026-07-13/continuity-protocol-and-litrev-predictive-gates.md`
- `imports/2026-07-13_continuity_protocol_and_litrev_predictive_gates.json`
- `AGENTS.md`
- `CLAUDE.md`
- `operational_notes/07-26/13/2026-07-13_CURRENT_CLOSURE_AND_PREDICTIVE_MODEL_START_HERE.md`
- `tools/analyze/build_predictive_input_contract.py`
- `tools/analyze/test_predictive_input_contract.py`
- `tools/analyze/run_predictive_forward_v0_imposed_cooler.py`
- `tools/analyze/test_predictive_forward_v0_imposed_cooler.py`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/**`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/**`

## Recommended Next Action

Claim or continue `TODO-PRED-HX-FIT` and use the new current-state handoff as
the first file. Any new branch of work should start with a board row and a
start-here note using the continuity protocol now present in both `AGENTS.md`
and `CLAUDE.md`.

