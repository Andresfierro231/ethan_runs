# 2026-07-10 Next Meeting: Start Here

Open this note first at the next Ethan thermal/CFD-1D meeting.

Tags: #thermal-parity #external-boundary #internal-nu #patch-role-table
#rcExternalTemperature #end-of-day #litrev-synthesis #research-pathways

## Related

- `operational_notes/07-26/10/2026-07-10_end_of_day_todo.md`
- `operational_notes/07-26/10/2026-07-10_thermal_parity_roadmap.md`
- `reports/2026-07/2026-07-09/2026-07-09_internal_nu_model_form_comparison/README.md`
- `reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/README.md`
- `operational_notes/07-26/13/2026-07-13_live_job_heartbeat_and_cleanup_call.md`
- `operational_notes/07-26/13/2026-07-13_litrev_synthesis_start_here.md`
- `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/README.md`

## First Files To Open

1. `operational_notes/07-26/10/2026-07-10_end_of_day_todo.md`
   - Short operational TODO.
   - Live-job follow-up.
   - What not to submit.

2. `operational_notes/07-26/10/2026-07-10_thermal_parity_roadmap.md`
   - Scientific roadmap for CFD-1D thermal parity.
   - Patch-level external boundary matching.
   - `rcExternalTemperature` emissivity/Tsur audit.
   - Diagnostic-to-predictive study ladder.

3. `reports/2026-07/2026-07-09/2026-07-09_internal_nu_model_form_comparison/README.md`
   - Paper-facing explanation of CFD internal heat transfer versus 1D internal
     Nu/HTC model forms.

4. `reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/README.md`
   - Current external boundary/setup reference and heat-source/sink summary.

5. `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/README.md`
   - Literature-review-derived lessons, model forms, things to try, and
     board-ready research pathways with author/title provenance.

## Next Meeting Agenda

1. Check terminal status for live jobs noted in the end-of-day TODO.
2. Do not submit a new thermal-parity compute job before the boundary audits.
3. Start the thermal parity program with a read-only patch-level boundary table.
4. Audit the actual `rcExternalTemperature` implementation before deciding
   whether 1D parity mode should include radiation.
5. Draft the 1D parity-mode specification before editing Fluid.
6. Use the lit-rev synthesis package to choose the next closure-ledger task:
   source-envelope table, property sensitivity, reset/named-loss extraction,
   heat-loss calibration, or CFD validity diagnostics.

## Thermal-Parity Priority

The top scientific priority is:

> Make the 1D external wall, insulation, ambient, heater, cooler, and
> test-section boundary/source contract match the CFD contract as closely as
> possible, then use the remaining section heat-loss mismatch to isolate the
> internal thermal-development problem.

Keep these distinctions explicit:

- realized CFD `wallHeatFlux` is diagnostic;
- imposed CFD inputs document setup;
- parity mode comes before predictive fitting;
- total heat balance comes before branch losses;
- branch losses come before station/probe temperatures;
- wall temperatures come last.

## First New Task To Claim

Suggested task name:

`thermal_boundary_patch_role_table`

Expected output:

- patch name
- case/source id
- boundary type
- physical role
- area if available
- mapped 1D segment/span
- `h`, `Ta`, `Tsur`, emissivity
- layer thicknesses and conductivity coefficients
- imposed heat term if present
- realized wallHeatFlux if available
- admissibility flags for ambient/heater/cooler/test-section/diagnostic roles

Do this before modifying the 1D model.

## Documentation Cross-References

Lightweight Obsidian-style cross-reference metadata has been added to this
thermal-parity documentation cluster by `AGENT-260`.

Recommended convention:

- Keep normal repo-relative markdown/file-path links as the primary references.
- Add a short `Related` block to durable notes and reports.
- Add stable topic tags in plain text, for example:
  `#thermal-parity`, `#external-boundary`, `#internal-nu`,
  `#patch-role-table`, `#rcExternalTemperature`, `#end-of-day`.
- Do not backfill the whole repo. Start with the current thermal-parity cluster
  and only extend the convention when a note becomes a durable reference.

Files included in the first pass:

- `operational_notes/07-26/10/2026-07-10_NEXT_MEETING_START_HERE.md`
- `operational_notes/07-26/10/2026-07-10_thermal_parity_roadmap.md`
- `operational_notes/07-26/10/2026-07-10_end_of_day_todo.md`
- `reports/2026-07/2026-07-09/2026-07-09_internal_nu_model_form_comparison/README.md`
- `reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/README.md`

## Do Not Lose This

The agreed modeling strategy is not "fit 1D temperatures until they match."
It is:

1. match CFD external/source boundary contract,
2. compare total and section heat transfer,
3. identify where bulk 1D temperature is not the right driving temperature,
4. build a physically motivated internal development / wall-adjacent
   temperature model,
5. use effective HTC only as a diagnostic or fallback where the physics cannot
   yet be defended.
