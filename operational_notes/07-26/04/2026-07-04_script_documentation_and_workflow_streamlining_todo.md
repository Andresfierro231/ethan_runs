# TODO — Script Documentation and Analysis Workflow Streamlining

Date: `2026-07-04`
Role: Coordinator / Writer
Task ID: `AGENT-174`

## Why this note exists

The repo now has many useful analysis, extraction, convergence, launch, backup,
and publication scripts. Several are well documented individually, but the
knowledge is distributed across script docstrings, dated journals, operational
notes, reports, status files, and Slurm logs. That makes it too easy to miss the
right tool or to repeat manual glue steps when deciding what to run next.

Create a future documentation and workflow pass that makes the scripts easy to
discover, easy to run safely, and easy to compose into repeatable analysis
pipelines.

## Desired end state

- Every maintained script has clear usage documentation in the script itself:
  purpose, inputs, outputs, environment requirements, expected runtime class,
  destructive/non-destructive behavior, and one or more tested examples.
- A repo-level script inventory exists, grouped by workflow:
  intake/registration, OpenFOAM runtime, convergence triage, extraction,
  closure derivation, ROM comparison, report packaging, backup/publish, and
  cleanup.
- Canonical workflows have one-page runbooks that say which scripts to run, in
  what order, with what prerequisites and trust gates.
- Repeated manual workflows get lightweight wrappers where appropriate, especially
  when the current procedure requires mapping scheduler jobs to case directories,
  running multiple read-only analyses, then summarizing a decision.
- Documentation distinguishes login-node-safe checks from compute-node or Slurm
  work.
- Generated artifacts remain reproducible from scripts rather than hand-edited.

## High-priority workflow candidates

1. Live CFD convergence triage:
   - Map active Slurm jobs to case directories from launcher logs.
   - Run `tools/analyze/assess_time_convergence.py` on each case.
   - Report monitor stationarity, operating-point movement where applicable,
     heat-balance closure, latest time, and a `continue / stop / investigate`
     recommendation.
   - Replace the current ad hoc operator pattern with a reusable repo script.
     The July 4 run-status check had to glue together `squeue`, Slurm launcher
     logs, `case_config.yaml` Q ratios, nominal mdot baselines, and
     `assess_time_convergence.py` from a one-off Python snippet. That exact
     process should become a maintained command with clear help text, examples,
     tests, and documented decision rules.
   - Required script behavior:
     - discover or accept active job IDs;
     - parse packed-job stdout lines of the form `Prepared <label> from <case>`;
     - detect nominal vs Q-perturbed vs insulation-perturbed cases;
     - apply the operating-point movement gate when a perturbation exists;
     - emit both per-case and per-job recommendations;
     - preserve a machine-readable report for later citation.

2. Continuation readiness:
   - Given a case family, verify latest restart time, `postProcessing` coverage,
     convergence status, retained field availability, and known trust caveats.

3. Closure extraction pipeline:
   - Make the mesh-derived geometry, pressure, friction, thermal, and recirculation
     steps discoverable as one ordered workflow with explicit required inputs.

4. Report-package generation:
   - Identify which report builders are canonical, which are historical, and which
     outputs are safe to cite for paper or presentation use.

5. Runtime and environment reference:
   - Consolidate Python/OpenFOAM environment expectations, including which commands
     must use system Python and which require the OF13 runtime.

## Acceptance criteria for the future pass

- A durable inventory file or report exists and names each maintained script under
  `tools/`, major campaign `scripts/`, and recurring `tmp`/`jadyn_runs` launchers
  that should remain discoverable.
- Each inventory row records:
  `script`, `workflow group`, `status`, `safe location to run`, `expected runtime`,
  `inputs`, `outputs`, `environment`, `example command`, and `owner/last reviewed`.
- At least the live CFD convergence triage workflow has an operator-ready runbook
  or wrapper, because it directly supports decisions about whether running CFD jobs
  need more walltime.
- The live CFD convergence triage wrapper reproduces the July 4 manual decision
  process without requiring a custom throwaway Python snippet.
- Ambiguous or obsolete scripts are explicitly marked rather than silently left in
  the same bucket as current tools.
- The pass writes a status note and cites the inventory/runbook paths so later
  agents know where to start.

## Notes for whoever picks this up

- Preserve existing dated journals and reports as provenance; do not rewrite old
  conclusions just to make documentation cleaner.
- Prefer adding concise script help, tests, and runbooks over large prose-only
  summaries.
- Keep workflow wrappers read-only by default unless the workflow is explicitly a
  launch, staging, publish, or cleanup operation.
- Coordinate before editing shared files such as `README.md`, `.agent/BOARD.md`,
  `config/**`, or registry files.
