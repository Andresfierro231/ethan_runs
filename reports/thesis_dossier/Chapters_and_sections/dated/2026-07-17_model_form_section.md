---
provenance:
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/Outline.md
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_current_context.md
  - operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md
  - operational_notes/07-26/15/2026-07-15_segment_resolved_pressure_thermal_modeling_plan.md
  - work_products/2026-07/2026-07-17/2026-07-17_salt2_pm5q_val_salt2_readiness_ledger/README.md
tags: [thesis-section, model-form, fluid-walls, cfd-to-1d, steady-state]
related:
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_modeling_approach_section.md
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_split_policy_section.md
  - reports/thesis_dossier/Outline.md
task: AGENT-497
date: 2026-07-17
role: Writer
type: thesis-section
status: draft
supersedes: []
superseded_by:
---
# Draft Thesis Section: Steady `fluid+walls` Model Form

## Section Role

This section belongs in the methodology and forward-model chapters. Its purpose
is to define the 1D model form used by the thesis before presenting closure
coefficients or scorecards. The current target is a steady, segment-resolved
`fluid+walls` model. That phrase is important: the loop is not treated as a
fluid-only pipe network with one fitted heat leak. Each segment carries both a
fluid state and a wall/material state, and the pressure, thermal, source/sink,
and admission information are kept in separate ledgers.

The model is steady-state in the present thesis scope. Transient wall storage
and heat-capacity terms are not part of the current predictive model unless a
later dated study explicitly reopens transient modeling. This choice matches the
current evidence base, which is built around terminal or final-window CFD
states, steady heat ledgers, and split-aware predictive scorecards.

## Segment State

The loop is decomposed into physical segments and branch regions. A segment is
not only a length of pipe; it is a modeling control volume with a declared
geometry, material stack, pressure model, thermal circuit, source or sink role,
and evidence status. A typical segment record should contain:

- branch and station mapping;
- length, diameter, elevation change, orientation, and local area;
- material stack, such as steel, insulation, quartz, connector, or junction;
- fluid property lane and local evaluation temperature;
- pressure model slot;
- thermal model slot;
- source/sink role: heater, cooler/HX, passive wall, test section, junction, or
  connector;
- boundary-layer/development and reset status;
- recirculation or invalid-single-stream flags;
- training, support, holdout, external-test, diagnostic, or blocked status.

The test section is retained as a physical region. It is the bare-quartz middle
span of the upcomer, not a removable compatibility term. In the 1D path it sits
between the lower and upper upcomer spans:

```text
left_lower_leg -> test_section_span -> left_upper_leg
```

This region may add heat to the salt through electrical deposition, lose heat to
ambient through quartz and external boundary layers, or do both. The sign of the
net term is therefore a result of the model, not an assumption.

## Fluid Energy Balance

For a steady segment, the fluid energy balance is written as a source/sink
ledger along the path coordinate `s`:

$$
\frac{d}{ds}\left[\dot{m} c_p(T) T\right]
= q'_{heater\to fluid,i}
- q'_{cooler,i}
- q'_{wall loss,i}
+ q'_{other,i}.
$$

The terms on the right-hand side are intentionally named by physical role. The
heater term represents setup-defined electrical-to-fluid heat addition, the
cooler term represents setup-defined heat removal by the cooler or heat
exchanger model, and the wall-loss term represents passive heat transfer from
the fluid/wall system to the surroundings. The `other` term is reserved for
documented local source/sink regions such as connectors, junctions, or
test-section effects. It should not be used as an untracked residual sink.

For a finite segment with approximately uniform properties, the same statement
can be expressed as:

$$
\dot{m}\,\bar{c}_{p,i}\left(T_{out,i}-T_{in,i}\right)
= Q_{heater,i}
- Q_{cooler,i}
- Q_{wall loss,i}
+ Q_{other,i}
+ Q_{residual,i}.
$$

The residual is an accounting result. It is not automatically a calibratable
closure coefficient. Before it can be assigned to internal convection, wall
loss, cooler performance, heater efficiency, or a junction model, the relevant
admission gates must be satisfied.

## Wall And External-Boundary Circuit

The ordinary wall-covered region uses a resistance-network interpretation:

```text
fluid bulk
  -> internal convection / thermal boundary layer
  -> pipe wall conduction
  -> insulation or local material layer
  -> external convection to ambient
  -> external radiation to surroundings
```

In compact form, a passive wall heat loss can be written as:

$$
Q_{wall loss,i}
= \frac{T_{drive,i}-T_{env,i}}{R_{int,i}+R_{wall,i}+R_{layer,i}+R_{ext,i}}.
$$

The drive temperature must be declared. It may be bulk fluid temperature, inner
wall temperature, pipe outer-wall temperature, or insulation outer-surface
temperature, depending on what the segment model and available data support.
Changing the drive temperature changes the meaning of the fitted or admitted
resistance. The thesis should therefore report the drive-temperature convention
with every wall-loss or `UA` value.

External radiation is part of the boundary network. In current CFD evidence, the
`rcExternalTemperature` boundary condition embeds emissivity and surrounding
temperature effects into the realized wall heat flux. A 1D replay that consumes
realized CFD `wallHeatFlux` should not add a second standalone radiation term.
For predictive modeling, radiation may be represented explicitly only through a
setup-only external boundary dictionary carrying quantities such as ambient
temperature, surrounding temperature, emissivity, external convection, and layer
resistance.

## Test-Section Heat Balance

The test-section model is a local source/loss circuit, not an omitted segment.
The draft steady form is:

$$
q'_{test\ section\to fluid}
= q'_{electrical\ deposition}
- \frac{T_{drive}-T_{external}}{R'_{quartz,external}}.
$$

The electrical deposition term may be assigned directly to the fluid or through
the quartz/wall stack depending on the implemented model. The second term is the
quartz-to-external loss path. The model must allow the net sign to change. If
the quartz/external loss exceeds local deposition, the test section can be a net
loss even when it is physically associated with heating hardware.

This is why diagnostic models that delete the test section are not final model
forms. They can identify how much error is associated with the region, but the
thesis-ready successor must include the physical segment with setup-only inputs.

## Pressure Model

The hydraulic model is also segment-resolved. The buoyancy drive is an integral
over the loop temperature, density, pressure, composition, and elevation field:

$$
\Delta p_{drive}
= \oint \rho\left(T(s),p(s),x,property\ lane\right) g\,dz(s).
$$

The pressure loss is a sum of local segment terms:

$$
\Delta p_{loss}
= \sum_i
\left[
f_i \frac{L_i}{D_i} q_i
+ K_i q_i
\right],
\qquad
q_i=\frac{1}{2}\rho_i V_i^2.
$$

The coefficient symbols are placeholders for model families, not universal
constants. The friction term may depend on Reynolds number, Prandtl number,
Richardson number, roughness, development length, and branch geometry. The
local-loss term may represent an isolated bend, a named fitting, a close-coupled
cluster, a junction, or a branch-apparent residual. These cases must not be
collapsed into one global `K` if the pressure taps or planes do not isolate the
feature.

Regions with material recirculation are not ordinary single-stream segments.
For those regions, the row can support recirculation diagnostics, onset
classification, or section-effective descriptions, but it should not be used to
fit ordinary single-stream `Nu`, `f_D`, or local `K` without an explicit
recirculation-aware model.

## Predictive Input Contract

A thesis-strength predictive model accepts setup information and returns
predicted mass flow and temperatures. Runtime inputs may include:

- geometry, branch map, and segment map;
- property mode;
- heater setup inputs;
- cooler/HX setup inputs;
- external boundary dictionary with `h`, `Ta`, `Tsur`, emissivity, wall/layer
  resistance, and drive-temperature selector where admitted;
- trained hydraulic and thermal coefficients from allowed training rows.

Runtime inputs must not include CFD `mdot`, realized CFD `wallHeatFlux`, imposed
CFD cooler duty, or validation temperatures. Any mode that uses those quantities
is diagnostic or replay evidence. It may explain model error, but it does not
qualify as a final predictive model.

## Draft Thesis Wording

The 1D model used in this thesis is a steady `fluid+walls` network. Each segment
is represented by a fluid state coupled to a wall or material stack and by
separate pressure, thermal, source/sink, and admission ledgers. This structure
is chosen because the CFD evidence shows that pressure loss, heat placement,
external boundary conditions, wall material, and recirculation can change the
meaning of an apparent closure coefficient. A single tuned friction factor,
Nusselt number, minor-loss coefficient, or heat-leak multiplier would obscure
these effects.

The model therefore treats closure as an auditable decomposition. Buoyancy is
computed from the loop density/elevation field, pressure losses are assigned to
segment-local distributed and local-loss terms, heat transfer is separated into
heater, cooler, passive wall, test-section, radiation, and residual lanes, and
each coefficient is labeled by its allowed evidence class. CFD-informed replay
quantities are used to diagnose model-form error, while final predictive modes
are restricted to setup-only runtime inputs.
