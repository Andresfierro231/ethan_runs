# Decisions

## 2026-06-09

- Repo-level coordination lives in `.agent/` so agents launched from
  subdirectories can share the same board, ownership map, journal policy, and
  cleanup rules.
- Root `AGENTS.md` is the first instruction file every agent must read.
- `JOURNAL.md` is the curated journal. Raw append-only agent notes go under
  `.agent/journal/YYYY-MM-DD/`.
- Shared process files such as `.agent/BOARD.md` and
  `.agent/FILE_OWNERSHIP.md` require coordinator approval.
- No agent may claim broad destructive cleanup authority over `staging/`,
  `linked_cases/`, `work_products/`, `reports/`, `tmp_extract/`, or
  `jadyn_runs/` without a dry-run inventory and explicit confirmation.
- Login-node safety is mandatory. Long rendering, full-case extraction, and
  solver runtime work must be deferred to appropriate batch or compute-node
  workflows.
- High-coordination subtrees may carry short `AGENTS.override.md` files. The
  helper script should surface those automatically from the current working
  directory toward repo root.
- The Salt 2 hydraulic analysis framework is split into a major-loss layer and
  a feature-based minor-loss layer. Major-loss reporting is legwise and
  centerline-based. Minor-loss reporting is pressure-budget-first.
- The first hydraulic implementation target is
  `val_salt_test_2_coarse_mesh_laminar` only, using the late retained wall-field
  window rather than a full transient history.
- The test-section side branch is treated as its own major leg, while tee
  entry/exit and connector effects remain in the minor-loss feature budget.

## 2026-06-10

- The next Salt 2 analysis pass is promoted from a Salt 2 only hydraulic
  package into a reusable per-case framework with one shared manifest and case
  profile contract.
- The shared manifest freezes requested retained times, target `ds`, required
  fields, and sign conventions before downstream extractors run.
- The initial common profile layer supports `val_salt_test_2_coarse_mesh_laminar`
  only, but the builder and extractor interfaces now depend on a profile lookup
  rather than direct Salt 2 constants.
- The June 10 package target is
  `reports/2026-06-10_ethan_salt2_case_analysis_package/`.
- The legacy June 9 hydraulic builder remains callable as a thin wrapper around
  the shared case-analysis package builder.

## 2026-07-08

- For 3D CFD to 1D comparison, replay, and thermal-state mismatch analysis,
  agents must use realized CFD interface heat-transfer terms as the comparison
  contract. Heater input to the fluid is the heater patch
  `wallHeatFlux` integral / `heat_to_fluid_W`, not the idealized resistor
  wattage or imposed electrical duty. Cooler removal from the fluid is the CFD
  cooler `wallHeatFlux` sink magnitude / `cooler_removed_duty_W`, not the
  current idealized 1D cooler-capacity prediction.
- The idealized resistor wattage and idealized cooling-jacket model remain
  physical-system predictive targets. They must not be mixed into CFD-informed
  1D validation as if they were realized fluid heat transfer until dedicated
  heater and cooler predictive submodels pass documented held-out validation.
- Current 1D replays that impose CFD heater/cooler interface heat are
  CFD-informed thermal replays, not fully predictive simulations from electrical
  and cooling hardware settings. If this remains true in a thesis or paper
  draft, disclose it explicitly as a modeling limitation.
- Current Salt 2/3/4 CFD evidence has surface-emissivity metadata but no
  OpenFOAM `qr` radiation output term. Do not double-count radiation when using
  CFD `wallHeatFlux` comparison terms. The 1D model should still retain or add a
  radiation heat-loss capability for sensitivity studies and forward physical
  prediction, with radiation reported as a separate ledger term.

## 2026-07-13

- Any user-approved sbatch cancellation, early stop, or "ready to postprocess"
  steady-state stop must leave a dated status/journal or operational note with
  numeric final-window evidence. At minimum, record Slurm job/step ID, case path,
  final-window time bounds, mean/latest/drift/span for key mdot monitors and
  `total_Q` where available, max temperature and wall-temperature probe drift
  where available, the steady/not-steady decision, and whether the row is
  closure-fit/admission usable or only a runtime/continuation decision. If a
  case is stopped for resource scheduling despite incomplete evidence, state
  that explicitly.
- AGENT-277 and AGENT-287 supersede the stale "CFD no-radiation parity"
  assumption for Ethan Salt thermal-boundary work. The admitted Salt CFD rows
  use `rcExternalTemperature` patches with emissivity/Tsur metadata, and a
  task-scoped OF13 microcase showed that changing only `emissivity` or only
  `Tsur` changes realized `wallHeatFlux`. Current authoritative per-run values
  are in
  `work_products/2026-07/2026-07-13/2026-07-13_cfd_radiative_boundary_guidance/cfd_emissivity_by_run.csv`:
  Salt 2/3/4 each have 36 `rcExternalTemperature` patches with emissivity
  `0.95`, and `Tsur`/`Ta` of `299.19 K`, `299.79 K`, and `299.97 K`
  respectively. Agents running 1D models must not call radiation-off replay
  "CFD parity"; it is a sensitivity/diagnostic. When using CFD `wallHeatFlux`,
  do not add a separate radiation term on top because radiation is already
  inseparable in the total heat flux. For forward predictive 1D work from
  physical setup inputs, include a radiation-capable external loss model or
  explicitly label radiation disabled as a sensitivity, not as Ethan-CFD
  equivalence.
- `reports/thesis_dossier/README.md` is the living thesis and weekly-presentation
  synthesis hub. Future agents should consult it when framing external updates
  or thesis-facing claims and may update it when the story, claim ledger,
  blocker status, or research avenues materially change. It is not a mandatory
  destination for routine task closeout; normal task reporting still belongs in
  the task-specific status, journal, import manifest, package README, and topic
  map.

## 2026-07-22

- Scheduler wrappers for this Ethan/S13 workflow must not submit to
  `development`. Use the NuclearEnergy dev queue. On Lonestar6 `sinfo` reports
  the partition spelling as `NuclearEnergy-dev`; pair it with account
  `ASC23046` unless a later task-specific scheduler note supersedes this.
