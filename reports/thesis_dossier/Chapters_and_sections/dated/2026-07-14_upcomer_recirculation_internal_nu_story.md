---
provenance:
  - operational_notes/07-26/14/2026-07-14_PROJECT_MISSION_AND_SCIENTIFIC_QUESTIONS.md
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate/README.md
tags: [thesis-dossier, weekly-presentation, internal-nu, upcomer-recirculation, admission-rule]
related:
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-14_thesis_presentation_story_sync.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
task: AGENT-335
date: 2026-07-14
role: Thesis/Presentation/Documentation
type: report
status: complete
supersedes:
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-14_thesis_presentation_story_sync.md
superseded_by:
---
# Upcomer Recirculation / Internal-Nu Story Update - 2026-07-14

Purpose: make the thesis and weekly-presentation wording reflect the AGENT-330
internal-Nu result. The correct story is not just "Nu is blocked." The result
is that the currently admitted Salt2-4 upcomer regime is recirculating and
therefore cannot support fitted single-stream internal Nu.

## Thesis Claim

The admitted Salt2-4 upcomer evidence is a recirculating mixed-convection
regime, not ordinary pipe flow. The three admitted diagnostic points span
Re_upcomer `71.125-134.883`; all are classified as
`recirculation_cell_observed`, backflow fraction remains material
(`0.277778` down to `0.171875`), and Ri_median remains above one
(`1.497987-2.633785`).

That is a scientific result and an admission rule. It tells us how to name and
use the evidence: single-stream `Nu`, `f_D`, and `K` labels are invalid when the
upcomer has material recirculation/reverse flow. Use section-effective or
diagnostic labels, and keep those rows out of closure fitting.

## What Is Admitted

- Current upcomer observations are admissible as recirculation/regime evidence.
- They support a coefficient-naming rule: recirculating sections cannot be
  reduced to ordinary-pipe `Nu`, `f_D`, or `K` without overclaiming.
- They support the thermal gate decision that no internal Nu row is
  fit-admissible today.

## What Is Not Admitted

- No calibrated onset threshold is admitted.
- No transferable upcomer internal-Nu closure is admitted.
- No ordinary-pipe upcomer friction or loss coefficient is admitted from the
  current recirculating rows.
- No internal Nu residual may absorb heater realization, cooler/HX duty,
  passive loss, wall storage, branch mixing, radiation, or sign residuals.

## Presentation Wording

Say:

> We learned that the current admitted Salt2-4 upcomer regime is recirculating,
> not ordinary pipe flow. That makes fitted single-stream internal Nu invalid
> for these rows; it is a physics/admission result, not merely a failed Nu fit.

Also say:

> Onset remains uncalibrated because all admitted points are still
> recirculating. We need ordinary-pipe or transition anchors before reopening an
> upcomer internal-Nu fit gate.

Avoid:

> Nu is blocked.

That is too weak and hides the result. Use:

> Upcomer Nu is blocked for fitting because the admitted regime is recirculating
> and invalidates single-stream coefficient labels.

## Next Work

Next work is targeted evidence, not broad retelling:

- matched vector and thermal plane extraction at upcomer inlet, midpoint, and
  outlet;
- reverse area fraction, reverse mass fraction, secondary velocity fraction,
  mass-flux-weighted bulk temperature, wall temperature, local wallHeatFlux,
  Re, Pr, Ri, Ra/Gr, Gz, and exact time window on the same planes;
- candidate cases near Re `150`, `200`, and `250`;
- at least one ordinary-pipe or transition anchor before any calibrated onset
  or internal-Nu fit claim.
