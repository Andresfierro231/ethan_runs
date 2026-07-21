---
task: AGENT-294
date: 2026-07-13
role: Writer
type: map
status: reference
tags: [thermal-parity, rcExternalTemperature, radiation, external-boundary]
related:
  - operational_notes/maps/README.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/forward-predictive-model.md
---

# Thermal Boundary & Radiation — Map of Content

Tags: #thermal-parity #rcExternalTemperature #radiation #external-boundary

## What this covers

The external thermal boundary contract of the Ethan Salt CFD cases — what the
custom `rcExternalTemperature` wall BC actually imposes (h, Ta, Tsur,
emissivity, layer thicknesses), whether radiation is present, and how the 1D
model must consume the CFD wall heat balance without double-counting. This is
the external-loss / boundary half of the thermal work; internal wall-adjacent
convection lives in `thermal-closures-and-internal-nu.md`.

## Current status

**ANTI-STALE HEADLINE:** The claim "CFD has no radiation" is SUPERSEDED as of
2026-07-13 (AGENT-277 / AGENT-287). The custom `rcExternalTemperature` wall BC
DOES include radiative exchange via `emissivity` and `Tsur`. Each admitted
mainline case (Salt 2/3/4) applies emissivity 0.95 on 36 `rcExternalTemperature`
patches with `Tsur = Ta` of 299.19 / 299.79 / 299.97 K respectively. Radiation
is inseparable inside the total OpenFOAM `wallHeatFlux` — there is no separate
`qr` term exported — so it cannot be split back out from the current CFD
outputs. Blocker `cfd-no-radiation-parity` is marked **superseded** in
`.agent/BLOCKERS.md`; the broader `thermal-cfd-1d-parity` blocker is resolved
narrowly by AGENT-452 because residual owners are separated and internal Nu is
kept out of boundary/source/storage cleanup.

2026-07-14 flow/temperature/BC response study: AGENT-351 consolidated existing
case-level setup BCs, time-series mdot/temperature aggregates, patch-role
boundary reductions, corrected-Q harvest status, and false-steady perturbation
provenance in
`work_products/2026-07/2026-07-14/2026-07-14_flow_rate_temperature_bc_response_study/`.
Use it when asking which boundary conditions were used and what flow-rate /
temperature results they produced. The package is observational: old Q
perturbations remain invalid false-steady provenance, and corrected-Q +/-5 rows
are terminal-harvested but split/BC-role pending.

2026-07-14 external-BC thermal-profile parity study: AGENT-365 built
`work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/`.
Use it for a thesis-ready statement of the external boundary/source contract,
the radiation/double-counting policy, and the leg-level 3D-vs-1D heat-release
diagnosis. It reports 207 patch contract rows, 24 segment-equivalent
external-boundary rows, 15 leg comparisons, and 15 wall/profile drive diagnostic
rows. It is diagnostic/model-form evidence only; it does not admit final
predictive-HX or internal-Nu closure.

2026-07-15 AGENT-413 update:
`work_products/2026-07/2026-07-15/2026-07-15_blocker_resolution_wave_implementation/`
recasts the Fluid external-boundary API blocker. External-boundary dictionaries
for `h`, `Ta`, `Tsur`, emissivity, source, and drive selector already exist, and
AGENT-413 adds a direct predictive HX `hx_ua_multiplier`. Remaining work is now
setup-only campaign validation and admission, not basic API availability.

2026-07-16 AGENT-452 update:
`work_products/2026-07/2026-07-16/2026-07-16_thermal_parity_resolution_gate/`
resolves `thermal-cfd-1d-parity` as a blocker to predictive thermal
continuation. The resolution is not a Nu fit: radiation metadata, passive wall
loss, cooler/HX removal, heater/source transfer, storage, and recirculation
remain separate residual owners.

2026-07-21 LitRev heat-loss contract alignment:
`work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/`
is the current external-boundary/`fluid+walls` heat-path contract. It separates
runtime inputs, forbidden inputs, outputs, and current blockers for heater,
internal `Nu`, wall conduction, contact/layer resistance, insulation/quartz,
external convection, radiation, jacket/cooler removal, storage, and residual
lanes. Use it before changing external-boundary dictionaries or predictive
wall-loss scoring; realized CFD `wallHeatFlux` remains diagnostic/scoring only.

2026-07-21 phased progress plan:
`operational_notes/07-26/21/2026-07-21_HEATLOSS_PHASED_PROGRESS_PLAN.md`
is the current board-backed sequence for heat-loss work. For this map, the key
ordering is Phase 1 before new wall/test-section scoring: external-boundary
dictionaries and radiation semantics must be executable and runtime-audited
before candidates consume them.

## Trusted results

- **rcExternalTemperature carries radiation.** emissivity 0.95, Tsur≈Ta per case
  (Salt 2/3/4 = 299.19 / 299.79 / 299.97 K), 36 patches each spanning
  `ambient_wall`, `heater`, `junction_other`, `test_section` roles.
  → `work_products/2026-07/2026-07-13/2026-07-13_cfd_radiative_boundary_guidance/`
- **Microcase sensitivity confirmed (OF13, AGENT-277).** Varying only emissivity
  or Tsur changes realized `wallHeatFlux`: emissivity 0.95→0.10 = −658.64 W,
  0.95→0.00 = −809.14 W; Tsur 299.19→350 K = +1912.50 W (final-time deltas,
  glass+roof patches combined). → `work_products/2026-07/2026-07-13/2026-07-13_rc_external_temperature_publication_evidence/`
- **Patch-role table (AGENT-263).** Per-patch boundary type, physical role,
  h/Ta/Tsur/emissivity, layer thicknesses, imposed heat, realized `wallHeatFlux`,
  admissibility flags. → `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/`
- **External boundary setup reference (human-readable).**
  → `reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/`

## Open / in-progress / blocked

- **RESOLVED — `thermal-cfd-1d-parity`.** AGENT-452 resolved the broad parity
  blocker for predictive thermal continuation by assigning residual owners and
  preserving the no-Nu-absorption rule. Internal Nu fitting, mesh/GCI, and
  branch recirculation gates remain separate constraints.
  → `work_products/2026-07/2026-07-16/2026-07-16_thermal_parity_resolution_gate/`
- **OPEN — `TODO-1D-RADIATION-CAPABILITY` (board row).** Forward/predictive 1D
  needs a radiation-capable external-loss model (emissivity + surroundings), or
  radiation-off runs must be explicitly labeled sensitivities.
- **OPEN — recover exact `rcExternalTemperature` C++ source** for
  publication-strength provenance. Audit concluded emissivity/Tsur are active and
  embedded in `wallHeatFlux` with no separate `qr`; source itself not yet found.

## Guardrails for 1D (do not lose)

- Radiation is inseparable inside total CFD `wallHeatFlux`; **do NOT add a
  separate 1D radiation term on top of CFD `wallHeatFlux`.**
- **Do NOT call a radiation-off replay "CFD parity"** — it is a sensitivity.
- For forward prediction from physical setup, include a radiation-capable
  external-loss model, or explicitly label radiation-off as a sensitivity.
- Thermal-parity ordering: match CFD external/source boundary contract → total
  heat balance → branch losses → station/probe temps → wall temps last. Realized
  CFD `wallHeatFlux` is diagnostic; imposed CFD inputs document setup. Parity
  BEFORE predictive fitting.
  → `operational_notes/07-26/10/2026-07-10_thermal_parity_roadmap.md`,
  `operational_notes/07-26/10/2026-07-10_NEXT_MEETING_START_HERE.md`

## Research avenues tried (outcome + provenance)

- **"CFD has no radiation" assumption** — DISPROVEN. Patch audit + OF13 microcase
  show emissivity/Tsur drive `wallHeatFlux`. → radiative_boundary_correction note
  + publication_evidence package (above).
- **Search for exact rcExternalTemperature source / separable `qr`** — source not
  located; no separate `qr` ledger exists. Radiation stays folded into total
  `wallHeatFlux`. → `2026-07-13_rc_external_temperature_publication_evidence/`
  (`source_probe.csv`, `publication_evidence_decision.json`).
- **AGENT-279 no-radiation replay** — retained only as a diagnostic sensitivity,
  NOT as CFD parity.

## Key artifacts (canonical)

- Correction note (decision + per-run values): `operational_notes/07-26/13/2026-07-13_cfd_radiative_boundary_correction.md`
- Agent-facing policy: `.agent/DECISIONS.md` (2026-07-13 entry)
- Blocker ledger: `.agent/BLOCKERS.md` (`cfd-no-radiation-parity` superseded; `thermal-cfd-1d-parity` resolved narrowly)
- Radiative boundary guidance: `work_products/2026-07/2026-07-13/2026-07-13_cfd_radiative_boundary_guidance/`
- Microcase publication evidence: `work_products/2026-07/2026-07-13/2026-07-13_rc_external_temperature_publication_evidence/`
- Patch-role table: `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/`
- Flow-rate / temperature / BC response study: `work_products/2026-07/2026-07-14/2026-07-14_flow_rate_temperature_bc_response_study/`
- External-BC thermal-profile parity study: `work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/`
- Blocker-resolution wave / Fluid HX hook: `work_products/2026-07/2026-07-15/2026-07-15_blocker_resolution_wave_implementation/`
- Thermal parity resolution gate: `work_products/2026-07/2026-07-16/2026-07-16_thermal_parity_resolution_gate/`
- LitRev thermal heat-loss contract alignment: `work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/`
- Heat-loss phased progress plan: `operational_notes/07-26/21/2026-07-21_HEATLOSS_PHASED_PROGRESS_PLAN.md`
- External boundary setup reference: `reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/`
- Parity roadmap + meeting starter: `operational_notes/07-26/10/2026-07-10_thermal_parity_roadmap.md`, `operational_notes/07-26/10/2026-07-10_NEXT_MEETING_START_HERE.md`

## Related

- `operational_notes/maps/README.md` — map index
- `operational_notes/maps/thermal-closures-and-internal-nu.md` — internal wall-adjacent convection (HTC, Nu, UA')
- `operational_notes/maps/forward-predictive-model.md` — forward 1D prediction (radiation-capable external loss)
