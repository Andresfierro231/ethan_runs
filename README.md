# ethan_runs

`ethan_runs/` is a heavy-data intake, preprocessing, and evidence-packaging
workspace for Ethan-provided CFD cases. It is built for scientific provenance:
every useful result should be traceable back to source case paths, import
manifests, board rows, journals, and generated work products.

This is not a small library and it is not the canonical paper repository. The
canonical cross-model publication home is usually
`../cfd-modeling-tools/cross_model_comparison`; this workspace prepares,
audits, and packages the CFD evidence that can later be published there.

## Who This Guide Is For

Use this README if you are:

- a new GitHub user trying to understand what the repository contains;
- an agent picking up a board task without chat history;
- a researcher looking for current CFD admission, blocker, or thesis evidence;
- a developer maintaining intake, extraction, analysis, publication, or agent
  tooling.

You do not need to understand the full CFD campaign before doing safe local
discovery. You do need to respect the board, provenance, and HPC rules before
editing or launching work.

## What This Repo Is

- Intake state: `imports/`, `registry/`, `config/`.
- Source/staging convenience: `staging/`, `jadyn_runs/`, `linked_cases/`.
- Reproducible helpers: `tools/agent`, `tools/analyze`, `tools/extract`,
  `tools/intake`, `tools/publish`, `tools/docs`.
- Durable generated evidence: `work_products/`, `reports/`, `figures*`.
- Coordination and state: `.agent/BOARD.md`, `.agent/STATE.md`,
  `.agent/BLOCKERS.md`, `.agent/journal/`, `.agent/status/`.
- Topic maps and handoffs: `operational_notes/`.

## What This Repo Is Not

- It is not a place to mutate native solver outputs.
- It is not a place to run heavy CFD or full postprocessing on login nodes.
- It is not a place to fit or tune predictive models from validation, holdout,
  external-test temperatures, CFD `mdot`, realized `wallHeatFlux`, or imposed
  CFD cooler duty.
- It is not self-contained without local data. Many source cases live on TACC
  filesystems or other local mounts and may not exist on a public clone.

## First Hour Walkthrough

Start from the repo root.

```bash
pwd
rg --files | head -80
sed -n '1,220p' AGENTS.md
sed -n '1,220p' operational_notes/START_HERE_FOR_AGENTS.md
python3.11 tools/agent/board_dashboard.py --limit 20
sed -n '1,180p' .agent/STATE.md
sed -n '1,180p' .agent/BLOCKERS.md
```

Check tooling without touching scientific data:

```bash
python3.11 -m pytest tools/agent
python3.11 -m unittest tools.docs.test_repo_tool_inventory
python3.11 tools/docs/build_repo_tool_inventory.py
python3.11 tools/docs/build_repo_index.py --check
```

If `pytest` is unavailable, use the standard-library path:

```bash
python3.11 -m unittest discover tools/agent
```

Before editing a task:

```bash
python3.11 tools/agent/preflight_task.py --task-id <TASK_ID>
```

Before closing a task:

```bash
python3.11 tools/agent/finish_task.py --task-id <TASK_ID>
```

## Environment Prerequisites

- Linux shell on the workspace filesystem.
- Python `3.11` for most current agent and analysis tooling.
- `rg` for fast file and text search.
- TACC/Slurm commands (`sbatch`, `squeue`, `sacct`, `srun`) only when the board
  row authorizes scheduler work.
- OpenFOAM/ParaView/PyVista only for rows that explicitly involve solver,
  postprocessing, reconstruction, rendering, or field extraction.

Do not assume external data paths, HPC modules, or solver environments exist in
a fresh clone. Read the package README and source manifests first.

## Directory Map

| Path | Purpose |
| --- | --- |
| `.agent/` | Board, ownership, status, journals, blockers, generated current state, and agent tools contract. |
| `config/` | Shared workspace and QOI configuration. Treat as coordinated shared state. |
| `imports/` | Dated provenance manifests. These explain what changed, what was read, and which mutation guardrails were preserved. |
| `registry/` | Case registry. Update only under assigned intake/registry rows. |
| `tools/` | Reusable intake, extraction, analysis, publishing, docs, and coordination helpers. |
| `work_products/` | Generated packages, usually task-scoped and reproducible from scripts. |
| `reports/` | Durable reports, thesis dossiers, and report-facing packages. |
| `operational_notes/` | Dated handoffs and living topic maps. |
| `reference/` | Shared factual references such as geometry and naming truth. |
| `jadyn_runs/` | Campaign workspaces and staged/relaunched cases. Read local instructions first. |
| `staging/` | Local staged copies and render inputs. Inspect before touching. |
| `linked_cases/` | Convenience symlinks only; never cite as provenance. |
| `figures/`, `figures_rendered/` | Generated figure outputs. Prefer regeneration over manual edits. |
| `tmp/`, `tmp_extract/`, `cache/` | Scratch or generated material. Do not broad-delete without a cleanup row and dry-run. |

## User Guide

The full guide lives in `docs/repo_user_guide/`:

- `quickstart.md`: beginner-safe first steps and commands.
- `repo_organization.md`: how the repository is organized.
- `tool_index.md`: generated inventory of every helper under `tools/`.
- `tool_inventory.csv`: machine-readable tool inventory.
- `data_and_provenance.md`: manifests, registry, native outputs, and work products.
- `agent_workflow.md`: board claiming, closeout, and handoff rules.
- `hpc_and_background_jobs.md`: Slurm, `srun`, `tmux`, and monitor-agent policy.
- `common_tasks.md`: concrete workflows for common work.
- `troubleshooting.md`: common failure modes and safe checks.
- `glossary.md`: repo and research terms.

Regenerate the tool index after adding, removing, or renaming helpers:

```bash
python3.11 tools/docs/build_repo_tool_inventory.py
```

## Current State and Blockers

Generated files are authoritative for current state:

- `.agent/STATE.md`
- `.agent/BLOCKERS.md`
- `.agent/catalog.csv`
- `.agent/catalog.json`

Regenerate/check the index only when no active row owns the generated index
files, or when your row explicitly allows it:

```bash
python3.11 tools/docs/build_repo_index.py --check
```

Open blockers currently live in `.agent/blockers.yml` and render into
`.agent/BLOCKERS.md`. Do not scatter new blocker status across journals without
updating the blocker register under an assigned row.

## Provenance Rules

- Native CFD/OpenFOAM outputs are read-only unless a board row explicitly grants
  a controlled staged-copy or postprocessing action.
- `linked_cases/` symlinks are convenience handles, not provenance.
- Every durable task should leave a status file, journal entry, import manifest,
  and package README or operational note.
- Claims should cite exact repo paths, not chat history.
- Registry/admission/source-property/scoring changes require explicit board
  scope.

## HPC and Background Compute

Use the scheduler/session tool that matches the work lifetime:

- `sbatch`: durable long-running or overnight work from a login node.
- `srun`: compute work inside an allocation.
- `tmux`: keep an interactive launcher alive; it does not allocate resources.

Never run expensive solver, rendering, full-case extraction, or convergence
work directly on a login node. Long jobs need a principal row and a monitor row:
the principal launches and documents; the monitor checks state without
submitting duplicates or harvesting unless explicitly assigned.

Get the policy checklist with:

```bash
python3.11 tools/agent/background_compute_helper.py --duration long --openfoam --persistent
```

## Primary Entrypoints

Read `tools/README.md` and `docs/repo_user_guide/tool_index.md` before running
tools. Representative entrypoints:

```bash
python3.11 tools/agent/board_dashboard.py
python3.11 tools/agent/preflight_task.py --task-id <TASK_ID>
python3.11 tools/agent/finish_task.py --task-id <TASK_ID>
python3.11 tools/intake/register_case.py --source-path <case-dir>
python3.11 tools/intake/build_import_manifest.py --source-id <source-id>
python3.11 tools/extract/extract_case_inventory.py --source-id <source-id>
python3.11 tools/extract/extract_qoi_table.py --source-id <source-id>
python3.11 tools/publish/build_cross_model_join.py --source-id <source-id>
python3.11 tools/publish/publish_cross_model_campaign.py --source-id <source-id>
python3.11 tools/run_registered_pipeline.py --source-id <source-id>
```

Many analysis builders are package-specific. Do not run them as generic
maintenance commands; open the matching board row, package README, and test
first.

## Run Classification

- Continuation runs are the current mainline Ethan run family when they exist.
- Kirst runs are historical unless a later dated note explicitly re-admits them.
- Perturbation runs belong in sensitivity or testing groups, not nominal
  baseline groups.
- Final predictive training currently spans admitted Salt1-4 nominal rows;
  holdout/testing comes from perturbation, external, and new-CFD rows after
  their own admission gates.

## Safe Local Discovery Commands

Read-only:

```bash
pwd
rg --files
rg -n "TODO-REPO-USER-GUIDE" .agent/BOARD.md
sed -n '1,160p' .agent/BLOCKERS.md
python3.11 tools/agent/board_dashboard.py --limit 20
python3.11 tools/docs/build_repo_index.py --check
```

Mutating or potentially heavy, only under assigned scope:

```bash
sbatch <script.sbatch>
srun -N1 <command>
python3.11 tools/intake/register_case.py --source-path <case-dir>
python3.11 tools/extract/render_field_figures.py --source-id <source-id> --backend auto
python3.11 tools/run_registered_pipeline.py --source-id <source-id>
```

## Keeping This Guide Current

When a workflow changes, update the nearest guide page and regenerate
`docs/repo_user_guide/tool_index.md` with
`tools/docs/build_repo_tool_inventory.py`. For significant documentation
sessions, close out with a status, journal, import manifest, and
`finish_task.py`, then regenerate the repo index only if the active board scope
allows generated index edits.
