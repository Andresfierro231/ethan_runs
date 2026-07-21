# AGENT-102 June 29 Raw Note

## Observed output

- Updated `tools/analyze/build_ethan_fluid_replay_against_frozen_state.py` to
  use the nested June 22 report roots and to audit the external `Fluid` repo
  against the new parallel `ethan_cfd_informed_salt_v2` contract instead of
  assuming a pure `v1` blocker.
- Regenerated
  `reports/2026-06/2026-06-22/2026-06-22_ethan_fluid_replay_against_frozen_state/`.
  `summary.json` now reports:
  - tracked bundle `ethan_cfd_informed_salt_v2`
  - tracked bundle generated on `2026-06-29`
  - `open_blocker_count = 2`
- Updated the sibling `Fluid` repo so the parallel `v2` path exists in code,
  configs, tests, and static validation data:
  - `validation_data/ethan_cfd_informed_salt_v2/**`
  - `tools/build_ethan_cfd_informed_salt_v2_bundle.py`
  - `configs/campaigns.yaml`
  - `configs/scenarios.yaml`
  - `tests/test_ethan_cfd_informed_salt.py`
  - `tests/test_profile_descriptor_closure.py`
- Narrow external verification now passes under module `python`:
  `python -m unittest tests.test_ethan_cfd_informed_salt tests.test_profile_descriptor_closure`
- Launched a live bounded rerun in the sibling `Fluid` repo:
  `python -m tamu_loop_model_v2.run_resumable --campaign ethan_cfd_informed_salt_v2 --output-root results/diagnostics/ethan_cfd_informed_salt_v2 --output-label ethan-cfd-informed-salt-v2 --jobs 2`
- As of `2026-06-29T13:48:26-05:00`, observed partial external outputs include:
  - `results/diagnostics/ethan_cfd_informed_salt_v2/scenario_manifests/000_ethan_cfd_informed_salt_v2_baseline_ins_1.0in_rad_0.csv`
  - `results/diagnostics/ethan_cfd_informed_salt_v2/scenario_manifests/002_ethan_cfd_informed_salt_v2_baseline_ins_1.0in_rad_1.csv`
  - `results/diagnostics/ethan_cfd_informed_salt_v2/ethan_cfd_informed_salt_v2_baseline_ins_1.0in_rad_0/Salt_1/summary.csv`

## Inferred interpretation

- The main June 23 blocker is no longer “no producer / no v2 wiring”.
- The external blocker has narrowed to two bounded items:
  - no finalized readable `v2` campaign output yet
  - static `v2` bundle still carries forward descriptor and safe-subset surface
    tables unchanged from `v1`
- The local June 22 replay package can now state the true external status
  without pretending the repo is still fully pinned to `v1`.

## Contradictions and corrections

- The local replay builder had been hard-coded to the flat
  `reports/2026-06-22_*` paths. The actual June 22 package roots are nested
  under `reports/2026-06/2026-06-22/`.
- The first `v2` scenario insertion accidentally absorbed four legacy `v1`
  scenarios into the `v2` campaign. This was corrected by restoring the full
  six-scenario `v1` list and keeping the `v2` campaign to its intended six
  `v2_*` scenarios only.
- A prepared external output root is not sufficient evidence of a readable new
  replay surface. The local audit now requires finalized `run_manifest.csv`
  before marking readable `v2` diagnostics present.

## Next suggested actions

- Poll the live external rerun until
  `results/diagnostics/ethan_cfd_informed_salt_v2/run_manifest.csv` exists.
- Re-run
  `python3.11 -m tools.analyze.build_ethan_fluid_replay_against_frozen_state`
  once the external rerun finalizes so the local June 22 replay package can
  cite a completed readable `v2` surface if the run succeeds.
- Decide whether the carried-forward `profile_descriptor_bundle.csv`,
  `ua_prime_surface.csv`, and `htc_surface.csv` justify a new follow-on task
  before treating the external refresh as fully regenerated science.

## Clarification added at 2026-06-29T14:48:40-05:00

- The live `ethan_cfd_informed_salt_v2` run is a `Fluid` reduced-order replay,
  not a new 3D CFD solve.
- Concretely, it is the external `Fluid` 1D loop model campaign launched with:
  `python -m tamu_loop_model_v2.run_resumable --campaign ethan_cfd_informed_salt_v2 ...`
- The `v2` label means:
  - the 1D `Fluid` campaign is pointed at the new tracked static bundle under
    `validation_data/ethan_cfd_informed_salt_v2/`
  - that bundle refreshes the closure contract and provenance against the June
    23/26 local Ethan stack
  - the bundle still carries some descriptor and safe-subset surface tables
    forward unchanged from `v1`
- So the live run is best described as:
  a refreshed 1D/ROM replay against the newer `v2` static contract, not a new
  CFD rerun.

## Immediate next work note

- Wait for the `Fluid` 1D `v2` replay to finalize and write
  `results/diagnostics/ethan_cfd_informed_salt_v2/run_manifest.csv`.
- Once that exists, rebuild the local June 22 replay package with
  `python3.11 -m tools.analyze.build_ethan_fluid_replay_against_frozen_state`.
- Then compare:
  - finalized readable `v2` 1D rows
  - legacy readable `v1` 1D rows
  - June 22 frozen-state CFD contract
- If the readable `v2` surface is materially better, publish that in the local
  replay package and narrow the remaining blocker to the still-carried-forward
  `v1` tables.
- If the readable `v2` surface is not materially better, open the next follow-on
  around the surface-table refresh rather than pretending the bundle rename
  alone solved the replay gap.

## Update added at 2026-06-29T15:45:00-05:00

- Earlier inspection incorrectly concluded that the original local `--jobs 2`
  `ethan_cfd_informed_salt_v2` replay had exited. A later process check showed
  the original worker family was still alive on the compute node:
  - parent `2642865`
  - workers `2642940`, `2642943`
- The output root remains partial but is still advancing:
  - `scenario_manifests/001_ethan_cfd_informed_salt_v2_hybrid_ins_1.0in_rad_0.csv`
    is still missing entirely
  - `003_ethan_cfd_informed_salt_v2_hybrid_ins_1.0in_rad_1.csv` currently
    contains `Salt 1` and `Salt 2` only
  - `005_ethan_cfd_informed_salt_v2_hybrid_ins_2.0in_rad_1.csv` currently
    advanced from `Salt 1` only to `Salt 1-3`
  - `000_ethan_cfd_informed_salt_v2_baseline_ins_1.0in_rad_0.csv` still stops
    after `Salt 2`
  - no finalized `run_manifest.csv` exists yet
- A separate `nohup` wrapper was launched at user request so the run would be
  left overnight, but that wrapper PID exited immediately without creating a
  second durable worker family. The effective overnight work remains the
  original active `2642865` process tree.
- Recommended relaunch shape is no longer “add more workers to the live run”.
  It is a clean scenario-level split:
  - reuse the prepared output root only if `solve-scenario` resume behavior is
    confirmed safe, otherwise stage a fresh `v3` root
  - run the heavy remaining hybrid scenarios as separate scenario workers
    (`001`, `003`, `005`)
  - optionally run the quick remaining baseline tail (`000`) as a fourth small
    worker or fold it into the shortest hybrid lane
  - prefer `taskset` on a compute node or a tested Slurm array submission over
    another single monolithic `--jobs 2` replay
- The key test before any larger relaunch is one end-to-end split workflow:
  `prepare`, one `solve-scenario --scenario-index N`, then `finalize`, ideally
  on `NuclearEnergy-dev` if local compute-node capacity is tight.
