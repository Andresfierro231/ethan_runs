---
provenance:
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_model_form_section.md
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_current_context.md
  - operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md
  - operational_notes/07-26/15/2026-07-15_segment_resolved_pressure_thermal_modeling_plan.md
tags: [thesis-section, current-section, model-form, fluid-walls, steady-state]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/01_modeling_approach.md
  - reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md
task: AGENT-502
date: 2026-07-17
role: Writer
type: thesis-section
status: current-draft
supersedes:
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_model_form_section.md
superseded_by:
---
# Steady `fluid+walls` Model Form

## Definition

The final 1D target model is a steady `fluid+walls` network. Each segment
carries a fluid state coupled to a wall or material stack, plus separate
pressure, thermal, source/sink, boundary, and admission ledgers. This replaces a
fluid-only model with a fitted heat leak.

The present thesis scope is steady-state. Wall storage and transient
heat-capacity terms are future work unless a later study reopens transient
modeling.

## Segment Record

A segment record should include:

- branch and station mapping;
- length, diameter, elevation change, orientation, and area;
- wall/material stack such as steel, insulation, quartz, connector, or junction;
- fluid property lane;
- pressure model slot;
- thermal circuit slot;
- source/sink role;
- boundary-layer, development, and reset status;
- recirculation or invalid-single-stream flags;
- evidence class and uncertainty status.

The test section is retained as the bare-quartz middle span of the physical
upcomer:

```text
left_lower_leg -> test_section_span -> left_upper_leg
```

It is not a deleted or hidden model region. Its net heat effect is computed from
electrical deposition and quartz/external loss.

## Fluid Energy Balance

For a steady segment,

$$
\frac{d}{ds}\left[\dot{m} c_p(T)T\right]
= q'_{heater\to fluid,i}
- q'_{cooler,i}
- q'_{wall loss,i}
+ q'_{other,i}.
$$

For a finite segment,

$$
\dot{m}\bar{c}_{p,i}(T_{out,i}-T_{in,i})
= Q_{heater,i}
- Q_{cooler,i}
- Q_{wall loss,i}
+ Q_{other,i}
+ Q_{residual,i}.
$$

The residual is not itself a closure. It is the remaining imbalance after
declared source and sink lanes are evaluated.

## Wall And Boundary Circuit

Ordinary wall-covered regions use a thermal-resistance path:

```text
fluid bulk
  -> internal convection / thermal boundary layer
  -> pipe wall conduction
  -> insulation or local material layer
  -> external convection to ambient
  -> external radiation to surroundings
```

A compact passive wall-loss form is:

$$
Q_{wall loss,i}
=
\frac{T_{drive,i}-T_{env,i}}
{R_{int,i}+R_{wall,i}+R_{layer,i}+R_{ext,i}}.
$$

The drive temperature must be reported: bulk fluid, inner wall, pipe outer wall,
or insulation outer surface. Changing this drive changes the meaning of the
admitted `UA`, `hA`, or resistance term.

Radiation is part of the external boundary network. In current CFD evidence,
`rcExternalTemperature` embeds emissivity and surrounding-temperature effects in
the realized wall heat flux. A 1D replay using realized CFD `wallHeatFlux`
should not add a second radiation term. A predictive model should instead use a
setup-only external boundary dictionary if radiation is represented explicitly.

## Test-Section Balance

The test-section source/loss term is:

$$
q'_{test\ section\to fluid}
= q'_{electrical\ deposition}
- \frac{T_{drive}-T_{external}}{R'_{quartz,external}}.
$$

The model must allow either sign. If quartz/external loss exceeds local
deposition, the test section can be a net sink even though it is associated
with heating hardware.

## Pressure Model

Buoyancy is integrated over the loop field:

$$
\Delta p_{drive}
= \oint \rho(T(s),p(s),x,\mathrm{property\ lane}) g\,dz(s).
$$

Losses are segment-local:

$$
\Delta p_{loss}
= \sum_i
\left[
f_i\frac{L_i}{D_i}q_i
+ K_i q_i
\right],
\qquad
q_i=\frac{1}{2}\rho_iV_i^2.
$$

The coefficient symbols are model slots, not universal constants. The local
loss may be an isolated component, a close-coupled cluster, a junction term, or
a branch-apparent residual depending on plane placement and flow validity.

## Predictive Input Contract

Permitted runtime inputs are setup-known quantities: geometry, property mode,
heater inputs, cooler/HX inputs, external boundary dictionaries, and admitted
closure coefficients trained only on allowed rows. Prohibited runtime inputs are
CFD `mdot`, realized CFD `wallHeatFlux`, imposed CFD cooler duty, validation
temperatures, and held-out pressure or heat targets.
