---
provenance:
  - operational_notes/07-26/21/2026-07-21_THESIS_CSEM_BOARD_DISPATCH.md
  - reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
  - reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md
  - reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md
  - reports/thesis_dossier/figures/README.md
  - reports/thesis_dossier/figures/figure_claim_crosswalk.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_csem_enrichment_writing_pass/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_diagnostic_evidence_integration/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/model_form_candidates.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_seeded_heat_path_lane_release/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/README.md
tags: [thesis-section, current-section, csem, fluid-walls, model-form]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md
  - reports/thesis_dossier/Chapters_and_sections/current/16_ch3_csem_cfd_evidence_database.md
  - reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md
task: TODO-THESIS-CH5-CSEM-FLUID-WALLS-DRAFT
date: 2026-07-21
role: Writer/Reviewer/Thermal-modeling/Hydraulics
type: thesis-section
status: current-draft
supersedes: []
superseded_by:
---
# Steady `fluid+walls` Model

## Chapter Claim

The target reduced model is a steady `fluid+walls` network. It is not a
fluid-only energy balance with one fitted heat leak, and it is not a single
global pressure multiplier. Each loop segment owns a fluid state, a wall or
material stack, pressure and thermal model slots, source/sink roles,
recirculation flags, uncertainty state, and admission status.

This chapter supports CL-02, CL-03, CL-17, and CL-18. It defines the model
architecture used by later closure-admission and results chapters.

## Segment State

A segment record should include:

| Field | Purpose |
| --- | --- |
| Branch and station map | Connects CFD reductions, sensor positions, and 1D control volumes. |
| Geometry | Length, diameter, area, elevation change, and orientation. |
| Material stack | Steel, insulation, quartz, connector, junction, or other local role. |
| Fluid property lane | Defines density, viscosity, heat capacity, conductivity, and derived groups. |
| Pressure slot | Distributed, developing/reset, local feature, junction/cluster, recirculation, or residual. |
| Thermal slot | Heater, cooler/HX, passive wall, test-section, junction/stub, radiation/external, or residual. |
| Boundary-layer and reset state | Records whether ordinary fully developed assumptions are appropriate. |
| Recirculation flag | Prevents ordinary one-stream coefficient labels where reverse flow is material. |
| Admission state | Separates admitted, partial, diagnostic, blocked, and missing quantities. |

The segment atlas in `09_fluid_walls_segment_atlas.md` is the current
implementation bridge. It should appear in this chapter as a table or as the
companion loop-region atlas figure:

`reports/thesis_dossier/figures/svg/F01_fluid_walls_loop_segment_atlas.svg`

## Architecture-To-Admission Interface

The `fluid+walls` model form should be described as an interface between CFD
evidence and predictive closure use. The architecture contains slots even when
the coefficient behind a slot is not yet admitted. That distinction lets the
thesis name missing physics without hiding it in the nearest available
multiplier.

| Model slot | What the slot records | Current admission stance |
| --- | --- | --- |
| External boundary dictionary | `h`, `Ta`, `Tsur`, emissivity, wall/layer resistance, and drive-temperature selector by role. | Contract ready; first-class Fluid source integration remains separate. |
| Heat-path lane | Heater, cooler/HX, passive wall, test section, junction/stub, radiation/external, residual. | Split evidence ready; wall/test-section closure still blocked. |
| Pressure source-envelope lane | Straight/developing, section/cluster, component, recirculation-effective, unresolved. | Diagnostic/non-admitted for current corner/F6 rows. |
| Recirculation lane | Reverse-flow/onset metrics and throughflow-plus-exchange variables. | Diagnostic evidence ready; exchange-cell and ordinary upcomer closures not admitted. |
| Source/property lane | Property mode, source envelope, source-use category, provenance author/title. | Required release gate before freeze. |

This interface is what makes the model useful before the final scorecard
exists. It defines where future evidence will attach and prevents current
diagnostic evidence from being mistaken for admitted predictive closure.

## Recirculation Guard Interface

The recirculation lane is now a completed diagnostic guard, not a fitted
closure. The S4 package reviewed `90` ordinary single-stream candidates and
disabled ordinary closure language for the upcomer-left vertical,
downcomer-right vertical, heater lower leg, and cooling upper leg. It admitted
`0` ordinary upcomer `Nu/f_D/K` rows, `0` exchange-cell coefficients, and `0`
scoreable-now rows.

That result belongs in the model architecture because it defines what the
`fluid+walls` interface must carry forward. RAF/RMF/SVF and energy-residual
diagnostics can mark a segment as recirculation-effective and can attribute
missing exchange physics, but they cannot be passed to Fluid as runtime inputs
or relabeled as ordinary friction, internal heat-transfer, or local-loss
coefficients. The future throughflow-plus-recirculation lane remains a variable
contract: `V_recirc`, `mdot_exchange`, `tau_recirc`, `T_main/T_recirc`,
same-window pressure/thermal residuals, and same-QOI uncertainty must exist
before an exchange cell can be calibrated or scored.

## Seeded Exchange-CV Path

The next upcomer model-form step is now more concrete than a qualitative
recirculation caveat. The S13 seeded surface/input manifest releases an
input-ready exchange-CV scaffold for Salt2, Salt3, and Salt4: each case has
`38880` seeded CV cells, `38880` seeded internal interface faces, `38880`
trusted wall faces, a released wall/core band, a released normal convention,
an existing cell VTK, an existing cell-volume CSV, and static source/sink
context. This is enough to define where later sampled exchange variables will
attach in the `fluid+walls` architecture.

The scaffold is still not sampler readiness or closure admission. The manifest
reports `0/3` sampler-manifest-ready rows because raw sampled interface/wall
VTKs, `Q_wall_W`, same-window sampler outputs, and same-QOI uncertainty remain
absent. The follow-on S13 heat-path lane release also fail-closes the current
source-side release: it records `6` heat-path lanes and upstream surface VTK
validation, but `0` `Q_wall_W` release rows, `0` source-side heat-path release
rows, `0` same-window thermal release rows, and `0` sampler
refresh/harvest/UQ allowed rows. The model-form conclusion is therefore a
clean interface, not an admitted exchange cell.

The matched Salt upcomer velocity figures should be paired with this scaffold.
The four-case `side_z` image package supplies both signed `U_y` arrows and
resultant `|U|` arrows using common color and glyph ranges. It shows why the
upcomer needs a throughflow-plus-exchange lane and why ordinary single-stream
upcomer `Nu`, `f_D`, or `K` language remains disabled. The visual evidence is
diagnostic only; it may motivate the exchange-CV architecture but may not be
used as a runtime input or coefficient.

## Fluid Energy Balance

For a steady segment, the fluid energy balance can be written as

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

The residual is an accounting lane. It is not automatically internal
convection, passive wall loss, heater inefficiency, cooler error, radiation, or
storage. It can become a named model term only after the corresponding source
and admission gates pass.

## Wall And External Boundary Circuit

Ordinary wall-covered regions use a resistance path:

```text
fluid bulk
  -> internal convection / thermal boundary layer
  -> pipe wall conduction
  -> insulation or local material layer
  -> external convection to ambient
  -> external radiation to surroundings
```

A compact wall-loss statement is

$$
Q_{wall loss,i}
=
\frac{T_{drive,i}-T_{env,i}}
{R_{int,i}+R_{wall,i}+R_{layer,i}+R_{ext,i}}.
$$

The drive temperature must be named. A `UA`, `hA`, or resistance fitted with
bulk-fluid drive is not the same closure as one fitted with inner-wall,
outer-wall, or insulation-surface drive. Radiation is part of the external
boundary network. Current realized CFD wall heat flux already includes the
`rcExternalTemperature` radiation and surrounding-temperature behavior, so a 1D
replay using realized CFD `wallHeatFlux` must not add a second radiation term.
A predictive model should instead use setup-facing external-boundary inputs
such as `Ta`, `Tsur`, emissivity, and wall/layer resistance.

The CSEM UQ/Fluid readiness addendum makes this interface more concrete:
external-boundary dictionaries are now a runtime setup interface, not a
realized CFD wall-flux replay. The current Fluid smoke evidence supports the
mechanism-level claim that role rows can carry external `h`, ambient and
surroundings temperature, emissivity, area/coverage, and drive-temperature
selectors into the setup contract. It does not claim a full-loop predictive
temperature score, a held-out score, or an external-test result.

## Test-Section Balance

The test section is retained as the bare-quartz middle upcomer span. It is a
physical region in the model, not a cleanup term to hide inside passive heat
loss. Its net source/loss can be written as

$$
q'_{test\ section\to fluid}
= q'_{electrical\ deposition}
- \frac{T_{drive}-T_{external}}{R'_{quartz,external}}.
$$

The term must allow either sign. The test section can be a local heat source
or a local sink depending on electrical deposition, quartz/external loss, drive
temperature, and surrounding boundary conditions.

## Pressure Balance

The hydraulic model balances loop buoyancy against segment-local loss:

$$
\Delta p_{drive}
= \oint \rho(T(s),p(s),x,\mathrm{property\ lane})g\,dz(s),
$$

and

$$
\Delta p_{loss}
= \sum_i
\left[
f_i\frac{L_i}{D_i}q_i
+ K_iq_i
\right],
\qquad
q_i=\frac{1}{2}\rho_iV_i^2.
$$

The coefficient symbols are model slots. Depending on evidence quality, a slot
may represent an ordinary distributed loss, a developing-flow correction, a
component loss, a section or cluster loss, a branch-apparent residual, or a
recirculation-aware section-effective residual. The current two-tap corner
evidence does not admit ordinary component `K`, so the model must preserve
diagnostic labels until later pressure gates pass.

## Relationship To LitRev Model Forms

The July 21 LitRev extraction provides a useful model-form inventory:

- gated single-stream developing branches;
- section or cluster `K` with recirculation diagnostics;
- signed-flow junction networks;
- throughflow plus recirculation exchange cells;
- period-averaged unsteady fitting losses;
- CFD-derived compartment or ROM hybrids.

The current thesis model uses these as architecture candidates and gates, not
as new admissions. All candidate model forms in that extraction are labeled
`not admitted here`. The `fluid+walls` model should therefore expose the
necessary slots and metadata without pretending that every slot already has an
admitted coefficient.

## Predictive Runtime Contract

A final predictive `fluid+walls` model may use setup-known quantities and
admitted coefficients:

- geometry and segment map;
- property lane;
- heater setup model;
- cooler/HX setup model;
- external boundary dictionary;
- admitted pressure and thermal coefficients trained only on legal rows.

It may not use CFD `mdot`, realized CFD `wallHeatFlux`, imposed CFD cooler
duty, validation TP/TW or branch temperatures, realized test-section heat, or
scored-row pressure/heat targets at runtime.

For the present thesis status, the predictive runtime contract is active as a
guardrail rather than a final score. Runtime setup dictionaries may describe
geometry, material stacks, property lane, heater/cooler setup inputs, and
external-boundary fields. The same contract rejects residual fills, realized
wall heat flux, CFD mass flow, imposed cooler duty, realized test-section heat,
validation temperatures, holdout temperatures, and external-test temperatures
as model inputs. This is the input side of the rigorous path: train-only full
solve, attribution, freeze, validation, holdout, and external-test.

## Figure Placement

Use the thesis diagram package as follows:

| Figure | Placement in this chapter |
| --- | --- |
| `F01_fluid_walls_loop_segment_atlas.svg` | Open the chapter after the model definition. |
| `F02_segment_local_ledger_inset.svg` | Place near the pressure and thermal equations. |
| `F03_upcomer_hybrid_schematic.svg` | Reference when explaining recirculation flags and blocked ordinary upcomer coefficients. |
| Matched Salt `side_z` upcomer velocity panels | Place immediately after the seeded exchange-CV path, or pair with `F03` as the CFD visual companion. Use the dated work-product package path and caption as diagnostic model-form evidence only. |

## Chapter-Ready Wording

The reduced model is a steady `fluid+walls` network. Each segment carries a
bulk fluid state coupled to a wall or material stack, plus separate pressure,
thermal, source/sink, boundary-condition, recirculation, uncertainty, and
admission fields. This structure is deliberately more explicit than a
fluid-only heat-loss model. It makes the location and status of each closure
visible: a pressure or heat-transfer slot can exist because the physics needs
an ownership lane, while the coefficient assigned to that slot can still be
diagnostic or blocked.

The predictive input contract follows from that architecture. Setup-known
geometry, property models, heater/cooler inputs, external-boundary dictionaries,
and admitted coefficients may be used to run the model. CFD mass flow,
realized wall heat flux, imposed cooler duty, validation temperatures, realized
test-section heat, and scored-row pressure or heat targets may not be runtime
inputs. This separation lets the same `fluid+walls` structure support both
diagnostic CFD replay and final predictive scoring without confusing the two.
