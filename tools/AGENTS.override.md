# Tools Override

Read this after the repo-root `AGENTS.md` when working anywhere under `tools/`.

## Scope

`tools/` contains the reusable workflow entrypoints for intake, extraction,
analysis, publishing, and OpenFOAM launch wrappers.

## Local rules

- Prefer the narrowest script edit that solves the assigned task.
- Do not refactor unrelated builders just because they share patterns.
- Treat `tools/analyze/` outputs as report-coupled; check the matching package
  README before changing assumptions or filenames.
- Treat `tools/extract/` and `tools/run_openfoam_case.sh` as runtime-sensitive.
  Do not turn them into login-node heavy workflows.
- If a tool change affects provenance, manifests, or registry semantics, update
  the assigned report, manifest, or journal entry in the same task.
- Prefer adding or adjusting helper functions over copying launch or figure
  logic into another script.

## Files to read first by area

- `tools/analyze/`: related `reports/<dated_package>/README.md`
- `tools/extract/`: `staging/AGENTS.override.md` and current render status JSON
- `tools/intake/`: `registry/case_registry.csv` and latest `imports/*.json`
- `tools/publish/`: target package README plus transfer notes in
  `operational_notes/`
