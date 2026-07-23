# File Ownership

Updated: `2026-06-09`

## Active ownership rules

- No agent may edit paths claimed by another active task on `.agent/BOARD.md`.
- When a task needs a new path, the coordinator updates the board first.
- Shared files listed below require coordinator approval even for small edits.
- Prefer task-scoped path claims such as one report package or one campaign
  subtree instead of broad repo-wide claims.

## Shared files requiring coordinator approval

- `AGENTS.md`
- `*/AGENTS.override.md`
- `JOURNAL.md`
- `.agent/BOARD.md`
- `.agent/BOARD_ARCHIVE.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `.agent/DECISIONS.md`
- `.agent/JOURNAL_POLICY.md`
- `.agent/CLEANUP_POLICY.md`
- `registry/case_registry.csv`
- `config/workspace_paths.yaml`
- `config/qoi_definitions.yaml`

## Path ownership map

| Path pattern | Default owner | Notes |
| --- | --- | --- |
| `.agent/**` | Coordinator | Shared coordination state. Other roles may add status, journal, handoff, cleanup, or lock entries only for their assigned task. |
| `.agent/BOARD_ARCHIVE.md` | Coordinator | Historical board rows. Do not edit manually except for emergency conflict repair; use `tools/agent/board_archive.py`. |
| `*/AGENTS.override.md` | Coordinator or assigned Implementer | Local instruction files must stay short and reflect real subtree workflow, not generic restatements. |
| `journals/**` | Writer | Historical curated research log. Do not rewrite existing entries casually. |
| `operational_notes/**` | Writer or Coordinator | Use for dated planning and checkpoints. Preserve contradictory or incomplete lines of investigation. |
| `reports/<dated_package>/**` | Writer or assigned Implementer | Claim one package subtree at a time. `README.md`, `summary.json`, figures, and analysis notes in a package should be treated as a unit unless the coordinator splits ownership. |
| `reports/**/README.md` | Writer | These files carry interpretive context and provenance, not just packaging. |
| `reports/**/scientific_writeup_notes.md` | Writer | Research prose with evidence requirements. |
| `reports/**/scientific_numerical_analysis.md` | Writer | Interpretive analysis. Requires source citations. |
| `reports/**/figures/**` | Implementer or Cleaner | Generated outputs. Prefer regeneration over manual edits. |
| `tools/analyze/**` | Implementer | Analysis code. Avoid mixing multiple report scopes in one task. |
| `tools/extract/**` | Implementer | Extraction and rendering helpers. Be careful around heavy case reads. |
| `tools/intake/**` | Implementer | Intake and manifest tooling. Coordinate with registry/manifests. |
| `tools/publish/**` | Implementer | Publication packaging and transfer helpers. |
| `tools/run_registered_pipeline.py` | Implementer | Shared pipeline entrypoint. High coordination risk. |
| `tools/run_openfoam_case.sh` | Implementer | Do not convert this into a long-running login-node workflow. |
| `imports/**` | Implementer or Writer | Manifests are provenance artifacts. Use dated filenames only. |
| `registry/**` | Coordinator or assigned Implementer | Registry updates affect global state. |
| `config/**` | Coordinator or assigned Implementer | Shared workflow definitions. |
| `jadyn_runs/**/README.md` | Writer or Coordinator | Campaign context and staged-run instructions. |
| `jadyn_runs/**/TODO.md` | Coordinator or Writer | Durable unresolved-work notes. |
| `jadyn_runs/**/scripts/**` | Implementer | Lightweight helper scripts only. Avoid touching case content unless the task is specifically about staging metadata. |
| `jadyn_runs/**/case_stage/**` | Implementer with explicit assignment | Treat as staged run material. Do not broad-edit. |
| `staging/**` | Implementer with explicit assignment | Contains local staged copies and render inputs. Never treat as disposable by default. |
| `linked_cases/**` | No edits | Convenience symlinks only. Do not use for provenance and do not edit targets. |
| `work_products/**` | Implementer or Cleaner | Generated extraction artifacts. Prefer scripted regeneration. |
| `figures/**`, `figures_rendered/**` | Implementer or Cleaner | Generated figures and status JSON. Avoid manual pixel edits. |
| `cache/**`, `tmp/**`, `tmp_extract/**` | Cleaner or assigned Implementer | High cleanup candidate areas. Dry-run first. |

## Claim patterns

- Good claim: `reports/2026-06-05_ethan_continuation_diagnosis/**`
- Good claim: `tools/analyze/build_ethan_continuation_diagnosis.py`
- Good claim: `.agent/journal/2026-06-09/writer-salt-summary.md`
- Bad claim: `reports/**`
- Bad claim: `tools/**`
- Bad claim: `staging/**` without a specific campaign or case
