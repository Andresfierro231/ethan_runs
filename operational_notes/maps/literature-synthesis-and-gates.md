---
task: AGENT-294
date: 2026-07-13
role: Writer
type: map
status: reference
tags: [litrev-synthesis, closure-ledger, source-envelope, property-sensitivity]
related:
  - operational_notes/maps/README.md
  - operational_notes/maps/friction-closures.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - reports/2026-07/2026-07-22/2026-07-22_litrev_latest_modeling_handoff/README.md
---
# Literature Synthesis & Gates — Map of Content

Tags: #litrev-synthesis #closure-ledger #source-envelope #property-sensitivity

## What this covers
What the HITEC closure literature review implies for the TAMU molten-salt loop
1D model, and the five diagnostic **gates** that must clear before any closure is
promoted. The central finding: the literature does **not** support one global
friction factor, one global Nusselt number, or one global heat-loss UA. It
supports a **branchwise closure ledger** — each branch/section carried with its
own reset history, local properties, source envelope, pressure/velocity basis,
heat-transfer state, heat-loss path, and residual. Reference limits, active
closures, diagnostic gates, sensitivity models, method sources, and residuals are
kept **separate**. Companion maps: friction-closures (candidate f forms) and
thermal-closures-and-internal-nu (candidate Nu forms). Provenance for literature
is by **author/title**, because citation numbers change.

## Current status (one paragraph)
The synthesis (AGENT-282) and its start-here index (AGENT-285) are complete, and
all **five gate packages** were implemented 2026-07-13 (AGENT-288 campaign
index). The gates exist and are populated but are **planning/diagnostic
artifacts, not validated models** — no new closure has been calibrated through
them yet. The five `TODO-LITREV-*` BOARD rows are deliberately unclaimed; a
future worker claims one at a time. The consume order is source-envelope →
property-sensitivity → reset/named-losses → heat-loss-calibration →
CFD-validity-diagnostics. Concurrent model default already moved to `salt_jin` to
match CFD (property lane locked before calibration). The 2026-07-21 new-LitRev
extraction adds the next model-form dispatch layer: six reduced model candidates,
pressure/corner extraction rules, CFD postprocessing contract fields, and
assignable next-agent lanes, while keeping all closures non-admitted.
The 2026-07-22 latest-LitRev handoff adds the current Ethan-facing synthesis:
14 requested research threads, MF-01 through MF-06 model forms, pressure/energy
ledgers, property hierarchy, branch consequences, negative lessons, and the
case-by-segment admission-engine target.

## Trusted results
- **Branchwise closure ledger** is the governing architecture (not a global
  f/Nu/UA). Keep reference limits, active closures, gates, sensitivities, method
  sources, and residuals separate. → lessons README (below).
- **Five gates implemented** (consume order):
  1. **Source envelope** — 90 branch rows + 360 source-overlap rows; Chen 2017
     checked vs audited ranges; Tian 2024 reference-only for laminar TAMU. →
     `work_products/2026-07/2026-07-13/2026-07-13_litrev_source_envelope/`
  2. **Property sensitivity** — 90 branch + 15 mode rows (Reis/Jadyn, Sohal/Janz,
     Jin+Parida+Santini, Jin+1560+0.60, Shen); no calibration before property
     lane is chosen; 1D default now `salt_jin`. →
     `work_products/2026-07/2026-07-13/2026-07-13_litrev_property_sensitivity/`
  3. **Reset & named losses** — 33 reset rows + 33 named pressure-loss rows
     (straight / component-K / cluster-K / branch-apparent); no global friction
     multiplier. → `work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/`
  4. **Heat-loss calibration** — 207 heat-path + 18 admission rows; jacket/cooler,
     passive convection, rcExternalTemperature radiation, heater input,
     wall/storage, residual kept separate; internal Nu blocked from absorbing
     external heat loss. → `work_products/2026-07/2026-07-13/2026-07-13_litrev_heat_loss_calibration/`
  5. **CFD validity diagnostics** — 18 section-validity rows + 54
     coefficient-naming rows; universal K/f_D/Nu names rejected where
     section-effective or diagnostic. →
     `work_products/2026-07/2026-07-13/2026-07-13_litrev_cfd_validity_diagnostics/`
- **Boundary/HX/wall/radiation model-form decision table** — compact downstream
  table produced 2026-07-14 (AGENT-314). It separates property lanes from
  friction/thermal fitting and marks sources as admitted, sensitivity-only,
  reference-only, or rejected with author/title provenance. →
  `work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/`
- **Research-studies roadmap and today-start package** — AGENT-518 turns the
  LitRev pathways plus current F6/wall/segment blockers into a ranked study
  matrix, today-start ledger, multi-agent campaign sequence, thesis roadmap, and
  tomorrow handoff without changing solver/admission state. →
  `work_products/2026-07/2026-07-17/2026-07-17_research_studies_roadmap_and_today_start/`
- **LitRev gate carryforward ledger** — AGENT-521 converts source-envelope,
  property-mode, reset/named-loss, heat-loss, and CFD-validity outputs into
  required columns and default blocked/diagnostic statuses for future F6,
  pressure-loss, HTC, CFD-reduction, wall-model, and final-scorecard packages. →
  `work_products/2026-07/2026-07-17/2026-07-17_litrev_gate_carryforward_ledger/`
- **Source-envelope/property carryforward labels** — AGENT-538 narrows the
  carryforward requirement to the two labels future closure scorecards most
  easily drop: source-validity envelope and property-mode sensitivity. It emits
  row labels, scorecard-contract checks, conservative Salt1/perturbation/future
  coverage gaps, blocker labels, and next research paths without admitting a
  closure. →
  `work_products/2026-07/2026-07-18/2026-07-18_source_envelope_property_carryforward/`
- **Source/property label enforcement** — AGENT-546 turns the carryforward
  labels into a strict scorecard audit. It scans current post-litrev closure
  scorecard/admission/fit/gate CSVs, detects fit/admission candidate rows,
  fills or synthesizes the five required labels, and blocks rows where coverage
  is missing or the label content itself says refresh/blockage is required.
  Acceptance result: `1110` candidate rows, `0` enforced rows with blank
  required labels, and `0` rows allowed through the source/property gate. →
  `work_products/2026-07/2026-07-18/2026-07-18_source_property_label_enforcement/`
- **Reusable source/property gate tooling** — AGENT-554 promotes the AGENT-546
  policy into `tools/agent/source_property_gate.py` and warning-mode
  `finish_task.py` enforcement. Future scorecard-like CSVs now surface
  `SOURCE_PROPERTY_GATE_WARNING` messages with failure-mode counts and a TODO
  command instead of silently closing with unlabeled or blocked fit/admission
  rows. Current final-scorecard TODO ledger →
  `work_products/2026-07/2026-07-20/2026-07-20_source_property_gate_infrastructure/final_scorecard_source_property_todo.csv`
- **Blocker / research-path / next-step synthesis** — AGENT-539 turns the
  current blocker register plus July 18 UMX1, TP/TW, source-property, and
  two-tap endpoint packages into a verified open-blocker list, viable research
  paths, ordered next-step queue, acceptance signals, and guardrails. UMX1 is
  carried as an API implementation path, not a score-grid path, until a real
  Fluid hook exists. →
  `work_products/2026-07/2026-07-18/2026-07-18_blocker_research_path_next_step_synthesis/`
- **New LitRev model-form extraction** — TODO-LITREV-MODEL-FORM-EXTRACTION-2026-07-21
  extracts the revised standalone LitRev into source inventory, six candidate
  model forms, pressure/corner findings, a CFD postprocessing contract, and a
  next-agent task matrix. It clarifies that static pressure recovery or
  source-defined negative junction coefficients are naming/basis issues until
  hydrostatic, kinetic, straight/developing, recovery, recirculation, and
  uncertainty gates pass. →
  `work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/`
- **Latest LitRev modeling handoff** — TODO-LITREV-LATEST-MODELING-HANDOFF-2026-07-22
  summarizes the newest source-audited litrev for Ethan model work and points
  later agents to the model-form hierarchy, active equations, source gates,
  branch consequences, and next implementation order. →
  `reports/2026-07/2026-07-22/2026-07-22_litrev_latest_modeling_handoff/README.md`

## Gate discipline (the rule)
- source-envelope overlap **before** using a source-bounded correlation;
- property sensitivity **before** fitting residuals;
- reset/named-loss **before** global friction calibration;
- separated heat-loss calibration **before** internal Nu tuning;
- invalid-single-stream CFD diagnostics **before** exporting section coefficients.

## Model forms to carry forward (from lessons README)
Pressure ledger (`dp = hyd + kin + dist_dev + minor + reset + transient + res`);
named property modes P0/P1..; `f_D = 64/Re` **reference only**; developing
`fRe(L+)` from reset distance; pressure-derived section loss (`f_D,Δp` / `K_Δp`);
`K(Re, geometry, split, pressure_basis, velocity_basis)`; forced-developing Nu
(Muzychka-Yovanovich); low-Re molten-salt mixed Nu (Chen 2017, **conditional** on
envelope overlap); heat-loss resistance network (VDI Heat Atlas); CFD-invalidity
flags (reverse area/mass, secondary-velocity fraction); ROM (future).

## Open / in-progress / blocked
- **Five `TODO-LITREV-*` BOARD rows** — OPEN, unclaimed; claim one at a time.
- **Tier 2 (next modeling):** Chen 2017 conditional overlap test; branchwise
  internal-HTC bakeoff; TAMU fitting inventory + `K_source_status`;
  reset-distance map + developing-pressure-loss bakeoff; radiation bound;
  invalid-single-stream CFD diagnostics on every reduction.
- **Tier 3 (experimental/longer):** pressure taps around fitting clusters;
  wall/surface/coolant-temp instrumentation; transient extension
  (Welander/Creveling/Vijayan); ROM archive-design (store snapshot fields now).
- All Tier 2/3 provenance is in `research_pathways.csv` (author/title + gates).

## Research avenues tried (outcome + provenance)
- **Global f / Nu / UA** — REJECTED by the review; replaced by the branchwise
  ledger. A match in total mdot or total heat removal is insufficient if it hides
  hydrostatic, fitting, heat-loss, or property error in the wrong coefficient. →
  lessons README, Main Takeaway.
- **Fully-developed 64/Re & FD Nu as defaults** — DEMOTED to reference/diagnostic
  columns (Shah & London; Shah entry-length; Muzychka-Yovanovich).
- **Chen 2017 low-Re mixed Nu as active closure** — CONDITIONAL only; usable per
  branch **iff** Re/Pr/Gr/Gz/(L/D)/BC overlap Chen's envelope (gate 1).
- **HITEC-specific ⇒ TAMU-active** — REJECTED as automatic; square-tube,
  turbulent, or horizontal-cooling sources (Chen multi-sided, Yang inclined, Tian
  cooled) stay diagnostic, not promoted into low-Re circular-pipe closures.
- **Property lane** — Jin viscosity + Parida/Basu cp are candidates/sensitivities,
  NOT the Reis/Jadyn replication mode; mixing modes breaks provenance. Default
  moved to `salt_jin` (matches CFD).

## Key artifacts (canonical)
- Lessons + pathways (main narrative): `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/`
  (README.md, `research_pathways.csv`, `summary.json`)
- Start-here index: `operational_notes/07-26/13/2026-07-13_litrev_synthesis_start_here.md`
- Campaign index (five gates tie-together): `work_products/2026-07/2026-07-13/2026-07-13_litrev_todo_campaign_index/`
- Gate 1 source envelope: `work_products/2026-07/2026-07-13/2026-07-13_litrev_source_envelope/`
- Gate 2 property sensitivity: `work_products/2026-07/2026-07-13/2026-07-13_litrev_property_sensitivity/`
- Gate 3 reset & named losses: `work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/`
- Gate 4 heat-loss calibration: `work_products/2026-07/2026-07-13/2026-07-13_litrev_heat_loss_calibration/`
- Gate 5 CFD validity diagnostics: `work_products/2026-07/2026-07-13/2026-07-13_litrev_cfd_validity_diagnostics/`
- Boundary/HX/wall/radiation model-form decision table:
  `work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/`
- Research-studies roadmap and today-start package:
  `work_products/2026-07/2026-07-17/2026-07-17_research_studies_roadmap_and_today_start/`
- LitRev gate carryforward ledger:
  `work_products/2026-07/2026-07-17/2026-07-17_litrev_gate_carryforward_ledger/`
- Source-envelope/property carryforward labels:
  `work_products/2026-07/2026-07-18/2026-07-18_source_envelope_property_carryforward/`
- Blocker / research-path / next-step synthesis:
  `work_products/2026-07/2026-07-18/2026-07-18_blocker_research_path_next_step_synthesis/`
- Latest LitRev modeling handoff:
  `reports/2026-07/2026-07-22/2026-07-22_litrev_latest_modeling_handoff/README.md`

## Related
- `operational_notes/maps/README.md` — MOC index
- `operational_notes/maps/friction-closures.md` — candidate f forms (gates apply)
- `operational_notes/maps/thermal-closures-and-internal-nu.md` — candidate Nu forms (gates apply)
- `.agent/BOARD.md` — `TODO-LITREV-*` rows (source-envelope, property-sensitivity, reset-named-losses, heat-loss-calibration, cfd-validity-diagnostics)
- `reports/thesis_dossier/README.md` — living weekly-presentation and thesis
  synthesis hub for turning the literature gates into thesis structure and
  presentation-ready claims.
