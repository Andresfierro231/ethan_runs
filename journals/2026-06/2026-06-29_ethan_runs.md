# 2026-06-29 Ethan Runs

## Codex Agent Handoff

You are taking over the next phase of post-processing for the Ethan 3D CFD
campaign with the explicit goal of strengthening the ATH paper honestly and
with scientific rigor.

Do not optimize for a prettier validation plot. Optimize for defensible
evidence, reproducible reductions, and a clear separation between:

- observed CFD evidence
- support-limited interpretation
- residual-only or still-blocked physics

## Working Locations

- Primary 3D CFD campaign roots: `../../ethan*/`
  - current local match: `../../ethan_runs`
- Primary 1D model location: `../../cfd*/tamu*/Fluid`
  - current local match:
    `../../cfd-modeling-tools/tamu_first_order_model/Fluid`
- Cross-model and comparison workflows: `../../cfd*/cross*/`
  - current local match:
    `../../cfd-modeling-tools/cross_model_comparison/`
- Paper notes that motivated this queue:
  `../../papers/ath26_paper/vision.tex`

## Mission

Build the next post-processing wave needed to turn the paper's current
trust-region claims into a stronger, reproducible evidence base without
smuggling unsupported physics into the 1D model.

## Non-Negotiable Rules

- Keep unsupported right-leg, cooler-vicinity, and feature-level physics
  explicit until the reduction evidence is strong enough to defend promotion.
- Do not promote a closure just because it improves 1D parity.
- If a closure candidate fails the support gate, document why and leave it
  blocked or residual-only.
- Keep provenance for every derived table, figure, and reduced dataset.
- Prefer one bounded analysis lane at a time over reopening the whole campaign.

## Priority Queue

### 1. Build a paper-grade case inventory

- Make or refresh a manifest that maps every Salt case used by the paper to:
  CFD case name, property mode, geometry version, mesh, solver settings,
  convergence status, retained-time status, and reduction script version.
- Mark each case as one of:
  `paper-grade`, `exploratory`, `blocked`, or `exclude`.
- Record which reduced products and which 1D model branch were used for every
  current paper-facing plot or summary.
- Freeze a paper subset so later analyses do not mix incompatible cases.

### 2. Audit the 3D-to-1D reduction contract

- Write down the exact station map and branch map used for loop reductions.
- Re-run or verify extraction of:
  bulk temperature, wall temperature, wall heat flux, pressure gradient,
  apparent friction, HTC, Nu, UA', and branchwise heat partition.
- Audit the reduction choices that can move closure conclusions:
  area averaging, wall patch selection, axial smoothing, pressure differencing,
  entrance-location references, and coordinate unwrap logic.
- Save reduced outputs in a versioned, paper-facing package.

### 3. Quantify the upcomer recirculation story

- Pull the strongest retained-time evidence for upcomer recirculation and
  profile distortion from the Ethan campaign.
- Turn that into quantitative descriptors rather than narrative only:
  reversed-flow fraction, skewness, recirculation extent, off-axis peak
  location, wall-flux redistribution, or another defensible metric.
- Test whether recirculation severity correlates more cleanly with:
  `Re`, `Gr/Re^2`, heater power, cooling condition, mean upcomer temperature,
  or heater-to-cooler bulk temperature span.
- Produce one paper-safe figure candidate that contrasts textbook
  fully-developed expectations against the observed CFD field.

### 4. Expand hydraulic closure support

- Re-check the current defended straight friction lane and its true support
  interval.
- Extract right-leg and cooler-return hydraulic evidence branch by branch.
- Evaluate whether any feature-level `K_eff` terms can be defended with
  acceptable integral consistency.
- Test whether the full-loop pressure budget closes after reduction. If it does
  not, isolate whether the problem is reduction methodology, solver maturity,
  property handling, or real unsupported feature physics.

### 5. Expand thermal closure support

- Finish the right-leg thermal closure audit.
- Separate passive ambient loss from active cooler removal more cleanly.
- Re-evaluate which branches truly support direct `Nu(Re)` promotion and which
  only support `UA'` as the primary transfer surface.
- Compare branchwise thermal trends across promoted versus legacy property
  bundles to check whether apparent closure support is property-artifact-driven.

### 6. Make the cooler / HX region a first-class evidence product

- Isolate the cooler-region reduction logic in a dedicated notebook, script, or
  report package.
- Determine whether the cooler should enter the ROM as:
  imposed `q'`, a `UA'` surface, a mixed empirical-CFD submodel, or a bounded
  residual plus narrow defended component.
- Quantify how much current wall-temperature mismatch is driven by cooler
  placement and allocation rather than bulk-flow error.
- Check whether cooler-vicinity transport contaminates neighboring branch
  averages enough that the region needs a split before 1D transfer.

### 7. Formalize the closure gate

- Write the actual promotion rules in one place:
  support fraction threshold, monotonicity expectations, sign checks, minimum
  Reynolds window width, branch exclusions, and fallback behavior.
- For each closure family, label it:
  `defended`, `support-gated`, `diagnostic-only`, `residual-only`, or
  `blocked`.
- Keep failure examples. Those are part of the scientific record.

### 8. Turn 1D validation into a real test matrix

- Split cases into:
  closure-identification, calibration, and withheld validation sets.
- Do not reuse the same cases for every stage and still describe the result as
  predictive validation.
- Track more than mass-flow parity:
  thermocouple RMSE, branchwise wall-temperature error, energy residual,
  circulation bias, and trust-region membership.
- Explicitly log cases where mass flow improves while wall temperatures worsen.
  Interpret those as closure-allocation warnings.

### 9. Add uncertainty accounting

- Propagate uncertainty from:
  salt properties, ambient loss, cooler power, sensors, CFD reduction choices,
  and fitted closure coefficients.
- Separate robust topological conclusions from fragile coefficient-level ones.
- If a near-promoted closure has wide uncertainty, keep it support-gated.

### 10. Repair paper-facing evidence gaps

- Replace vague "transport topology" language with quantities actually defined
  by the reduced data.
- Assemble the operating-envelope ranges used by the promoted Salt subset:
  `Re`, `Pr`, `Pe`, `Gz`, heater power, cooling condition, and useful
  wall-to-bulk `Delta T` measures.
- Add a concise explanation for why better mass-flow agreement can coexist with
  poor wall-temperature agreement.
- Prepare figure inputs that make the closure-allocation problem visible rather
  than only described.

## Required Deliverables

Produce the following, not just a verbal update:

- a dated case inventory table
- a dated open-questions / blocked-closures table
- a dated closure-status table by branch and closure family
- at least one reproducible reduced-data package for the paper subset
- at least one figure-ready artifact for the upcomer recirculation story
- a short ranked next-actions note for the following agent

## Suggested Output Locations

- journal summary:
  `../../ethan_runs/journals/2026-06/`
- agent handoff notes:
  `../../ethan_runs/.agent/journal/2026-06-29/`
- report or evidence package:
  `../../ethan_runs/reports/2026-06/2026-06-29/`
- machine-readable tables:
  `../../ethan_runs/work_products/`

## Stop Conditions

Stop and document the blocker if any of the following happens:

- the reduction contract cannot be reconstructed from existing scripts
- case provenance is too weak to defend the paper subset
- a promoted closure depends on undocumented manual filtering
- retained-time evidence is too immature for the intended claim

## Final Standard

Leave the next agent with a sharper evidence boundary than the one you found.
If the honest answer is that some closure remains unsupported, say that
plainly and preserve the residual bucket.

## Coordination Reset

### Observed Output

- Reorganized the live board into five June 29 research tracks in
  `.agent/BOARD.md`:
  - Track A: ROM / latest-window / presentation
  - Track B: CFD jobs / campaign operations
  - Track C: postprocessing / hydro summaries
  - Track D: additive paper-evidence wave
  - Track E: cleanup / commit curation
- Added one new coordinator task (`AGENT-146`) plus four unclaimed additive
  June 29 tasks (`AGENT-147` through `AGENT-150`) with disjoint script,
  report, work-product, status, and raw-note scopes.
- Recorded an explicit June 29 note-collision rule on the board:
  one task claim gets one raw note file under `.agent/journal/2026-06-29/`,
  and only the coordinator updates this curated journal.

### Sources Used For The Open TODO Reset

- `.agent/BOARD.md`
- `operational_notes/06-26/26/2026-06-26_rom_modeling_validation_checkpoint.md`
- `operational_notes/06-26/25/2026-06-25_progress_checkpoint.md`
- `operational_notes/06-26/25/2026-06-25_postprocessing_registry_checkpoint.md`
- `reports/2026-06/2026-06-26/2026-06-26_ethan_progressive_story_synthesis/open_analysis_queue.md`
- `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/TODO.md`
- `jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/TODO.md`
- `journals/2026-06/2026-06-25_ethan_runs.md`
- `journals/2026-06/2026-06-26_ethan_runs.md`

### Open TODO By Track

#### Track A: ROM / Latest-Window / Presentation

- Let the current latest-window refresh finish decisively, then republish the
  latest-window frozen-state package with `--skip-case-refresh`
  (`2026-06-26_rom_modeling_validation_checkpoint.md`).
- Run latest-window local validation with the June 26 closure bundle.
- Run latest-window local bakeoff with the June 26 closure bundle.
- Run the latest-window discrepancy explainer.
- Write the bundle-to-ROM variable mapping and keep direct downcomer / feature
  closures blocked unless the evidence truly expands.
- Do not claim a refreshed readable ROM validation surface until either:
  - a reproducible external `Fluid` producer exists, or
  - a versioned `v2` static bundle is published.
- Keep the presentation lane bounded to current defended evidence only:
  slide-ready 1D section, Salt 1-4 metric cards, and explicit heater-normalized
  energy-error definitions.

## Codex Relay Plan: AGENT-102, AGENT-150, AGENT-149

This section is a bounded relay note for another Codex instance. It is not a
claim by itself. The next instance should still follow the repo startup
protocol, claim only one task at a time, and stay inside the owned paths on
`.agent/BOARD.md`.

### Shared startup reads

Read these first before claiming any of the three tasks:

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `.agent/status/2026-06-29_AGENT-146.md`
- `.agent/journal/2026-06-29/coordinator-writer-board-track-reorg.md`
- `journals/2026-06/2026-06-29_ethan_runs.md`
- `reports/2026-06/2026-06-26/2026-06-26_ethan_progressive_story_synthesis/open_analysis_queue.md`

Also note the live overnight latest-window chain already queued on
`2026-06-29`:

- `3265733` `lw_s234_full`
- `3265734` `lw_finalize`
- `3265893` `lw_promote`
- `3265895` `lw_1d_val`
- `3265894` `lw_bakeoff`
- `3265896` `lw_discrep`

Those jobs matter because tomorrow's local Salt interpretation surface will
change once the latest-window validation / bakeoff / discrepancy packages land.

### AGENT-102 relay plan

Claim only if you intend to work in both this repo and the sibling `Fluid`
repo scope listed on `.agent/BOARD.md`.

Read next:

- `.agent/status/2026-06-22_AGENT-102.md`
- `.agent/journal/2026-06-29/track-a_AGENT-102_v2-refresh-and-replay.md`
- `tools/analyze/build_ethan_fluid_replay_against_frozen_state.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/README.md`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/run_resumable.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/run_local_segmented_campaign.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/ethan_cfd_informed_salt_v2/scenario_plan.csv`

Current verified state as of `2026-06-29`:

- The external replay root exists at
  `../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/ethan_cfd_informed_salt_v2`.
- That root is prepared but not finalized:
  `campaign_metadata.json`, `resolved_run_manifest.json`, `scenario_plan.csv`,
  and `runtime/prepare_stage.json` exist, but `run_manifest.csv` does not.
- Scenario manifests currently exist for indices `0`, `2`, `3`, `4`, and `5`.
- The only missing shard is scenario index `1`:
  `ethan_cfd_informed_salt_v2_hybrid_ins_1.0in_rad_0`.
- The partial scenario-1 root currently only shows `Salt_1/`, so this looks
  like an interrupted or incomplete solve-scenario lane, not a finished run.

Planned execution:

1. Inspect the scenario-1 root and any existing logs under the external output
   root to determine whether it failed before or during the case sequence.
2. Re-run only the missing shard with the tracked resumable split path, using
   the existing output root:
   `python -m tamu_loop_model_v2.run_resumable --campaign ethan_cfd_informed_salt_v2 --output-root results/diagnostics/ethan_cfd_informed_salt_v2 --output-label ethan-cfd-informed-salt-v2 --stage solve-scenario --scenario-index 1`
3. If single-shard rerun is unstable or too slow, switch to a segmented local
   or array-style relaunch, but still only for the missing shard.
4. After scenario `1` writes its manifest, run the `finalize` stage on the
   same root to create `run_manifest.csv` and rebuilt analysis tables.
5. Only after that, regenerate the local replay package from
   `tools/analyze/build_ethan_fluid_replay_against_frozen_state.py`.

Stop conditions:

- If scenario `1` fails again for a substantive model/config reason, stop and
  write the exact failure into the AGENT-102 raw note before attempting a
  broader relaunch.
- Do not rerun the whole six-scenario campaign unless the prepared root is
  proven inconsistent.

### AGENT-150 relay plan

This is the cleanest additive paper-facing task. It does not need new compute
or shared-code edits outside its owned report/import/work-product paths.

Read next:

- `.agent/BOARD.md` entry for `AGENT-150`
- `reports/2026-06/2026-06-26/2026-06-26_ethan_progressive_story_synthesis/open_analysis_queue.md`
- `.agent/status/2026-06-23_AGENT-121.md`
- `.agent/status/2026-06-23_AGENT-122.md`
- `.agent/status/2026-06-23_AGENT-123.md`
- `reports/2026-06/2026-06-29/2026-06-29_ethan_paper_case_inventory/README.md`
- `reports/2026-06/2026-06-29/2026-06-29_ethan_reduction_contract_audit/README.md`
- `work_products/2026-06-29_ethan_reduction_contract_audit/reduction_choice_audit.csv`
- `work_products/2026-06-29_ethan_reduction_contract_audit/branch_map.csv`

Current context:

- `AGENT-147` already froze the current paper subset:
  `paper-grade = Salt 1-4 Jin`,
  `exploratory = Salt 2 Kirst`,
  `blocked = Salt 1 Kirst + Salt 2 Val`,
  `exclude = Salt 3 Kirst + Salt 4 Kirst`.
- `AGENT-148` already published the paper-facing reduction contract tables.
- The latest-window local validation / bakeoff / discrepancy chain is queued
  overnight, so a closure-status package written tonight should explicitly say
  whether it is based on the current June 22 local stack, the June 29 additive
  audit stack, or the post-overnight refreshed latest-window stack.

Planned execution:

1. Claim `AGENT-150` and create the missing owned status/raw-note files.
2. Build one dated machine-readable closure-status table by branch and closure
   family using the queue plus the current closure/frozen checkpoints.
3. Label each lane as one of:
   `defended`, `support-gated`, `diagnostic-only`, `residual-only`, `blocked`.
4. For every non-defended lane, preserve at least one concrete failure example
   and the missing observable or support gap that prevents promotion.
5. Publish a dated README, import manifest, and work-product tables inside the
   AGENT-150 scope only.

Strong recommendation:

- Start this before AGENT-149 if only one additive task can be claimed first.
  It is lower-risk, compute-free, and sharpens tomorrow's interpretation
  boundary.

### AGENT-149 relay plan

This is the next quantitative additive lane and is better grounded now that
`AGENT-148` exists.

Read next:

- `.agent/BOARD.md` entry for `AGENT-149`
- `reports/2026-06/2026-06-29/2026-06-29_ethan_paper_case_inventory/README.md`
- `reports/2026-06/2026-06-29/2026-06-29_ethan_reduction_contract_audit/README.md`
- `work_products/2026-06-29_ethan_reduction_contract_audit/station_map.csv`
- `work_products/2026-06-29_ethan_reduction_contract_audit/branch_map.csv`
- `work_products/2026-06-29_ethan_reduction_contract_audit/paper_reduced_branch_summary.csv`
- any currently relevant branch / heat-loss / transport package roots named in
  the reduction audit README

Current context:

- This task should reuse existing reduced outputs first; it should not reopen a
  fresh heavy extraction wave unless the reused package roots are proven
  insufficient.
- The reduction audit currently uses mixed provenance intentionally:
  `Salt 1 Jin` points at the latest-window refresh root in progress, while
  `Salt 2-4 Jin` still point at June 15 reduced package roots.
- That mixed provenance is acceptable for a first evidence package if it is
  stated plainly in the report and machine-readable outputs.

Planned execution:

1. Claim `AGENT-149` and create the missing owned status/raw-note files.
2. Use the frozen paper-grade Salt subset plus the station/branch mappings from
   `AGENT-148` to derive upcomer-versus-return-leg evidence from existing
   reduced outputs.
3. Prefer defensible retained-time metrics such as support fraction, branchwise
   temperature contrast, wall-to-bulk contrast, directional asymmetry, or other
   clearly reproducible descriptors over purely narrative claims.
4. Publish at least one figure-ready artifact that contrasts textbook
   expectations with the observed CFD pattern.
5. Keep provisional station assumptions or mixed-provenance limitations
   explicit rather than smoothing them away in prose.

Strong recommendation:

- Do this after `AGENT-150` unless the paper team specifically needs a figure
  candidate before the closure-status gate.

### Recommended claim order for another Codex instance

1. `AGENT-150`
2. `AGENT-149`
3. `AGENT-102` as the separate sibling-repo intervention lane

If two Codex instances are available, the safest split is:

- one instance claims `AGENT-150`
- one instance claims `AGENT-102`

Then start `AGENT-149` after `AGENT-150` or once the next paper-facing gap is
clearer from the overnight latest-window outputs.

#### Track B: CFD Jobs / Campaign Operations / Backup

- Check the June 25/26 continuation and recirculation-boundary jobs before
  doing science interpretation:
  confirm scheduler state, startup success, and whether the active `120 h`
  `NuclearEnergy` packs will need another continuation chain before timeout
  (`2026-06-26_ethan_runs.md`).
- Build a short run-status snapshot for the recirculation-boundary wave before
  any heavier analysis is launched.
- Finalize the June 23 temporary Salt checkpoint copy and finish the remaining
  June 18 campaign TODO bookkeeping:
  import/status/journal updates, day-1/day-2/day-3 health checks, and the
  parent heat-ledger prerequisite for any fixed-`Q` DOE child work
  (`2026-06-18_convergence_and_jin_envelope_wave/TODO.md`).
- Finish the June 19 blocker-wave follow-ons that are still open:
  readable cooler-side mutation path, next Salt follow-on design centered on
  heater/cooler boundary behavior and recirculation onset, balanced-node
  runtime/memory review, and cleanup/archive of the abandoned
  `runs/salt2_jin_hiq_balq/` scratch copy
  (`2026-06-19_ethan_blocker_and_1d_followon_wave/TODO.md`).
- Check backup job `3259614`, inspect logs, inspect the manifest outputs if
  complete, and decide whether a second incremental pass or checksum dry-run is
  needed (`2026-06-25_progress_checkpoint.md`).
- Treat `jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/TODO.md`
  as stale until it is reconciled with the June 25-26 journals; the journal
  trail shows the submissions and repack already happened.

#### Track C: Postprocessing / Hydro Summaries

- Review the single flagged `mdot` discrepancy case
  `val_water_test_4_coarse_mesh_laminar` and decide whether the tolerance
  should remain `1e-6 kg/s` or be relaxed
  (`2026-06-25_postprocessing_registry_checkpoint.md`).
- Spot-check representative `case_summary.csv` and
  `wall_heat_flux_grouped.csv` outputs for physical reasonableness, not just
  file existence.
- Decide whether to add user-facing batch wrappers for TP, TW, and velocity
  plots across all runs.
- Decide whether grouped wall-heat output needs its own dedicated plot or
  report builder.
- Decide whether SQLite remains the defended fast format or whether Parquet is
  worth introducing later in a dedicated environment.
- For corner-pressure-drop outputs:
  - decide whether the table should remain all-case or be narrowed to a
    presentation/modeling subset
  - choose the preferred sign convention
  - add a flow-aligned sign layer only if the real question is "drop along
    flow" rather than "start-to-end patch order"
  - refresh underlying roots if true `10`/`20` retained-time windows are
    required rather than the current `4-5` retained rows
  (`2026-06-25_progress_checkpoint.md`).

#### Track D: Additive Paper-Evidence Wave

- Freeze a paper-grade Salt case inventory with case class, provenance, and
  current paper-facing usage mapping.
- Publish a versioned 3D-to-1D reduction contract:
  station map, branch map, reduction choices, and reproducible reduced data.
- Quantify the upcomer recirculation story with defended retained-time metrics
  and at least one figure-ready artifact.
- Publish a closure-status and blocked-questions table that labels each branch
  and closure family as `defended`, `support-gated`, `diagnostic-only`,
  `residual-only`, or `blocked`.
- Follow the ranked queue from
  `2026-06-26_ethan_progressive_story_synthesis/open_analysis_queue.md`:
  1. refresh the external replay against the frozen-state contract
  2. rebuild straight-section sensitivity on matured late windows
  3. expand retained-time branchwise thermal closure on blocked branches
  4. build the retained-time full-path feature extractor
  5. move Water from readiness to defended closure only after the Salt-first
     replay and closure lanes harden

#### Track E: Cleanup / Commit Curation

- Finish the commit-ready curation pass that removes generated figure/image
  artifacts from git while preserving code, text, manifests, provenance, and
  dated notes (`AGENT-127` scope on the board).
- Keep cleanup separate from science edits. If a cleanup action would touch a
  live analysis/report root outside the claimed curation scope, reopen it as a
  separate coordinator task instead of bundling it into Track E.

### Parallel-Agent Note Convention

- One claimed task, one status file, one raw journal file.
- Raw note files for June 29 live under `.agent/journal/2026-06-29/` and must
  include the task ID in the filename.
- Only the coordinator task updates this curated journal.
- If a task needs to cross into another track's claimed files, stop and reopen
  the board first rather than sharing notes or silently widening scope.

## Active-Board Audit

### Observed Output

- A June 29 status-file audit found that several rows still listed under
  `Active` on `.agent/BOARD.md` already report `complete` or `completed` in
  their owned status files:
  - `AGENT-124`, `AGENT-128`, `AGENT-129`, `AGENT-130`, `AGENT-131`,
    `AGENT-132`, `AGENT-133`, `AGENT-138`, `AGENT-145`
- `AGENT-146` itself is complete for the initial board/journal reset and can
  stay active only as the coordinator umbrella while the stale rows are pruned.
- `AGENT-132` is duplicated on the board under two separate goals while both
  rows point to the same status file.
- `AGENT-108` looked like the smallest real closeout candidate because its
  status only left one remaining follow-up: verify the temporary Salt
  checkpoint copy and confirm its local manifest state.
- `AGENT-121`, `AGENT-122`, and `AGENT-123` still look genuinely unfinished:
  the latest-window package chain is not fully published yet, and the
  dependency order in their status files still matches what is on disk.
- `AGENT-129` is not a clean closeout yet even though its status says
  `complete`; the backup logs still show rsync churn and there is no
  `manifests/latest/summary.txt` at the backup root yet.

### Interpretation

- The fastest useful cleanup is not new science first; it is to remove stale
  `Active` rows, close the duplicate `AGENT-132` bookkeeping, and then finish
  the smallest real remaining task so the board reflects reality again.
- The first practical follow-on is `AGENT-108`, not the longer latest-window
  chain or the still-open backup lane.

### Immediate Next Actions

- Write this audit into the curated June 29 journal.
- Close `AGENT-108` if the temporary Salt checkpoint copy is verified on disk.
- After that closeout, prune the obviously stale `Active` rows and decide
  whether `AGENT-129` needs to stay live as a backup-monitoring task or be
  reopened under a narrower follow-up.

## Active Working Plan

### Observed Output

- As of `2026-06-29 14:52 CDT`, `AGENT-121` is still actively rebuilding the
  exact retained latest-window `salt1_jin` package. The live run has finished
  retained times through `3615`, is actively reducing `3616`, and the exact
  retained-time manifest still shows `7` Salt 1 entries left after that before
  the builder can advance to `salt2_cont`, `salt3_cont`, and `salt4_cont`.
- The new dated paper-case inventory from `AGENT-147` is now on disk and
  freezes the current Salt paper subset as:
  - `paper-grade`: `Salt 1-4 Jin`
  - `exploratory`: `Salt 2 Kirst`
  - `blocked`: `Salt 1 Kirst`, `Salt 2 Val`
  - `exclude`: `Salt 3 Kirst`, `Salt 4 Kirst`

### Interpretation

- `AGENT-121` is not blocked, but it is not close enough to justify treating
  `AGENT-122` as immediate. At the current `salt1_jin` retained-time rate of
  about `3.2 min` per retained time once a cross-section batch is underway,
  Salt 1 itself looks like roughly another `25-30 min`, but the full four-case
  latest-window refresh still looks like a same-evening finish rather than an
  afternoon finish because `60` more retained times remain across Salt 2-4.
- Current coordinator estimate for `AGENT-121`:
  likely around `2026-06-29 19:00-20:00 CDT` if the present per-time
  reconstruction and cross-section rate holds, Salt 2-4 behave similarly to
  the current Salt 1 pass, and no new extraction stalls appear.
- The best additive next step while that long compute path runs is the
  reduction-contract audit (`AGENT-148`), because it can reuse the frozen
  `AGENT-147` subset and existing reduction outputs without colliding with the
  live latest-window rebuild.

### Active Order

1. Let `AGENT-121` continue to completion.
2. Once `AGENT-121` finishes, run `AGENT-122` to rebuild the latest-window
   validation and closure bakeoff.
3. After `AGENT-122`, run `AGENT-123` to refresh the latest-window
   discrepancy explainer on the same contract.
4. While `AGENT-121` runs, actively work `AGENT-148` to publish the versioned
   3D-to-1D reduction-contract audit.
5. After the reduction contract lands, use it to tighten `AGENT-150`, then
   `AGENT-149`.
