# External Report — 2026-07-13 CFD→1D Closure Workday, Blocker Audit, and Research Index

Date: `2026-07-13`
Role: Coordinator / Writer
Task: `AGENT-289`
Owner: claude
Branch: `main`

Tags: #external-report #blocker-audit #research-index #provenance #cfd-to-1d
#thermal-parity #rcExternalTemperature #radiation #mesh-gci #salt-q-perturbation
#forward-model #litrev-synthesis #closure-ledger #reconstruction-repair
#uncertainty #thesis-source

## Purpose

This is a single, external-report-grade journal entry for 2026-07-13. It answers
three questions for a reader who was not in the room:

1. **What are we trying to do** (the day's themes)?
2. **What concretely changed** (tools, data, decisions, runs, policy)?
3. **What is actually blocking us** — and, critically, which "blockers" are stale
   items already resolved on an earlier day and only *appear* open in stale
   summaries?

It then does the wider bookkeeping the user asked for: a consolidated **open-TODO
backlog** spanning all previous days, and a **record of every research avenue
pursued** with its outcome, so the master's thesis can be reconstructed from a
single hub. This entry is written to be Obsidian-navigable: stable topic tags
above, a `## Related` block below, and repo-relative links throughout.

> Method note. This entry was assembled by reading the core coordination files
> (`AGENTS.md`, `CLAUDE.md`, `.agent/BOARD.md`, `.agent/DECISIONS.md`, the MASTER
> TODO) and today's 33 journal entries / status files first-hand, then
> cross-checking against three independent documentation sweeps (today's work,
> historical blocker-resolution status, and the historical TODO/research-avenue
> record). Every claim below carries a repo-relative source path. No science
> artifacts, solver outputs, scheduler state, or external `../cfd-modeling-tools/`
> files were modified by this task — it is documentation only.

---

## 1. What we are trying (today's themes)

The overarching program is unchanged from the July roadmap: **build a 1D
thermal-hydraulic model of the TAMU molten-salt natural-circulation loop that
predicts CFD mass-flow and temperature distribution, using a branchwise closure
ledger rather than global fudge factors.** The guiding order is *thermal parity
before predictive fitting*: match the CFD external/source boundary contract, then
compare total and section heat, then station temperatures, then wall temperatures
(`operational_notes/07-26/10/2026-07-10_NEXT_MEETING_START_HERE.md`).

Today's 33 tasks (AGENT-259 … AGENT-288, no 276) group into eight themes:

- **A. Live-job scheduling, stop calls, and Salt-Q continuation.** Read-only
  heartbeat of carry-over CFD jobs, user-approved stops of the steady Salt1 rows,
  and a repacked 4-case continuation to use freed nodes.
  (`.agent/journal/2026-07-13/live-job-heartbeat-and-cleanup-call.md`,
  `salt1-cancel-and-corrected-q-node-repack.md`,
  `salt-q-four-row-packed-continuation.md`,
  `stopped-sbatch-steady-state-decisions.md`)
- **B. Salt-Q admission policy correction + quarantine cleanup.** User corrected
  the rule: a *converged* Salt-Q row is closure-fit admissible even if the old
  `too_short` post-restart gate would reject it; historical `corrected` suffix
  dropped from display names; old invalid June-19/25 staged roots deleted after
  path-specific approval. (`.agent/journal/2026-07-13/salt-q-admission-policy-and-short-names.md`)
- **C. Thermal boundary characterization + radiation separability.** Patch-role
  table → `rcExternalTemperature` source/binary audit → OF13 microcase evidence →
  policy correction that the CFD is **not** "no-radiation."
  (`thermal-boundary-patch-role-table.md`,
  `rc-external-temperature-implementation-audit.md`,
  `rc-external-temperature-publication-evidence.md`,
  `cfd-radiative-boundary-correction.md`)
- **D. Fixed-mdot 1D parity + the forward/predictive model path.** Fixed-mdot
  replay ladders to localize where section heat disagrees, plus a full
  forward-model research plan with blocker register and task backlog.
  (`patch-boundary-fixed-mdot-1d-parity.md`, `cfd-bc-no-radiation-1d-parity.md`,
  `predictive-heat-loss-path-package.md`,
  `cfd-bc-no-radiation-wall-layer-mapping-docs.md`,
  `forward-predictive-model-research-plan.md`)
- **E. Reconstruction repair + mesh-GCI for thermal closure.** Diagnosed corrupt
  reconstructed `T`, proved a split-reconstruction repair path, compared
  medium/fine pressure fields, and assembled a Salt2 Closure-QOI mesh-GCI package.
  (`reconstructed-t-repair-diagnosis.md`, `reconstructed-t-repair-trial.md`,
  `salt2-pressure-only-mesh-family-comparison.md`, `salt2-closure-qoi-mesh-gci.md`)
- **F. Literature-review synthesis into actionable gates.** HITEC closure review
  → lessons/pathways package → five gate packages (`TODO-LITREV-*`) implemented
  and indexed. (`litrev-lessons-and-research-pathways.md`,
  `litrev-synthesis-crosslinks-and-board-next-steps.md`, the five `litrev-*.md`
  entries, and AGENT-288's campaign index.)
- **G. Presentation / uncertainty story for the paper.** Time-series steady-state
  metrics → paper-facing uncertainty components → compact Salt2/3/4 presentation
  table. (`time-series-uncertainty-story.md`,
  `salt234-presentation-uncertainty-table.md`, `time-series-uncertainty-doc-polish.md`)
- **H. Documentation cross-referencing + board hygiene.** Lightweight
  `Related`/tag metadata added to the thermal-parity cluster (AGENT-260); stale
  Active-board rows retired (AGENT-278).
  (`thermal-doc-cross-reference-polish.md`, `active-board-stale-row-cleanup.md`)

---

## 2. What changed today (concrete)

### 2.1 New tools / scripts (all in `tools/analyze/`, each with a focused test)

- `run_cfd_bc_no_radiation_1d_parity.py` — 4-mode radiation-off fixed-mdot parity (AGENT-279).
- `build_cfd_radiative_boundary_guidance.py` — per-run emissivity/Tsur guidance (AGENT-287).
- `run_patch_boundary_fixed_mdot_1d_parity.py` — B0–B4 fixed-mdot ladder (AGENT-271).
- `build_predictive_heat_loss_path.py` (AGENT-270).
- `build_rc_external_temperature_implementation_audit.py` (AGENT-264) and
  `build_rc_external_temperature_publication_evidence.py` (AGENT-277).
- `build_thermal_boundary_patch_role_table.py` (AGENT-263).
- `diagnose_reconstructed_t_corruption.py` (AGENT-265).
- `build_salt2_pressure_mesh_family_comparison.py` (AGENT-262).
- `build_terminal_harvest_admission_review.py` (AGENT-283).
- `build_salt2_closure_qoi_mesh_gci.py` (AGENT-284).
- `build_time_series_uncertainty_story.py` (AGENT-272; extended for the
  presentation table by AGENT-273/275).
- `build_litrev_source_envelope_table.py` plus the four other `build_litrev_*`
  builders behind the LITREV gate packages (`TODO-LITREV-*`).

### 2.2 Behavior changes wired into existing tooling

- `build_registry_corrected_q_status_table.py` now marks converged/stationary
  terminal-window rows `closure_fit_admissible=yes` and emits short display keys
  (AGENT-269).
- `build_f4_ri_calibration_and_solver_gate.py`, `build_upcomer_onset_regime_table.py`,
  `build_presentation_readiness_and_rom_agenda.py`, and
  `build_tomorrow_presentation_package.py` no longer categorically exclude Salt-Q
  rows (AGENT-269).
- `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/scripts/run_selected_corrected_salt_q_continuation.sbatch`
  retargeted to the packed 4-case set with a ≤4-case / rank-vs-task guard
  (AGENT-269, AGENT-274).
- **The 1D `Fluid/` model source was deliberately NOT edited today** — every 1D
  interaction was read-only replay or planning, respecting the "draft the
  parity-mode spec before editing Fluid" rule.

### 2.3 New work products (`work_products/2026-07/2026-07-13/`)

`2026-07-13_cfd_bc_no_radiation_1d_parity/` (+ `wall_layer_bulk_temperature_mapping_recommendations.md`),
`2026-07-13_cfd_radiative_boundary_guidance/`, `2026-07-13_patch_boundary_fixed_mdot_1d_parity/`,
`2026-07-13_predictive_heat_loss_path/`, `2026-07-13_rc_external_temperature_implementation_audit/`,
`2026-07-13_rc_external_temperature_publication_evidence/`, `2026-07-13_thermal_boundary_patch_role_table/`,
`2026-07-13_reconstructed_t_repair_diagnosis/`, `2026-07-13_reconstructed_t_repair_trial/`,
`2026-07-13_salt2_pressure_only_mesh_family_comparison/`, `2026-07-13_salt2_closure_qoi_mesh_gci/`,
`2026-07-13_salt1_terminal_harvest_admission_review/`, `2026-07-13_stopped_sbatch_steady_state_decisions/`,
`2026-07-13_corrected_q_latest_time_refresh/`, `2026-07-13_forward_predictive_model_research_plan/`,
plus the five `2026-07-13_litrev_*/` gate packages and AGENT-288's `2026-07-13_litrev_todo_campaign_index/`.

### 2.4 New report

`reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/`
(README + `research_pathways.csv` + `summary.json`) — AGENT-282.

### 2.5 Decisions recorded (`.agent/DECISIONS.md`, 2026-07-13 block)

- **Steady-state stop evidence rule (AGENT-280):** every user-approved sbatch
  cancel / early stop / "ready to postprocess" call must leave a dated note with
  numeric final-window evidence (Slurm ID, case path, window bounds, mdot &
  `total_Q` mean/latest/drift/span, temp/wall drift, steady decision, admission
  usability); resource-driven stops must say so.
- **Radiation supersession (AGENT-277 + AGENT-287):** the stale "CFD no-radiation
  parity" assumption is superseded. Admitted Salt CFD uses `rcExternalTemperature`
  (emissivity `0.95`; Tsur=Ta `299.19 / 299.79 / 299.97 K` for Salt2/3/4).
  Radiation-off 1D replay must be labeled a **sensitivity, not parity**, and no
  separate 1D radiation term may be added on top of CFD `wallHeatFlux` (radiation
  is inseparable inside the total flux).

### 2.6 CFD jobs (Slurm IDs)

- **Cancelled (user-approved):** `3282992` (Salt1 nominal) and step `3288671.0`
  (Salt1 −10Q). `3288671` as a whole was deliberately **not** cancelled because
  that would kill the live Salt4 +10Q step `3288671.5`.
  (`salt1-cancel-and-corrected-q-node-repack.md`)
- `3288671` (selected corrected-Q) later reached `COMPLETED`, elapsed
  `3-00:23:10`, end `2026-07-13T12:42:33` on `c318-017` (AGENT-274).
- **Submitted:** `3293441` — new packed 4-case continuation (`salt2_lo10q`,
  `salt2_hi10q`, `salt4_lo10q`, `salt4_hi10q`), one 256-task node `c318-011`, 64
  ranks/case, from `login3` (`salt-q-four-row-packed-continuation.md`).
- Live interactive allocation at end of day: `3292998` on `c318-008`.

### 2.7 Key quantitative results recorded today

- **Cooler/HX is the dominant thermal lever.** Baseline fixed-mdot mean-abs Tmean
  error `63.746 K` → CFD-cooler-duty-only `4.456 K` (−59.29 K, 93.0%) (AGENT-270/271).
- **No-radiation parity modes (AGENT-279):** N0 `81.13 K`, N1 (heater+cooler
  imposed) `4.93 K`, N2 (setup BC + passive convection) `22.65 K`, N3 `118.92 K`;
  heater realized/imposed ratio `0.918126`; proposed diagnostic hA multiplier
  `0.666719` (blocked pending wall-layer mapping).
- **Radiation microcase deltas (AGENT-277):** emissivity 0.95→0.10 `−658.64 W`,
  →0.00 `−809.14 W`; Tsur 299.19→350 K `+1912.50 W`. `libRCWallBC.so` SHA256
  `34f4c7c2…81f09`.
- **Reconstructed-T repair (AGENT-267):** clean `518/T` (0 nonfinite, range
  `347.36–489.03 K`), 30/30 sampled rows; *smoke* rows — lower_leg HTC
  `457.34 W/m²/K`, upcomer HTC `77.94`, Nu `4.28`; downcomer still blocked.
- **Steady-state stop calls (AGENT-280):** salt1_nominal / lo10q / hi10q steady
  (max mdot rel. drift `8.0e-8` / `3.3e-7` / `2.0e-6`; `total_Q` drift `0 W`);
  **salt4_hi10q NOT steady** (mdot rel. drift `6.3e-3`, `total_Q` drift
  `−1.59 W`, probe drift `1.45 / 1.53 K`) → repacked into `3293441`.

---

## 3. Blockers (stated today, then audited)

### 3.1 Blockers stated in today's notes

| # | Blocker | Blocks | Source |
|---|---|---|---|
| B-rad | Radiation inseparable from total CFD `wallHeatFlux`; `rcExternalTemperature` C++ source not recovered from accessible locations | convection-vs-radiation split in any external-loss fit; calling radiation-off replay "parity" | `rc-external-temperature-implementation-audit.md`, `cfd-radiative-boundary-correction.md` |
| B-Trecon | Reconstructed refined-mesh `T` corruption (`-nan`); AGENT-267 rows are smoke, downcomer `thermally_blocked_segment_right_leg` | Salt2 refined thermal closure; thermal GCI | `reconstructed-t-repair-diagnosis.md`, `salt2-pressure-only-mesh-family-comparison.md` |
| B-gci | `0` publication-ready Closure-QOI GCI rows; hydraulic triplets oscillatory/divergent; thermal GCI blocked on fine thermal extraction | mesh-uncertainty bounds on f/Nu/UA' | `salt2-closure-qoi-mesh-gci.md` |
| B-fluidbc | Fluid does not accept first-class CFD wall-layer/external-boundary dictionaries; `B4_external_bc_equivalent_contract` is contract-only | true external-BC parity; forward wall-layer drive | `cfd-bc-no-radiation-1d-parity.md`, `patch-boundary-fixed-mdot-1d-parity.md` |
| B-walltemp | N2 `hA/Ta` replay over-removes heat; hA multiplier `0.666719` blocked pending wall-layer/bulk driving-temperature mapping | thermal parity below section level | `cfd-bc-no-radiation-1d-parity.md` |
| B-harvest | Post-exit terminal-gate harvest deferred while jobs still running | admission of Salt1/corrected-Q rows | `post-exit-gate-harvest-deferred.md` |
| B-salt4 | Salt4 +10Q not steady (mdot ~0.61%/600 s; probes ~1 K); log-tail advanced only `2.375 s` | terminal harvest of Salt4 +10Q | `salt-q-four-row-packed-continuation.md`, `corrected-q-latest-time-refresh.md` |
| B-cleanup | Cleanup unsafe while `3288671.5` lives (do not cancel `3288671`, allocation `3292998`, or the `srun` launcher) | interactive-allocation / tmux cleanup | `live-job-heartbeat-and-cleanup-call.md` |
| B-gate | Formal operating-point gate implies ~`15000 s` post-restart advance; short continuations still fail `too_short` | fast admission of the new Salt2 pair | `salt1-cancel-and-corrected-q-node-repack.md` |
| B-env | `pytest` absent for `python3.11`; `numpy` absent (must use system `python`); missing `upcomer_correlation_v2` input blocks one test | some test execution | `salt-q-admission-policy-and-short-names.md`, `cfd-bc-no-radiation-1d-parity.md` |

**Forward-model blocker register** (AGENT-286,
`work_products/2026-07/2026-07-13/2026-07-13_forward_predictive_model_research_plan/blocker_register.csv`):
B1 cooler/HX predictive duty (HIGH); B2 heater transfer efficiency (HIGH, ratio
0.918); B3 test-section source/sink contract (HIGH; setup +37 W but realized net
sink); B4 wall-layer driving temperature (see B-walltemp); B5 radiation
separability (see B-rad); B6 thermal mesh & reconstructed-T (HIGH; "0 fit
candidates"); B7 hydraulic closure fit-safety (MED-HIGH); B8 sensor location
(MEDIUM; coordinates provisional); B9 validation-split identifiability (HIGH; no
validation rows for fit parameters); B10 Fluid external-boundary API (see
B-fluidbc).

### 3.2 Blocker audit — which of these are REAL vs stale/forgotten

The user asked specifically whether reported blockers are genuine or things
already solved and forgotten. Cross-checking every recurring blocker against the
earliest and latest dated file that touched it:

| Blocker/problem | Verdict | Evidence (earliest → latest) |
|---|---|---|
| **OF12 `reconstructPar` SEGFAULT** (custom `libRCWallBC.so`) | **STALE / FALSE** | Still headlined in `CLAUDE.md §6` and MASTER TODO §2, but resolved by the OF13 env (`recon_salt{2,3,4}_of13` built) per `operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md §5`. Do **not** confuse with the genuinely-open refined-mesh `T` corruption below. |
| **"No mesh for GCI — waiting on Ethan's NCC mesh generator"** (T6) | **STALE / FALSE (as framed)** | `operational_notes/07-26/01/2026-07-01_T6_gci_blocker_ethan_request.md` and `CLAUDE.md §4` still say BLOCKED-on-external-mesh; superseded `2026-07-09` — Ethan's coarse/medium/fine family (24 cases) is readable (`operational_notes/07-26/09/2026-07-09_salt_mesh_refinement_discovery_plan.md`) and Salt2 endpoint-monitor GCI rows are admitted. The *real* remaining blocker is narrower (below). |
| **"CFD has no radiation, run 1D radiation-off to match"** | **STALE / FALSE (corrected today)** | `.agent/DECISIONS.md` (2026-07-08) said "no `qr` term, don't double-count." Superseded today: `rcExternalTemperature` **does** include radiative exchange (emissivity 0.95, Tsur ~299 K), verified by a microcase where changing emissivity/Tsur alone moved `wallHeatFlux`. Radiation-off is now a sensitivity, not parity (`cfd-radiative-boundary-correction.md`, `.agent/DECISIONS.md` 2026-07-13). |
| **"All 14 Q-perturbation runs false-steady / quarantined, none usable"** | **STALE / PARTIAL** | `CLAUDE.md §4` still headlines T2 as quarantined. Superseded: June runs deleted and corrected runs relaunched (`2026-07-04`), and today's admission policy makes converged corrected rows closure-fit admissible, with salt1_nominal/lo10q/hi10q confirmed steady. Genuinely open: salt4_hi10q not steady (repacked into `3293441`), and true insulation variants were never applied. |
| **Refined-mesh reconstructed `T` corruption (`-nan`)** | **REAL / OPEN** | New problem under OF13 (`.agent/journal/2026-07-09/salt2-refined-closure-qoi-repair-batch.md` → `.agent/journal/2026-07-13/reconstructed-t-repair-diagnosis.md`). A split-reconstruction workaround exists (AGENT-267) but rows are smoke, not admitted. |
| **Closure-QOI mesh GCI not publication-ready** | **REAL / OPEN** | `salt2-closure-qoi-mesh-gci.md`: 14 hydraulic triplets diagnostic-only (oscillatory/divergent), thermal blocked. This — not "no mesh" — is the true #1 trust limiter now. Refined NCC interface also breaks the OF13 `fvMeshStitcher` (needs conformal-first remesh; `2026-07-09_salt_mesh_refinement_discovery_plan.md`). |
| **Thermal CFD↔1D mismatch** | **REAL / OPEN** | Roadmap defined (`operational_notes/07-26/10/2026-07-10_thermal_parity_roadmap.md`, 7-study ladder), not executed; internal wall-adjacent-T model unsolved. |
| **Upcomer onset — too few Re points / extrapolated** | **REAL / OPEN** | `.agent/journal/2026-07-08/upcomer-onset.md`: all admitted points in-cell; onset is an extrapolated bracket, not a calibrated closure. |
| **F5 Ri-corrected friction fit** | **REAL / OPEN (closed as negative)** | `operational_notes/07-26/08/2026-07-08_friction_ri_failure_and_path_forward.md`: F5≡F3_shah_apparent, all leg fits R²<0, c≈0; preserved as negative evidence; next is φ(Re)/F6 `1+a/Re^b`. Production friction closure is `F3_shah_apparent`. |
| **Upper-leg single-leg negative friction** | **RESOLVED (scope-limited)** | Resolved by the de-buoyed momentum budget (`.agent/journal/2026-07-01/T1b-momentum-budget-debuoyed-friction.md`); only isothermal-upcomer f (~2–2.7) fully trustworthy (memory `friction-buoyancy-source-finding`). |

**Bottom line for an external reader:** of the classic headline blockers, **three
are stale and should be scrubbed from `CLAUDE.md`/MASTER TODO on the next edit** —
the OF12 reconstructPar segfault, the "no mesh exists for GCI," and the "CFD has
no radiation" framing. The genuinely-open frontier blockers are: closure-QOI mesh
GCI (blocked on conformal remesh + reconstructed-T repair), refined-mesh `T`
corruption, thermal parity / internal-development model, upcomer onset data
sparsity, the predictive heater/cooler/wall-layer submodels, and the Fluid
external-boundary API gap.

### 3.3 Documentation-integrity anomalies found (already logged as reopen items)

- **AGENT-276** holds a board claim but has no status/journal/import file and
  incomplete outputs (its promised no-radiation fixed-mdot replay results were not
  found). Logged for reopen in `active-board-stale-row-cleanup.md`.
- **AGENT-277**'s README contradicts its own decision JSON
  (`microcase_confirmed=true` in the decision file vs. README text saying the
  microcase was not confirmed). Needs reconciliation before publication use; also
  logged in `active-board-stale-row-cleanup.md`.

---

## 4. Consolidated open-TODO backlog (all days, deduplicated)

Sweep of the MASTER TODO, the July-8/9/10/13 notes, the June-30 scope/checklist,
all July reports, and every `.agent/BOARD.md` row. Completed July-8/9 ledger rows
(observation table, pressure ledger, patchwise/enthalpy heat ledgers, two-tap
minor loss, postprocessor charts, the five LITREV packages, interface sampling)
are **done** and listed only in §5 so they are not reopened by mistake.

| ID | Description | Status | Dep / blocked-on | Source |
|---|---|---|---|---|
| T6 / TODO-MESH-UNCERTAINTY | Mesh-independence (GCI) bounds on f/Nu/UA' | BLOCKED (meshes exist; 0 pub-ready GCI; NCC interface breaks fvMeshStitcher; reconstructed medium T `-nan`) | conformal remesh + T-repair | `2026-07-09_salt_mesh_refinement_discovery_plan.md`, `salt2_closure_qoi_mesh_gci/` |
| T10 / TODO-UPCOMER-ONSET | Upcomer onset law bf=F(Ri) + Nu(Ra,Pr) | STARTED (all points in-cell; onset extrapolated) | more Re points (T2/T13), mesh UQ | `work_products/2026-07/2026-07-08/2026-07-08_upcomer_onset/` |
| T11 | Re-derive published closure bundle from continuation window | BLOCKED | T6 bounds; external Fluid owner | MASTER TODO |
| T13 | Onset/limit CFD campaign (push Re 200–400) | DESIGN DONE, not launched | T2 requal, approval | `operational_notes/07-26/08/2026-07-08_t13_run_campaign_proposal.md` |
| F4 | Buoyancy/Ri-corrected friction for heated/cooled legs | OPEN (candidate; leg-class over-stiffens −23…−25% mdot) | more operating points; wall-bulk T | `reports/2026-07/2026-07-09/2026-07-09_friction_correlation_math_reference/` |
| F6 | φ(Re) friction correction after F5 failed (`1+a/Re^b`) | OPEN | Q-gate; self-consistent Ri; per-segment insulation BCs in 1D | `operational_notes/07-26/08/2026-07-08_friction_ri_failure_and_path_forward.md` |
| TODO-TARGETED-LITREV-FORMS | Lit-review forms → verified candidate equations | OPEN | verify Shah constants vs primary source | BOARD; `2026-07-09_friction_correlation_math_reference/` |
| TODO-PRED-INPUT-CONTRACT | Classify every forward-model field (input/calibrated/validation/diagnostic) | IN-PROGRESS (codex) | AGENT-286 | `forward_predictive_model_research_plan/task_backlog.csv` |
| TODO-PRED-FORWARD-V0 | Pressure-rooted forward mode (heater+imposed cooler → mdot+sensors; no CFD mdot at runtime) | IN-PROGRESS (codex) | INPUT-CONTRACT | same |
| TODO-PRED-HX-FIT | Replace imposed cooler duty with UA / ε-NTU | OPEN | FORWARD-V0 | same |
| TODO-PRED-HEATER-TEST-CONTRACT | η_heater + test-section source-plus-loss | OPEN | INPUT-CONTRACT | same |
| TODO-PRED-WALL-LAYER | Extract wall/shell/bulk temps + E0/E1/E2 replay (explain N2 overcooling) | OPEN | INPUT-CONTRACT | same; `cfd-bc-no-radiation-wall-layer-mapping-docs.md` |
| TODO-PRED-HYDRAULIC-GATE | Pressure-rooted mdot predictivity on fit-safe rows | OPEN | AGENT-262/284 | same |
| TODO-PRED-THERMAL-MESH-GATE | Salt2-first thermal extraction/GCI | OPEN | AGENT-284; T-repair | same |
| TODO-PRED-SENSOR-MAP | Confirm/bound TP/TW sensor coordinates → 1D path | OPEN | FORWARD-V0 | same |
| TODO-PRED-VALIDATION-SPLIT | Train/validation admission protocol | OPEN | HX-FIT + HEATER-TEST | same |
| TODO-PRED-ENDTOEND-SCORE | Predictive scorecard (mdot, branch heat, Tmean, loop ΔT, TP/TW) | OPEN | all PRED gates | same |
| TODO-PREDICT-HEATER-FLUID-FRACTION | Predict fraction of resistor power into fluid (η_heater) | OPEN (HIGH) | — | BOARD |
| TODO-PREDICT-COOLER-REMOVAL | Predict cooler removal without imposing CFD duty | OPEN (HIGH; strongest lever, 63.75→4.46 K) | — | BOARD; `2026-07-09_external_boundary_setup_reference/` |
| TODO-1D-RADIATION-CAPABILITY | Stefan-Boltzmann segment losses in 1D, no double-count | OPEN (MED/HIGH) | rcExternalTemperature audit (done) | BOARD; `.agent/DECISIONS.md` |
| Thermal-parity Studies 3–7 | external-BC parity → source/sink parity → section heat-loss decomp → internal-development diagnostic → predictive internal model | OPEN (Studies 1–2 done) | parity-mode spec before editing Fluid | `operational_notes/07-26/10/2026-07-10_thermal_parity_roadmap.md` |
| Fluid first-class fixed-mdot / frozen-hydraulics mode | native replay mode in Fluid | OPEN | — | `2026-07-09_external_boundary_setup_reference/` |
| Recover exact `rcExternalTemperature` source | compiled-library provenance for pub-strength | OPEN | run-env library access | `2026-07-10_thermal_parity_roadmap.md` |
| Op: Salt1 nominal post-exit gate | admit only after `3282992` exits + gate evidence | OPEN (job cancelled 2026-07-13; run terminal harvest next) | job terminal | `2026-07-10_end_of_day_todo.md` |
| Op: corrected-Q continuation gate | gate `3293441` steps; admit only `operating_point_verdict=requalified` | OPEN | job exit; SU/allocation | `salt-q-four-row-packed-continuation.md` |
| Op: salt3 hi5q/hi10q diagnosis | still-drifting (24%/45%) near-empty rows; likely rebuild | OPEN | — | `2026-07-10_end_of_day_handoff_and_todo.md` |
| Op: 10 clean Q-perturbation extended continuations | extend salt2{±5,±10q}, salt4{±5,±10q}, salt3{lo5q,lo10q} | OPEN | SU/allocation; Codex coord | `2026-07-10_end_of_day_handoff_and_todo.md` |
| Op: regenerate steady-state pkg at 600 s | on-disk is 300 s | OPEN | — | `2026-07-10_end_of_day_handoff_and_todo.md` |
| Op: integrate improved pressure figures into July-8 deck | wire `svg_chart_kit` into Codex chart builder | OPEN | Codex coord | `2026-07-10_end_of_day_handoff_and_todo.md` |
| TODO-MODEL-FORM-BAKEOFF | full bakeoff with model-specific thermal scores | STARTED (starter done; external Fluid rerun needed) | Fluid rerun | `work_products/2026-07/2026-07-08/2026-07-08_model_form_bakeoff/` |
| Per-leg friction multiplier | calibrate/validate the per-leg (vs global) multiplier | PARTIAL (implemented AGENT-171; not calibrated) | per-case thermal match | `reports/2026-07/2026-07-01/2026-07-01_model_form_comparison/` |
| Open factor-2 mdot discrepancy | ~2× mdot mismatch at matched-T with CFD friction | OPEN (no validated mechanism) | term-by-term momentum reconciliation | `reports/2026-07/2026-07-02/2026-07-02_overnight_synthesis/` |
| Litrev Tier-2/3 pathways | fitting inventory + `K_source_status`; internal-HTC bakeoff; Chen 2017 conditional; reset-distance map; radiation bound; single-stream diagnostics; experimental upgrades; transient extension; ROM archive | OPEN (planning done; extraction/experiment pending) | source-envelope gate | `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/research_pathways.csv` |
| Paper integration | absorb June-29/30/July-1+ packages into `../papers/3d_analysis` | OPEN | — | `reports/2026-07/2026-07-01/2026-07-01_paper_simulation_state_handoff/` |
| CFD gravity-orientation vs rig audit | reconcile CFD heater/cooler inclination with 20° rig | OPEN (inclination-based "downcomer transverse" claim retracted) | Ethan / mesh audit | `operational_notes/06-26/30/2026-06-30_next_scope_branch_closures_and_cfd_design.md §5b` |

---

## 5. Research avenues pursued (the record, for thesis reconstruction)

Every distinct direction attempted and its outcome. Structural takeaway across the
whole record: the literature does **not** support a single global f, Nu, or
heat-loss UA — the work has converged on a **branchwise closure ledger** (reference
limits / active closures / diagnostic gates / residuals kept strictly separate)
with a **thermal-parity-before-predictive-fitting** ordering.

| Avenue | What was tried | Outcome | Source |
|---|---|---|---|
| F1 friction (64/Re) | `friction_form="F1"` | PARTIAL — reference/diagnostic only, flagged `failed_as_predictive_form` | `2026-07-01_model_form_comparison/` |
| F3 Hagenbach | `F3_hagenbach` entry correction | WORKED (implemented) | `CLAUDE.md §3` |
| **F3 Shah apparent** | `F3_shah_apparent` developing-length friction | **WORKED — current baseline** (Salt2/3/4 mdot −0.93 / +3.33 / +3.75 %) | `2026-07-09_friction_correlation_math_reference/` |
| F4 buoyancy-modified | `F4_leg_class`, de-buoyed target, Ri candidate | PARTIAL/FAILED — leg-class over-stiffens (−23…−25% mdot), upcomer R²=0.02; not validated | `work_products/2026-07/2026-07-07/2026-07-07_f4_buoyancy_friction/` |
| F5 Ri-corrected (φ=1+c·Ri) | fit φ vs Ri per leg | FAILED (negative evidence kept) — R²<0, c≈0, 3 pts, Ri/Re collinear; next φ(Re)/F6 | `2026-07-08_friction_ri_failure_and_path_forward.md`; memory `friction-ri-fit-failure` |
| F-lit laminar forms | Shah, Baehr-Stephan, etc. screens | PARTIAL — candidate screens built; not promoted; constants need primary-source check | `work_products/2026-07/2026-07-07/2026-07-07_f_lit_forms/` |
| Per-leg vs global multiplier | per-leg multiplier in solver | PARTIAL — highest-value hydraulic lever; not calibrated | `2026-07-02_overnight_synthesis/` |
| Thermal closures (patch-based) | OF13 T-recon → per-segment HTC/UA'/Nu on Salt2/3/4 | WORKED (trustworthy, coarse-mesh caveat) — lower_leg HTC 252/269/288; upcomer Nu 3.1/4.1/5.0; downcomer HTC~43–44 | `work_products/2026-06-30_claude_thermal_htc/` |
| Internal Nu model-form comparison | CFD effective HTC vs 1D laminar-max/Dittus-Boelter | PARTIAL — CFD imposes no internal Nu; effective Nu diagnostic; largest T error tied to cooler duty not Nu | `reports/2026-07/2026-07-09/2026-07-09_internal_nu_model_form_comparison/` |
| Momentum-budget (de-buoyed) friction | variable-density buoyancy-corrected p_rgh gradients | PARTIAL — positive f only on fit-safe spans / isothermal upcomer (~2–2.7); single-leg heated/cooled → negative f | `work_products/2026-07-01_claude_momentum_budget/`; memory `friction-buoyancy-source-finding` |
| Mesh PCA centerlines | `build_mesh_centerlines.py` | WORKED — heater 21.5°, bores 20.9/22.1 mm; corrected probe-CSV schematic (lower↔right swap) | `work_products/2026-07-01_claude_mesh_centerlines/` |
| Span↔patch mapping audit | co-location check; label swap in profiles | WORKED — 0.566 m separation; fix landed; UA'/q' +27–33% | MASTER TODO (T8) |
| Q-perturbation (original) | hiq/loq/hi5q/lo5q/hiins/loins/optins | FAILED — all 14 false-steady; insulation knob never applied; quarantined | MASTER TODO (T3); `2026-07-04_salt_perturbation_quarantine_and_relaunch.md` |
| Corrected Q-perturbation | patched restart + patches + dynamicCode; extended continuations | PARTIAL — some requalified; salt3 hi5q/hi10q drifting (24%/45%); salt4 +10Q time-precision failures then repaired | `salt-q-admission-policy-and-short-names.md` |
| Convergence requalification gate | `--require-moved-from` | WORKED — exposed all 14 originals as false-steady | MASTER TODO (T3) |
| Time-series / steady-state UQ | 52 postProcessing dirs; trend + CLT SEM + autocorrelation | WORKED — steady rel. uncertainty 0.001–0.05%; `total_Q` "not steady" = near-zero residual noise; adopt 600 s window | `work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/` |
| Mesh refinement / GCI | refineMesh ×8 + external coarse/med/fine; `compute_gci.py` | FAILED/BLOCKED — refined NCC breaks OF13 fvMeshStitcher; walltime kills; reconstructed medium T `-nan`; 0 pub-ready GCI | `2026-07-09_salt_mesh_refinement_discovery_plan.md`; `salt2_closure_qoi_mesh_gci/` |
| Upcomer recirculation / cell model | backflow fraction + Ri/Ra/Re; all-span recirc | PARTIAL — cell confirmed (upcomer 15–33% backflow; downcomer ~0%); onset/max extrapolated | `operational_notes/06-26/30/2026-06-30_upcomer_convection_cell_model.md` |
| Upcomer onset Route A (data) | regress backflow vs Re, extrapolate to bf→0 | PARTIAL (LOW trust) — lower shutoff Re≈240–260; 2–4× beyond data | `2026-06-30_next_scope_branch_closures_and_cfd_design.md §4` |
| Upcomer onset Route B (reversal criterion) | Jackson-Cotton-Axcell Gr/Re^n vs threshold | PARTIAL (hand estimate) — Re_crit≈100–235, Ri_crit≈O(1); brackets Route A to ~2× | `mixed_convection_reversal.py` |
| Bend/junction minor-loss K (NIST two-tap) | straight-friction-removed two-tap | WORKED — corner K_apparent 6.22–16.50; connector K undefined (recirc) | `work_products/2026-07/2026-07-08/2026-07-08_minor_loss_two_tap/` |
| Downcomer closure | unblock thermal + reversal check | WORKED — ordinary f(Re)+Nu, no recirc (alignment 0.99) | `operational_notes/06-26/30/2026-06-30_downcomer_closure_analysis.md` |
| Fixed-mdot / frozen-hydraulics replay | CFD-informed fixed-mdot 1D replay | PARTIAL — package built; first-class Fluid mode needed; cooler duty strongest lever (63.75→4.46 K) | `work_products/2026-07/2026-07-08/2026-07-08_cfd_informed_fixed_mdot_1d_runs/` |
| Radiation / thermal boundary contract | patch-role table + rcExternalTemperature audit + microcase | WORKED (audit) — emissivity/Tsur affect wallHeatFlux but embedded (no separate qr) → radiation inseparable; off-replay ≠ parity | `2026-07-13_cfd_radiative_boundary_correction.md`; `.agent/DECISIONS.md` |
| Heat-loss calibration (resistance network) | separate jacket/passive/radiation/heater/residual | PARTIAL — 207 heat-path rows; internal Nu blocked from absorbing external loss; cooler under-removes ~90–116 W; 0 fit-candidate rows | `work_products/2026-07/2026-07-13/2026-07-13_litrev_heat_loss_calibration/` |
| Forward / predictive 1D model | research plan + input-readiness matrix + blocker register + backlog | PARTIAL/IN-PROGRESS — can run forward but not thesis-strength predict mdot+sensors from setup alone | `2026-07-13_forward_predictive_model_research_plan/` |
| Property sensitivity | matrix over Reis/Jadyn, Sohal/Janz, Jin+Parida+Santini, Jin+1560+0.60, Shen | WORKED (gate) — 90 branch + 15 mode rows; "no calibration before property lane selection"; 1D default now salt_jin | `work_products/2026-07/2026-07-13/2026-07-13_litrev_property_sensitivity/`; memory `jin-property-default` |
| Source-envelope gate | branch nondim envelope + source-overlap flags | WORKED (gate) — 90 branch + 360 overlap rows; Chen 2017 vs audited ranges; Tian 2024 reference-only | `work_products/2026-07/2026-07-13/2026-07-13_litrev_source_envelope/` |
| Model-form comparison (mdot metric) | test mdot as closure metric | PARTIAL — mdot not robust (±27% condition-dependent); per-segment ΔP is robust; dominant error = thermal boundary | `reports/2026-07/2026-07-01/2026-07-01_model_form_comparison/` |
| 1.4-in insulation boundary fit | 2-param compact fit | PARTIAL — best `fit_major_k90_1p4` 3.10% mdot err; but k90=0 is compensation artifact, not physics | `reports/2026-07/2026-07-01/2026-07-01_rom_model_form_fits_and_1p4_boundary/` |
| Postprocessing / ROM honesty audit | check formulas used outside valid assumptions | WORKED (audit) — 9 "left on table" items; f(Re)/Nu(Re) are narrow laminar calibrations, not correlations | `reports/2026-07/2026-07-01/2026-07-01_postprocessing_rom_honesty_audit/` |
| Solver Ra/Ri/Gr definition audit | page-audit coded dimensionless fields | WORKED — Lc=nominal bore, TRef=447 K, Nu uses Tw−TRef; use section MEDIAN Ri (~O(1)) | MASTER TODO (T9) |
| ROM (POD/POD-FV/C-ROM) | literature review | ABANDONED-for-now — deferred until FOM/snapshots/stabilization/validation; archive state vectors now | `2026-07-13_litrev_lessons_and_research_pathways/` (Lesson 9) |
| Transient/stability extension | Welander/Creveling/Vijayan review | CONDITIONAL/deferred — out of steady closure unless thesis scope activates | same (Tier 3) |
| Pressure decomposition figures | redesigned stacked/loss figures | WORKED — fixed legibility/scale; reusable `svg_chart_kit`; not yet in Codex July-8 deck | `work_products/2026-07/2026-07-09/2026-07-09_pressure_decomposition_figures/` |

**Completed foundation packages (do not reopen):** TODO-OBSERVATION-TABLE-CONTRACT,
TODO-OBSERVATION-TABLE-THERMAL-REFRESH, TODO-PRESSURE-TERM-LEDGER,
TODO-PATCHWISE-HEAT-LEDGER, TODO-HEAT-ENTHALPY-INTERFACE-LEDGER,
TODO-MINOR-LOSS-TWO-TAP, TODO-POSTPROCESSOR-CHARTS,
TODO-THERMAL-OPENFOAM-INTERFACE-SAMPLING, and the five `TODO-LITREV-*` packages.

---

## 6. Recommended next sequence

1. **Scrub stale blockers** from `CLAUDE.md §4/§6` and the MASTER TODO: OF12
   reconstructPar segfault (fixed by OF13), "no mesh for GCI" (meshes exist), and
   "CFD has no radiation" (superseded by AGENT-277/287). Replace with the real
   frontier blockers (§3.2). *(Coordinator edit — separate task, needs the
   `CLAUDE.md`/MASTER-TODO owner.)*
2. **Forward model:** finish `TODO-PRED-INPUT-CONTRACT` → `TODO-PRED-FORWARD-V0`
   (in progress, codex).
3. **Thermal closure unblock:** run the AGENT-267 split-reconstruction + OF13
   fallback on the Salt2 **fine** case; review sign/heat-balance on medium
   lower_leg/upcomer; keep downcomer blocked.
4. **Mesh GCI:** pursue the conformal-first remesh so refined levels survive the
   OF13 `fvMeshStitcher`; then close closure-QOI GCI.
5. **Runs:** monitor `3293441`; re-run the corrected-Q admission gate once late
   windows exist; diagnose salt3 hi5q/hi10q; run the deferred post-exit terminal
   harvest for the cancelled Salt1 rows.
6. **Reconcile the AGENT-276 / AGENT-277 documentation anomalies** (§3.3).

---

## Files inspected (representative)

`AGENTS.md`, `CLAUDE.md`, `.agent/BOARD.md`, `.agent/DECISIONS.md`,
`.agent/journal/README.md`,
`operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md`,
all `.agent/journal/2026-07-13/*.md`, all `.agent/status/2026-07-13_*.md`,
`operational_notes/07-26/13/*`, `operational_notes/07-26/10/*`,
`operational_notes/07-26/08/*`, `operational_notes/07-26/09/*`,
`reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/README.md`,
and the July `reports/` package READMEs referenced above.

## Files changed by this task

- `.agent/journal/2026-07-13/coordinator-writer-external-report-and-blocker-audit.md` (this file)
- `operational_notes/07-26/13/2026-07-13_external_report_research_index_and_blocker_audit.md` (connected index hub)
- `.agent/status/2026-07-13_AGENT-289.md`
- `imports/2026-07-13_external_report_and_blocker_audit.json`
- `.agent/BOARD.md` (own AGENT-289 row only)

## Incomplete lines of investigation

- This entry does not re-verify every quantitative number by re-running tools; it
  reports the values recorded in today's packages with their provenance.
- The stale-blocker scrub of `CLAUDE.md`/MASTER TODO is *recommended*, not done
  here — those files are owned elsewhere and editing them is out of this task's
  scope.

## Related

- `operational_notes/07-26/13/2026-07-13_external_report_research_index_and_blocker_audit.md` (the connected hub for this entry)
- `operational_notes/07-26/10/2026-07-10_NEXT_MEETING_START_HERE.md`
- `operational_notes/07-26/10/2026-07-10_thermal_parity_roadmap.md`
- `operational_notes/07-26/13/2026-07-13_litrev_synthesis_start_here.md`
- `operational_notes/07-26/13/2026-07-13_forward_predictive_model_research_plan.md`
- `operational_notes/07-26/13/2026-07-13_cfd_radiative_boundary_correction.md`
- `operational_notes/07-26/08/2026-07-08_friction_ri_failure_and_path_forward.md`
- `operational_notes/07-26/09/2026-07-09_salt_mesh_refinement_discovery_plan.md`
- `operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md`
- `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/README.md`
- `.agent/DECISIONS.md`
- `.agent/BOARD.md`
