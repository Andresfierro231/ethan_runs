# T2 — True-steady REAL-insulation perturbation runs (Salt 2 Jin)

Date: `2026-07-01` · Owner: claude (AGENT-164) · Task: T2 (user-requested)
Node: c318-008.ls6.tacc.utexas.edu · idev job 3269598 · NuclearEnergy-dev · 256 cores
Runtime: OpenFOAM Foundation v13 (Intel-MPI campaign build) + libRCWallBC.so.

## Goal / why

The existing `loq_loins` / `hiq_hiins` Salt-Jin perturbation runs are (a) FALSE-
STEADY — mdot pinned at the nominal value (~−0.0132 kg/s for Salt 2) despite ±10 %
heater-power changes, i.e. restarted near the old fixed point and never re-
equilibrated (audit: `.agent/journal/2026-06-30/perturbation-run-convergence-audit.md`);
and (b) NOT actually insulation variants — only `Q` was changed; `insulated.h`
stayed 5.964. This task resubmits Salt 2 Jin as TRUE-STEADY + REAL-insulation runs.
Conservative start: Salt 2 Jin only, two variants; report before extending to 3/4.

## Insulation semantics (RECONCILED) + the naming ambiguity to confirm

Insulation in these cases is NOT a single `case_config` scalar. It is the external
convective HTC `h` on each pipe-wall segment, applied per-patch in `0/T` (and in
the restart field `processors64/<t>/T`) via the custom `rcExternalTemperature` BC,
together with `thicknessLayers` + `kappaLayerCoeffs` (steel + insulation layers).
`insulated.h`=5.964 in `case_config.yaml` is only a nominal summary, not the knob
the solver reads. The real per-segment h values (Salt 2, nominal):
- passive insulated pipe legs / junctions / fittings / extensions: h ≈ 3.4–7.1
  W/m²K (two `pipeleg_left_*_connector` are 17.6 — thin/uninsulated connectors);
- powered heater segments (`pipeleg_lower_04/05/06`), test section
  (`pipeleg_left_04`): carry `Q` + their own h — LEFT UNCHANGED (Q knob);
- bare-metal stub fins (`*_stub`, h ≈ 64–90) and cooler/reducer fixed-Q patches:
  LEFT UNCHANGED.

Physical convention I adopt (and it CONFLICTS with the master-TODO text):
> higher external h ⇒ more heat loss to ambient ⇒ colder wall, bigger wall–core
> ΔT ⇒ this is LESS insulation. Lower h ⇒ MORE insulation.

So physically **hiins ("high insulation") = LOWER h**, **loins = HIGHER h**. The
master-TODO §T2(b) text says the opposite ("hiins = higher h = more loss"), which
labels the variants by heat-loss level, not insulation level. To avoid any
ambiguity I named the run dirs by the ACTUAL knob direction:
- `salt2_jin_hiins_loH` = HIGH insulation = h × 0.5
- `salt2_jin_loins_hiH` = LOW insulation  = h × 2.0
**USER ACTION: confirm which ins-label convention to keep for the paper.** The
knob direction in the runs is unambiguous regardless.

Factor ±2× on h chosen so insulation is a real, independent 2nd knob (distinct
from the ±5–10 % Q perturbations) and large enough to move the wall ΔT and the
buoyancy head measurably at the coarse-mesh resolution.

The 32 scaled patches: junction_lower_left/right, junction_upper_right/left, the 7
junction_*_extension, pipeleg_lower_{01,02,03,07,08,09}, pipeleg_right_{01,02,03},
pipeleg_upper_{01,02,03,07,08,09}, pipeleg_left_{01,02,03,05,06,07}.

## Thermal-relaxation time τ and endTime (arithmetic)

Geometry: bore r=0.011049 m ⇒ A_bore=π r²=3.835e-4 m²; main-loop centerline
L≈3.748 m (friction package) ⇒ V_main=1.437e-3 m³; +15 % for stubs/fittings ⇒
V_loop≈1.653e-3 m³.
Props at ~447 K (Jin fits): ρ=2293.6−0.7497·T=1958.5 kg/m³; cp=1423.47 J/kgK.
Fluid mass m=ρV=3.238 kg; heat capacity C=m·cp=4608 J/K.

Two relaxation modes bracket the physics:
- fast advective mixing: UA_adv = ṁ·cp = 0.0132·1423.47 = 18.8 W/K
  ⇒ τ_adv = C/UA_adv ≈ 245 s (redistributes bulk enthalpy around the loop).
- slow ambient-coupling (governs the operating point): loop steady external loss
  ≈ cooler+reducers ≈ 136 W over ΔT≈(447−299)=148 K ⇒ UA_ext≈0.92 W/K
  ⇒ τ_ext = C/UA_ext ≈ 5015 s.

mdot is set by the buoyancy head from the FULL bulk-T field re-equilibrating
against wall/ambient losses ⇒ the governing constant is the slow mode τ_ext≈5000 s
(consistent with the audit note's "≫ the 2000–5000 s these advanced"). Set endTime
to ≈5 τ_ext past the restart:
  restart t=7915 s; 5·5000=25000 ⇒ endTime = 33000 s (≈5 τ_ext past restart;
  ≈100 τ_adv, so the fast mode is fully resolved). Monitors will be watched; the
  run can be stopped early once mdot has clearly moved from −0.0132 and plateaued.

## Staging (source untouched)

New dated dir: `jadyn_runs/modern_runs/2026-07-01_insulation_truesteady/`.
Per variant `runs/<v>/case_stage/<v>/`:
- copied: `0/`, `system/`, `constant/`, `dynamicCode/`, `case_config.yaml`, `case.foam`;
- `processors64/constant` → SYMLINK to source mesh (426 MB, read-only, shared);
- `processors64/7915/` → COPIED (restart latestTime) then `T` PATCHED.
Source continuation `jadyn_runs/.../2026-06-18_convergence_and_jin_envelope_wave/
runs/salt2_jin/case_stage/..._continuation` is READ-ONLY and untouched.

### BC diff (external h before → after), examples
| patch | nominal h | hiins ×0.5 | loins ×2.0 |
|---|---|---|---|
| pipeleg_lower_02_straight | 3.7684 | 1.8842 | 7.5368 |
| pipeleg_right_02_middle   | 3.4302 | 1.7151 | 6.8603 |
| pipeleg_left_02_connector | 17.6747 | 8.8374 | 35.3495 |
| junction_lower_left       | 4.3441 | 2.1721 | 8.6882 |
(all 32 targets scaled by the same factor; full list logged by the patcher.)
`case_config.yaml` insulated.h: 5.964 → 2.982 (hiins) / 11.928 (loins), plus an
`insulation_perturbation:` block recording knob/factor/restart/endTime.
Verified landed in BOTH `0/T` boundaryField AND the restart field, AND case_config.

### How the binary-collated restart T was edited safely
`processors64/7915/T` is `decomposedBlockData`: a binary container of 64 ASCII
processor blocks, each framed as `// ProcessorN\n\n<byteCount>\n( <ascii> )`. The
external h lives in each block's boundaryField as
`h { type uniform; value <X>; }`. A naive string edit would desync `<byteCount>`.
Script `scratchpad/edit_T_h.py` parses the framing, scales h only for the 32
target patches inside each block, recomputes each block's byte count, and rewrites
the count — round-trip framing verified (64 blocks, every declared count lands
exactly on `)`).

## Launch (background, NOT sbatch)

Launcher: `2026-07-01_insulation_truesteady/launch_variant.sh <case_dir> <ncores>
<offset>` — sources the campaign Intel-MPI OF13 env (`.../2026-06-02_runtime_
recovery/scripts/of13-env.sh`, the runtime that produced these fields), prepends
libRCWallBC.so, then `ibrun -o <offset> -n 64 foamRun -parallel`.

- hiins: `ibrun -o 0  -n 64` ; log `runs/salt2_jin_hiins_loH/.../logs/log.foamRun_insulation`
- loins: `ibrun -o 64 -n 64` ; log `runs/salt2_jin_loins_hiH/.../logs/log.foamRun_insulation`
Two ibrun trees, 128 of 256 cores used. Live PIDs at handoff: hiins ibrun 3064212,
loins ibrun 3067260 (foamRun ranks under hydra_pmi_proxy children).

### Validation before the real launch
Ran hiins with a temporary tiny endTime (7917 s): confirmed the patched collated
T reads, `rcExternalTemperature` (libRCWallBC.so) constructs WITHOUT segfault, and
the solver advances from 7915 with clean converging residuals
(p_rgh/U/h Initial residuals ~1e-5, continuity ~1e-8). Restored endTime=33000 and
launched both for real. Both confirmed advancing (hiins ~7916.8 s, loins ~7915.3 s
shortly after launch).

## Acceptance still to check (next session)
1. mdot moves off nominal −0.0132 by ~Q-independent buoyancy response to the h
   change and re-plateaus (operating-point convergence, the T3 gate).
2. hiins vs nominal shows SMALLER wall–core ΔT (more insulation) and loins LARGER.
3. hiins and loins mdot differ from each other and from nominal.
Only after (1)–(3): extend to Salt 3/4 Jin, then feed T3/T10.

## Files (AGENT-164 scope)
- staging + launcher: `jadyn_runs/modern_runs/2026-07-01_insulation_truesteady/**`
- board row AGENT-164; `.agent/status/2026-07-01_AGENT-164.md`; this journal.
- helper (scratch): `edit_T_h.py`.
- NOTE: took ID AGENT-164 — prompt said AGENT-163 but that row was already claimed
  by codex (postprocessing-rom-honesty-audit); avoided the collision.
