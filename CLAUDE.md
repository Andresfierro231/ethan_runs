# CLAUDE.md — Context bootstrap for Claude (ethan_runs repo)

Reviewed: `2026-07-04`

This file is the Claude equivalent of `AGENTS.md`. Claude does not auto-load
`AGENTS.md` on startup, so this file provides the same orientation.

---

## 1. Required reading (read these in order before doing any work)

1. **`AGENTS.md`** (repo root) — non-negotiable rules, file-ownership policy,
   no-login-node rule, coordination protocol.
2. **`.agent/BOARD.md`** — current active tasks, their owners, their allowed
   edit paths, and the unclaimed task queue. Claim a row BEFORE editing.
3. **`.agent/FILE_OWNERSHIP.md`** — which paths belong to which agents.
4. **`.agent/ROLES.md`** — role definitions (Coordinator / Implementer / Writer / etc.).
5. **`operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md`** —
   the definitive current-phase task backlog (T1–T13 with context, method,
   acceptance, deps).

For any session doing 1D-model or CFD closure work, also read:
- `operational_notes/06-26/30/2026-06-30_mesh_geometry_vs_probe_csv_provenance.md`
  (CRITICAL: probe CSV ≠ mesh geometry; lower↔right labels swapped)
- `operational_notes/06-26/30/2026-06-30_cfd_1d_closure_workflow.md`
  (how to run every tool, OF13 env, reconstruction recipe)
- `.agent/DECISIONS.md` — architectural decisions with rationale

---

## 2. Workspace role

`ethan_runs/` is the heavy-data intake and preprocessing workspace for
Ethan-provided TAMU molten-salt natural-circulation loop CFD cases.

**This is not a generic software project.** It is a scientific research repo
combining:
- OpenFOAM 13 CFD cases (`jadyn_runs/modern_runs/`)
- Python postprocessing tools (`tools/`)
- 1D thermal-hydraulic model (`../cfd-modeling-tools/tamu_first_order_model/`)
- Extracted results (`work_products/`, `reports/`, `tmp_extract/`)
- Research context (`operational_notes/`, `.agent/journal/`)

---

## 3. Current phase summary (as of 2026-07-04)

**Phase: 1D model closure extraction and validation (July 2026)**

The goal is to improve the TAMU 1D loop model so it predicts the CFD-computed
mass-flow rate and temperature distribution, and can be compared against many
friction-factor and heat-transfer closure forms from the literature.

### What is trustworthy right now
- Thermal closures (HTC, UA', Nu, R') from patch-based extraction on mainline
  Salt 2/3/4 Jin continuations — `work_products/2026-06-30_claude_thermal_htc/`
- Buoyancy-corrected friction factors per span — `work_products/2026-07-01_claude_momentum_budget/`
- Upcomer recirculation exists (backflow 15–33%); lower_leg is the heater (inclined ~21°)
- Corrected segment-length geometry from mesh PCA — `work_products/2026-07-01_claude_mesh_centerlines/`

### What is NOT trustworthy / not yet done
- Friction from the old probe-CSV-based cut planes (lower↔right swapped) — superseded by momentum budget
- All 14 Q-perturbation runs are **false-steady** (mdot never moved); quarantined
- No mesh-independence (GCI) bounds yet (T6 blocked — needs external NCC mesh generator from Ethan)
- Upcomer correlation has only 3 coupled Re points; onset Re is extrapolated

### What changed 2026-07-04
- **Friction closure library** created: `cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
  — F1 (64/Re) and F3_hagenbach (64/Re + Hagenbach entry correction) implemented; solver wired via `friction_form: str = "F1"` on `ScenarioConfig`; backward-compatible.
- **Corrected Salt Q perturbation runs** submitted (3275448–3275451) — patched
  restart field + all heater/cooler patches + dynamicCode. These are the corrected
  replacement for the quarantined June 19/25 runs.
- **Gap analysis job** submitted (3275531) — insulation sweep + per-leg friction diagnosis.
- **Comparison script** created: `work_products/2026-07-04_friction_forms/run_friction_forms_compare.py`

---

## 4. Current open tasks (headline — see MASTER TODO for detail)

| ID | Priority | Status | Description |
|---|---|---|---|
| T2 | HIGH (user-requested) | RUNNING (3275448–3275451) | Corrected Salt Q perturbation runs; await mdot movement |
| T6 | HIGH | BLOCKED | Mesh-independence GCI — needs external NCC mesh generator |
| T10 | MED | BLOCKED on T2/T13 | Upcomer correlation fit (needs more Re points) |
| T11 | MED | BLOCKED on T6 | Closure bundle refresh (needs GCI bounds) |
| T13 | HIGH | DESIGN done | Onset/limit CFD campaign (needs T2 requalification first) |
| F4 | NEW | PENDING | Buoyancy-modified friction (Ri correction for heated/cooled verticals) |
| F-lit | NEW | PENDING | Laminar friction forms from lit review (Shah, Baehr-Stephan, etc.) |

**Next recommended 1D model tasks:**
1. Monitor corrected perturbation jobs (3275448–3275451): check that mdot actually moves
2. Run gap analysis results (job 3275531): insulation sweep + per-leg diagnosis
3. Implement F4 buoyancy-modified friction (next closure in the hierarchy)
4. Add more laminar friction correlations to `friction_closures.py` from LitRev

---

## 5. Key file paths

| What | Path |
|---|---|
| 1D model source | `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/` |
| Friction closures (NEW) | `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py` |
| Solver config | `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py` |
| CFD momentum budget (f per span) | `work_products/2026-07-01_claude_momentum_budget/momentum_budget.json` |
| Segment arc lengths | `work_products/2026-07-01_claude_segment_friction/segment_friction.csv` |
| Thermal closures (HTC, Nu) | `work_products/2026-06-30_claude_thermal_htc/` |
| Mesh-true centerlines | `work_products/2026-07-01_claude_mesh_centerlines/` |
| Corrected perturbation runs | `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/` |
| Per-leg friction compare script | `work_products/2026-07-04_friction_forms/run_friction_forms_compare.py` |
| OF13 env script | `tools/ofenv/of13_env.sh` |
| Tests baseline (62 passing) | `python -m pytest tools/analyze/test_*.py tools/extract/test_*.py -q` |

---

## 6. Hard gotchas (will break you if ignored)

1. **OF13 env required for T reconstruction**: `source tools/ofenv/of13_env.sh`
   then `module load gcc/15.2.0`. Under OF12, the custom BC (`libRCWallBC.so`) SEGFAULTS.
   Run `reconstructPar` in ONE FOREGROUND call (background kills get killed mid-merge).
2. **Do NOT source OF env when running Python** — it swaps libstdc++ and breaks Python.
   Tools wrap foamPostProcess in a subshell.
3. **Probe CSV (`tp_tw_probe_locations.csv`) is a schematic** — does NOT match mesh.
   `lower_leg` in CSV = downcomer in mesh. `right_leg` in CSV = heater in mesh. Use
   mesh PCA centerlines for geometry.
4. **Characteristic Ri = section MEDIAN**, not mean. The mean is ~100× larger (dominated
   by near-zero velocity cells).
5. **Sbatch from compute nodes**: use `ssh login3.ls6.tacc.utexas.edu "/usr/bin/sbatch <absolute_path>"`.
6. **Salt 1 Jin**: weakly converged; use with caution. Salt 2/3/4 are solid.
7. **Upcomer = left side** (pipeleg_left): the upward-flow leg with a recirculation cell.
   Downcomer = right side (pipeleg_right).

---

## 7. Coordination rules summary

- Claim a BOARD.md row BEFORE editing any shared file.
- Do NOT edit `tools/case_analysis_profiles.py` without coordinator approval.
- Do NOT mutate `jadyn_runs/` case_stage trees — stage into a fresh dated dir.
- Do NOT run long/expensive jobs on login nodes (use sbatch or interactive `idev`).
- Write a dated journal entry at end of any significant work session under
  `.agent/journal/YYYY-MM-DD/<role>-<slug>.md`.
- The `journals/` directory (curated journal) was active through June 30; current
  sessions write to `.agent/journal/` only.

---

## 8. Documentation landscape

Notes live in five places (consolidation recommended):

| Location | What lives there | Last active |
|---|---|---|
| `.agent/journal/YYYY-MM-DD/` | Raw agent session notes (append-only) | Active |
| `operational_notes/MM-YY/DD/` | Durable method/decision notes | Active |
| `journals/2026-06/` | Curated daily journal | Stopped 2026-06-30 |
| `work_products/*/README.md` | Per-product provenance notes | Active |
| `reports/` | Final analysis packages | Active |

**Recommendation**: treat `journals/2026-06/` as a read-only archive; no new entries.
All new session notes → `.agent/journal/YYYY-MM-DD/`. All durable method notes →
`operational_notes/MM-YY/DD/` (e.g., July 6, 2026 = `operational_notes/07-26/06/`).

---

## 9. File output conventions — must match Codex

Claude and Codex share the same repo. Every output artifact must follow the same
structure so either agent can pick up the other's work without ambiguity.

### 9.1 Status files (`.agent/status/`)

File name: `YYYY-MM-DD_AGENT-NNN.md`

Required heading format (match Codex exactly):

```markdown
# AGENT-NNN Status

Date: `YYYY-MM-DD`
Role: Coordinator / Implementer / Writer
Owner: claude

## Scope
<what this task is doing>

## Completed
- Bullet list of what was done

## Current State
<state at end of session>

## Follow-up
<what comes next>
```

Do NOT use ad-hoc sections like `## Done`, `## Done (continued)`, or task-ID
section headers. Do NOT omit the `Role:` field.

### 9.2 Journal entries (`.agent/journal/YYYY-MM-DD/`)

File name: `role-slug.md` (e.g., `coordinator-implementer-friction-closures.md`).
Task-named files (`T1-mesh-centerlines.md`) are also acceptable when the T-number
is unambiguous.

Each entry MUST include (per `.agent/journal/README.md`):
- date, agent role, task ID
- files inspected and files changed
- commands run (exact, reproducible)
- results or observations
- incomplete lines of investigation
- next steps

### 9.3 work_products naming

Directory name: `YYYY-MM-DD_descriptive-slug` — no owner prefix.

- Correct: `work_products/2026-07-06_friction_buoyancy_correction/`
- Wrong: `work_products/2026-07-06_claude_friction_buoyancy_correction/`

The `_claude_` prefix was used in June 2026 work products and is NOT the standard
going forward. Existing June entries keep their names (changing them would break
provenance references).

### 9.4 imports JSON manifests (`imports/`)

Create `imports/YYYY-MM-DD_<slug>.json` for **every major session** that produces
new tools, reports, or work products. Per AGENTS.md: "Major intake or interpretive
passes must write or update an import manifest."

Minimum fields:

```json
{
  "manifest_id": "YYYY-MM-DD_slug",
  "owner": "claude",
  "task": "AGENT-NNN",
  "generated_at": "YYYY-MM-DD",
  "purpose": "one-line description",
  "scope": "what cases / data / scope this covers",
  "new_tools": ["tools/..."],
  "new_docs": ["operational_notes/...", "reports/.../README.md"],
  "work_products": ["work_products/..."],
  "open_questions_for_user": ["..."]
}
```

### 9.5 Report packages (`reports/YYYY-MM/YYYY-MM-DD/<package>/`)

Every report package must contain at minimum:
- `README.md` — purpose, provenance, key findings, reproduce instructions
- `summary.json` — machine-readable package metadata (generated_at, task, inputs,
  outputs, key counts/metrics, limitations)

Codex packages always include both. A `README.md`-only package is incomplete.

Minimum `summary.json` structure:

```json
{
  "generated_at": "YYYY-MM-DDTHH:MM:SS-05:00",
  "task": "AGENT-NNN",
  "inputs": {"key": "path"},
  "outputs": {"key": "path"},
  "counts": {"metric": value},
  "limitations": ["..."]
}
```

### 9.6 BOARD.md claim format

Before any work, add a row to `.agent/BOARD.md` Active table with:
- Task ID (next available AGENT-NNN)
- Role, Owner (claude)
- Scope (specific file paths — claim narrowly, per FILE_OWNERSHIP.md examples)
- Goal (what you are doing and the STATUS field which updates as work progresses)

Do NOT begin editing files without a BOARD row. The coordinator (codex or claude)
must be the one to assign the ID if work is being coordinated across sessions.
