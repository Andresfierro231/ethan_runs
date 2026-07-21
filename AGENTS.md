# AGENTS.md

Reviewed: `2026-06-30T00:00:00-05:00`

## Workspace role

`ethan_runs/` is the heavy-data intake and preprocessing workspace for
Ethan-provided CFD cases that later publish durable summaries into
`../cfd-modeling-tools/cross_model_comparison`.

This repo is not a generic software project. It combines:

- intake and registration state in `imports/`, `registry/`, and `config/`
- analysis and publication scripts in `tools/`
- staged case trees in `staging/` and campaign workspaces in `jadyn_runs/`
- generated figures and extracted artifacts in `figures*`, `work_products/`,
  `tmp_extract/`, and `reports/`
- research context in `journals/`, `operational_notes/`, and report markdown

## Required startup protocol

Any agent launched from the repo root or any subfolder must do this first:

1. Locate the repo root.
2. Read this root `AGENTS.md`.
3. Read `.agent/BOARD.md`, `.agent/FILE_OWNERSHIP.md`, and `.agent/ROLES.md`.
4. Read relevant local instructions for the subtree being touched.
   Read any nearest `AGENTS.override.md` first, then the nearest `README.md`,
   `TODO.md`, campaign dossier, or report package README in `jadyn_runs/`,
   `reports/`, `operational_notes/`, `staging/`, or `tools/`.
5. Identify a role before editing:
   `Coordinator`, `Implementer`, `Tester`, `Reviewer`, `Writer`, or `Cleaner`.
6. Confirm a task ID and allowed edit paths on `.agent/BOARD.md`.
7. Refuse unassigned work or edits that overlap another active agent's files.

Use `.agent/scripts/agent_context.sh` when starting from a subdirectory.

## Research avenue continuity protocol

Claude and Codex agents must use this same protocol when opening a clearly new
research avenue: a new modeling question, source family, closure path,
campaign, validation split, predictive mode, or literature-derived line of
work.

1. Create or claim a `.agent/BOARD.md` row before editing. The row must name
   the task ID, role, owner, allowed edit paths, required read-only context,
   native-output guardrails, objective, acceptance signal, and current status.
2. Write a dated start-here or handoff note under `operational_notes/` or the
   package `README.md`. It must include: why this avenue exists, files to open
   first, trusted packages, unresolved blockers, active board rows, next task
   sequence, output contract, and do-not-do guardrails.
3. Cross-link the new note from the nearest current start-here document or
   package README so the chain of work is findable without reading chat logs.
4. Preserve provenance by author/title for literature ideas and by exact file
   path for repo evidence. Do not rely on citation numbers that may change.
5. End the work with a status file, dated journal entry, and import manifest
   when the task creates or updates a research artifact.

## Non-negotiable rules

- Never mutate native solver outputs in imported source directories.
- Treat `linked_cases/` symlinks as local convenience only, not provenance.
- Record exact source paths in manifests and published artifacts.
- Require local staging before analysis when a source originates on another
  machine or unavailable mount.
- Do not work on unassigned tasks.
- Do not edit files owned by another active agent.
- Keep changes small and reviewable.
- Update a status file, raw journal entry, or handoff at the end of work.
- Never run long or expensive jobs on login nodes.
- Ask before destructive cleanup, deletion, force-overwrite, or irreversible
  actions.

## Full documentation contract

Every agent must leave enough durable context for another agent or new user to
continue without reading chat logs. Before marking a task complete or blocked,
write or update:

- `.agent/status/<date>_<TASK>.md` with objective/outcome, changed artifacts,
  validation commands/results, unresolved blockers, and explicit guardrails
  such as native-output, registry, scheduler, and external-repo mutation status.
- `.agent/journal/<date>/<slug>.md` with what was attempted, what was observed,
  what was inferred, contradictions or caveats, and next useful actions.
- `imports/<date>_<slug>.json` with changed files, read-only context, and
  mutation/provenance flags.
- a package `README.md` or dated operational note whenever the work produces or
  changes durable research context, policies, tools, reports, or handoff
  instructions.

Use `python3.11 tools/agent/finish_task.py --task-id <TASK>` before closeout.
The validator is intentionally strict about documentation shape so incomplete
handoffs are found while the context is still fresh.

## Background compute-agent policy

Use the scheduler/session tool that matches the lifetime of the work:

- Use `sbatch` from a login node for durable long-running or overnight work that
  must survive the current shell.
- Use `srun` for compute work inside an allocation, especially OpenFOAM or
  postprocessing steps that need Slurm accounting.
- Use `tmux` only to keep an interactive compute-node launcher/session alive.
  `tmux` does not allocate resources; if it owns an `srun --jobid=...`
  launcher, killing the tmux session or the interactive allocation can kill the
  attached step.
- Do not use plain detached background processes for critical solver or
  admission work unless the task is tiny, non-critical, and fully logged.
- Every background handoff must record task ID, job/step ID if any, node, exact
  command, log path, expected completion/cleanup condition, and whether killing
  a tmux session or allocation is safe.

Use a principal-agent plus monitor-agent pattern for long or convergence-driven
work:

- The principal agent owns the scientific task, prepares the command, writes the
  `RUNNING.md`/README handoff, launches the `sbatch`, `srun`, or `tmux+srun`
  job, and then returns to normal user coordination instead of blocking the
  conversation for the whole run.
- A separate monitor agent should claim a narrow read-only board row for long
  jobs. The monitor checks `squeue`, `sacct`, process state, log growth, and
  expected output files; it does not submit duplicate jobs or harvest/admit
  results unless a later row explicitly grants that authority.
- The user must be able to keep communicating with the principal agent while
  the background terminal or compute job runs. Do not make the main agent sit
  idle in a long foreground watch loop when the work can be handed to a monitor
  row.
- Monitor handoffs must state when to report progress, when to leave a job
  running, what terminal states matter, and what action is forbidden without a
  new board row.

## Repo-specific operating rules

- Major intake or interpretive passes must write or update:
  - an import manifest in `imports/`
  - a case registry entry in `registry/case_registry.csv` when scope changes
  - a dated journal entry
  - a checkpoint or TODO when unresolved work remains
- `cross_model_comparison/` remains the canonical publication home for
  cross-model comparison campaigns, journals, and provenance indices.
- Treat continuation runs as the current mainline Ethan run family whenever a
  continuation exists for a case. Main documentation should surface the
  continuation artifact first, not the superseded parent warmup or other
  exploratory variants.
- Do not use Kirst runs as current mainline evidence or default comparison
  inputs. Keep them only as historical provenance unless a later dated note
  explicitly re-admits them.
- Keep perturbation runs in their own clearly labeled sensitivity /
  correlation-support group. They may inform correlations and trend checks,
  but they must not be classified as main runs or nominal baseline runs.
- Prefer coordination files, helper scripts, and dated markdown over ad hoc
  scratch notes.
- Prefer reproducible scripts over manual artifact edits for `reports/`,
  `figures/`, `figures_rendered/`, and `work_products/`.
- Treat `staging/`, `tmp_extract/`, `cache/`, and generated figure trees as
  potentially large and sensitive. Inspect first. Do not broad-delete.

## Writing rules

- Use dated filenames when practical.
- Separate observed output, inferred interpretation, contradictions, and next
  suggested actions.
- Preserve abandoned or incomplete lines of investigation instead of silently
  dropping them.
- Cite source files, scripts, journals, reports, or figures for claims.
- Keep machine-local artifacts reproducible from scripts wherever possible.

## Documentation continuity and index protocol

Claude and Codex work as **teammates on one shared documentation corpus**. There
is no per-document owner; any teammate may extend or correct any doc. (The
`.agent/BOARD.md` Owner column is only a live conflict-avoidance lock on an
active task, not authorship.)

- **Frontmatter.** New durable docs (status, journal, operational note, report
  README, work_product README) should carry the YAML frontmatter defined in
  `.agent/DOC_FRONTMATTER_SCHEMA.md`. Fill the priority core first — **provenance,
  tags, related** — even if you skip the rest. These are what make past material
  findable and reports assemble-able.
- **Blockers live in one register.** Add/curate `.agent/blockers.yml`; do not
  scatter blocker status across journals. When a finding overturns an earlier
  one, set the earlier doc's `status: superseded` and record `superseded_by`.
- **Regenerate the index at the end of any significant session:**
  `python3 tools/docs/build_repo_index.py` (writes `.agent/STATE.md`,
  `catalog.json/csv`, `BLOCKERS.md`). Run `--check` to validate the blocker
  register. `.agent/STATE.md` and `.agent/BLOCKERS.md` are generated and
  authoritative for "current state"; if a prose summary disagrees, trust the
  generated file.
- **Topic maps.** `operational_notes/maps/` holds one living map-of-content hub
  per research thread. Start there when picking up a topic; update the relevant
  hub when your thread produces a durable result.
