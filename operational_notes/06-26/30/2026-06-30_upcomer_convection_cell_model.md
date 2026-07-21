# Upcomer Convection-Cell + Natural-Circulation Closure (model plan + seed data)

Date: `2026-06-30` · Owner: claude (AGENT-156)
Supersedes the "exclude upper_leg friction" recommendation in
`2026-06-30_upper_leg_negative_friction_investigation.md` (see Reconciliation).
Tool: `tools/extract/sample_upcomer_convection_cell.py` ·
Data: `work_products/2026-06-30_claude_upcomer_convection_cell/`

## 1. Decision (user, 2026-06-30)

The upcomer's negative apparent friction factor reflects a **real buoyancy-driven
recirculation / convection cell**, not just a post-processing artifact. The
upcomer will therefore be modeled with a **convection-cell + natural-circulation
closure**, and we will FIT a correlation, in nondimensional groups, that captures
the **onset and limits** of the recirculation. More CFD is being run to map that
onset/limit envelope; this note sets up the framework and seeds it with the
current mainline (Salt 2/3/4 Jin) points.

## 2. Reconciliation with the earlier "artifact" finding

The earlier investigation found the negative f traces to the buoyancy/hydrostatic
term in `p_rgh`. That is consistent with — not contradictory to — a real cell:
the recirculation IS buoyancy-driven, so it both (a) makes a single Darcy f
meaningless on the upcomer and (b) shows up through the buoyancy term. The
correct response is to MODEL it with convection-cell scaling, not to assign a
friction factor. Direct CFD evidence of the cell (this session): on single-leg-
masked upcomer cross-sections, **15–33% of the section area flows backward**
(`backflow_area_fraction`), and flow alignment drops to ~0.5 near the top
(TP6) — a counter-rotating structure, not clean through-flow.

## 3. Literature basis (papers/LitRev-start-.../chapters 14 & 05)

- **Convection-cell scaling (LeFrancois et al.)**: `Nu = C·Ra^n·Pr^m`,
  `Ra = beta·g·(Th−Tc)·Lc^3/(nu·alpha)`. Molten-salt cells change scaling regime
  and large-scale circulation across ~`2e7 < Ra < 2e9`. (Cavity study → evidence
  the cell regime is Ra-controlled; not a pipe HTC law.)
- **Mixed convection in vertical tubes (Jackson, Cotton & Axcell)**: use
  `Ri = Gr/Re^2` as the buoyancy screen; buoyancy opposing/assisting the mean flow
  enhances or impairs transport and can drive reversed/recirculating flow.
  **Upcomer and downcomer must not share a closure** (branch-direction policy).
- **Thermal development**: Graetz `Gz` coordinate; report local quantities.

## 4. Candidate nondimensional groups (independent variables)

Primary: **Ri = Gr/Re²** (buoyancy-vs-forced screen; recirculation expected for
Ri ≳ O(1)). Secondary: **Ra** (cell scaling/regime), **Gr**, **Re**, **Pr**, and
**Gz** (development). The solver writes Gr, Ra, Ri, Re, Pr as volume fields, which
the tool samples on each upcomer cross-section.

Recirculation METRIC (dependent variable, all dimensionless):
- `backflow_area_fraction` — fraction of section flowing opposite to net flow
  (0 = clean; →0.5 = fully developed cell). **Recommended primary target.**
- `recirculation_intensity` — reverse volumetric flux / forward flux.
- `flow_alignment` — |mean U| / mean |U| (1 = coherent; →0 = cell-dominated).

## 5. Seed data (mainline Salt 2/3/4 Jin; SECTION-mean groups)

backflow_area_fraction with local section Ri, Ra, Re (full table in the CSVs):

| station (span) | Salt2 bf / Re | Salt3 bf / Re | Salt4 bf / Re |
| --- | --- | --- | --- |
| TW7 (left_lower_leg) | 0.28 / 86 | 0.22 / 112 | 0.17 / 153 |
| TP4 (left_lower_leg) | 0.24 / 80 | 0.18 / 105 | 0.15 / 142 |
| TP5 (test_section_span) | 0.33 / 77 | 0.31 / 99 | 0.30 / 133 |
| TW8 (left_upper_leg) | 0.31 / 78 | 0.28 / 102 | 0.27 / 137 |
| TP6 (left_upper_leg) | 0.33 / 51 | 0.32 / 69 | 0.33 / 97 |

Observed: Ri ≈ 64–300 (≫1 → buoyancy-dominated, consistent with a cell). In the
LOWER upcomer (TW7/TP4) backflow falls monotonically as Re rises (0.28→0.17) —
i.e. stronger forced flow suppresses the cell: a clear onset/limit trend ready to
correlate. The UPPER upcomer (TP5/TW8/TP6) keeps backflow ~0.3 and alignment ~0.5
even at the highest Re — a persistent cell near the cooler/top, suggesting a
spatially varying or two-region structure (a single bulk Ri may not collapse all
stations; see open items).

## 6. Proposed correlation framework (to fit as CFD grows)

1. Target: `backflow_area_fraction = F(Ri)` (or `F(Ra/Re^p)`), with an ONSET
   threshold `Ri_crit` below which the upcomer behaves as ordinary forced/mixed
   flow and a single Nu/f is admissible.
2. Functional candidates: logistic/onset form `bf = bf_max / (1 + (Ri_crit/Ri)^k)`
   or power-law `bf = a·Ri^b` above onset; choose once the sweep populates the
   low-Ri (high-Re) end where the cell turns off.
3. Hybrid 1D closure: when `Ri < Ri_crit`, use the forced/mixed Nu and the normal
   straight-friction path; when `Ri ≥ Ri_crit`, switch the upcomer to a
   convection-cell sub-model — Nu(Ra,Pr) cell scaling for heat transfer and a
   recirculation-aware effective resistance instead of a Darcy f.
4. Keep upcomer and downcomer closures separate (policy).

## 6b. Onset estimate (two independent hand routes — bracketed)

- **Route A (data extrapolation)**, 3 nominal points: lower-upcomer backflow→0 at
  **Re ≈ 240–260**; upper upcomer ~550; top (TP6) NOT Re-controlled (cooler-pinned).
- **Route B (literature criterion)**, `tools/analyze/mixed_convection_reversal.py` +
  `operational_notes/06-26/30/2026-06-30_upcomer_reversal_criterion_hand_estimate.md`:
  laminar mixed-convection screens (Ri = Gr_T/Re² → O(1); Gr_T/Re → O(100–300))
  give **Re_crit ≈ 100–235**, **Ri_crit ≈ O(1)** (band ~0.5–2). Jackson–Cotton–
  Axcell Bo* cited for physics only (it is a TURBULENT correlation; our flow is
  laminar). Current Salt 3 (Re≈112) sits right at the onset boundary — consistent
  with the observed 0.15–0.33 backflow.
- **Both routes agree to ~factor 2**: shutoff at "a few hundred" Re, ~1.5–2.5×
  above the current max CFD Re (~150). This is an order-of-magnitude estimate, not
  a fitted law — new CFD / existing perturbation runs (reach Re≳250) are required.

> **CORRECTION — use MEDIAN (or a characteristic) Ri, not the section MEAN.**
> The solver section-MEAN Ri (64–300 in §5) is dominated by low-velocity cells and
> is ~100× the section-MEDIAN Ri (2–8) in the SAME data. The hand Ri_crit≈O(1)
> matches the MEDIAN. Do NOT correlate against the solver mean Ri. A properly
> DEFINED characteristic Ri (leg ΔT, Lc=D_h, bulk U) is still NEEDS-AUDIT and is
> the right independent variable for the published correlation.

## 6c. Inclination IS a governing variable — RESOLVED: use mesh geometry (CFD matches the rig)

> **RESOLVED 2026-06-30.** The earlier "sim-vs-rig discrepancy" below was MY ERROR:
> I derived inclinations from the schematic `tp_tw_probe_locations.csv`, which does
> not match the mesh. Measured from the actual mesh patches (PCA), CFD gravity
> MATCHES the rig: HEATER (pipeleg_lower_05) 21° from horizontal; COOLER 22°; TEST
> SECTION (pipeleg_left_04) vertical + smaller bore (20.9 mm, quartz); DOWNCOMER
> (pipeleg_right_02) vertical. The probe CSV also SWAPS lower↔right spatially, so
> cut-plane friction/recirculation by probe label is mis-oriented and must be
> re-extracted from mesh-built centerlines. Thermal (patch-based) and the upcomer
> recirculation (left side) are unaffected. Full detail + fix plan:
> `operational_notes/06-26/30/2026-06-30_mesh_geometry_vs_probe_csv_provenance.md`. The
> stale (incorrect, probe-CSV-based) discussion is retained below struck-through
> for the record.

~~Buoyancy splits into a STREAMWISE part (g·cosθ → assist/oppose flow → reversal /
convection cell) and a TRANSVERSE part (g·sinθ → stratification / secondary flow),
where θ is the angle between the leg axis and GRAVITY. So inclination is a real
governing variable. BUT the CFD and the physical rig disagree on which legs are~~ (STALE — see resolution above)
<!-- STALE probe-CSV-based text retained below -->
## ~~6c-old (incorrect)~~ SIM vs RIG ORIENTATION DISAGREE (UNRESOLVED, HIGH PRIORITY)

Buoyancy splits into a STREAMWISE part (g·cosθ → assist/oppose flow → reversal /
convection cell) and a TRANSVERSE part (g·sinθ → stratification / secondary flow),
where θ is the angle between the leg axis and GRAVITY. So inclination is a real
governing variable. BUT the CFD and the physical rig disagree on which legs are
inclined:

| Leg | PHYSICAL rig (Ethan, authoritative for the rig) | CFD DATA (mesh coords + g=(0,-9.81,0); heater leg heat-flux-identified) |
| --- | --- | --- |
| lower_leg (HEATER) | 20° from horizontal = **70° from gravity (inclined)** | masked faces x≈0.888 along y; g along y → **0° from gravity (VERTICAL)** |
| upper_leg (COOLER) | 70° from gravity (inclined) | ~75° from gravity — roughly consistent |
| upcomer (3 left legs) | **vertical** | vertical — consistent |
| downcomer (right_leg) | **vertical** | ~75° (near-horizontal) — INCONSISTENT |

The heater leg is identified independently by its heat flux (q_w=+3798 W/m² into
the fluid), so this is not a labeling guess: in the SIMULATION the heated leg is
parallel to gravity, while the RIG's heater leg is a 20° incline. Cooler and
upcomer roughly agree; HEATER and DOWNCOMER do not.

**Why it matters:** the solver's Gr/Ra/Ri fields and the recirculation patterns
are computed in the simulation's geometry+gravity frame. If that orientation does
not match the rig, which legs carry streamwise vs transverse buoyancy — and hence
which legs recirculate — may not transfer to the physical loop.

**RETRACTION:** the earlier claim "the downcomer doesn't recirculate because its
buoyancy is transverse" is withdrawn. Physically the downcomer is vertical
(streamwise buoyancy), so its observed ~0% backflow needs another explanation
(lower local Ri, or buoyancy-assisted descent that does not reverse).

**ROBUST regardless of frame:** the EMPIRICAL recirculation from the velocity
field stands — upcomer cross-sections show 15–33% backflow, downcomer ~0%. Only
the inclination-based INTERPRETATION is on hold.

**Candidate causes (need Ethan / mesh audit):** (1) CFD gravity set axis-aligned
with the mesh while the rig is tilted ~20° → sim represents a differently-oriented
loop; (2) a mesh/segment-frame subtlety (less likely for the heat-flux-identified
heater). The tool now emits `inclination_from_vertical_deg`,
`buoyancy_streamwise_frac_cos/sin`, and `Ri_streamwise_median = Ri_char·cosθ`, but
these are SIMULATION-frame and NOT yet validated against the rig.

ACTION: confirm with Ethan whether the CFD gravity orientation was intended to
match the 20°-inclined rig. If not, the buoyancy/recirculation closures must be
re-derived against the correct orientation (or the discrepancy quantified). Use
the section-MEDIAN Ri (~O(1)) as the characteristic group, not the mean (6b).

## 7. Open items / NEEDS MORE ANALYSIS

- **Characteristic groups**: the section-mean local-field Ri/Ra are noisy and
  geometry-frame dependent. Define a CHARACTERISTIC upcomer Ri/Ra from the leg
  ΔT, Lc, and bulk U (page-audit the solver's Ra/Ri Lc and reference ΔT first).
- **Spatial structure**: lower vs upper upcomer behave differently → consider a
  two-region (entry vs cooler-adjacent) cell model or an s-resolved metric.
- **Onset point**: current Re range (~50–153) is all in-cell; the incoming
  onset/limit CFD must reach higher Re (cell-off) to locate `Ri_crit`.
- **Cell circulation strength**: add an in-plane stream-function / vortex metric
  (current metrics are normal-component based; a true cell metric would use the
  in-plane velocity rotation).
- Coarse mesh, laminar, single time — seed data only, not a fitted law yet.
