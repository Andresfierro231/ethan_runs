# Insulation in the 1D Model: Cautionary Note and Instructions

Date: `2026-07-08`
Author: claude (AGENT-210)
Status: **Standing instruction — read before any insulation-related work**

---

## CRITICAL LESSON: THE 1D MODEL INSULATION ≠ THE CFD INSULATION

This note exists because the 1D insulation parameter has been set to the wrong value
in multiple sessions. Each error corrupted the thermal matching and produced misleading
friction closure calibrations.

---

## 1. What the CFD actually has

Audited from `jadyn_runs/.../0/T` and `work_products/2026-07-08_cfd_scenario_contract/`
(AGENT-202, 2026-07-08).

| Pipe section | Insulation | Thermal details |
|---|---|---|
| Main piplegs (lower_leg, right_leg, upper_leg, left_lower_leg, left_upper_leg) | **1.4 in = 35.56 mm Calzite** | k=0.0455 W/m·K; outer wrap: 0.032 in Teflon; ε_outer=0.5 |
| Test section (pipeleg_left_04) | **NONE — 2.2 mm fused quartz only** | k_quartz=1.38 W/m·K; ε=0.95; net heat SINK |

**The test section is a net heat sink.** Even with its 37 W heater, the radiation +
convection loss through 2.2 mm bare quartz wall exceeds the electrical input:
net Q to fluid = −5.7 W (S2) to −16.8 W (S4).

---

## 2. What the 1D model uses and what it means

`ScenarioConfig.insulation_thickness_in` is a **SINGLE GLOBAL VALUE** applied to all
pipe sections uniformly. There is no per-section override in the current implementation
(as of 2026-07-08).

Historical temperature-matching sweep:

| insulation_thickness_in | Thermal match result |
|---|---|
| 1.4 in (physical CFD value) | **WRONG** — applies 1.4 in to the test section too; loop is too hot |
| 0.25–0.30 in (fitted) | Happens to match CFD T_loop **for the wrong reasons** |

The fitted value (0.25–0.30 in) is a **compensating error**: it cools down the main
piplegs (by thinning their insulation) to compensate for the missing test-section heat
loss (which the 1D model cannot represent with a global parameter).

---

## 3. Why this matters for closure work

The Ri number, heat transfer coefficients, and friction calibration ALL depend on the
loop temperature field. If the global insulation value is wrong, the T_bulk per segment
is wrong, which means:

- `Ri_streamwise` (used in F5) is computed at the wrong operating point
- `HTC / Nu` (thermal closures) are calibrated at the wrong ΔT
- `phi = f_CFD / f_F3_shah` depends on viscosity, which depends on T

Even a 10 K error in T_bulk changes μ by ~5%, which changes Re by ~5%, which changes
f_lam by ~5%, which changes phi by ~5%. Over multiple closures, these errors compound.

---

## 4. What future agents MUST do

### Before touching insulation:

1. **Read this note** (you already are).
2. **Check the scenario config** you are working with. What is `insulation_thickness_in`?
   - If it is 0.25–0.30 in: this is the TEMPERATURE-MATCHED value; use it for thermal
     comparisons but do NOT interpret it as the physical CFD insulation.
   - If it is 1.4 in: this is the PHYSICAL CFD value; the temperature will NOT match
     unless you implement per-section insulation overrides.
   - If it is anything else: investigate why before proceeding.

3. **Do NOT use global insulation 1.4 in for validation runs**. The loop temperature
   will be ~30–50 K too hot and all comparisons will be off.

4. **Do NOT claim that global insulation 0.25–0.30 in represents the physical setup**.
   It is a model-matching parameter only.

### When implementing per-section insulation (the right fix):

The `outer_insulation_multiplier_by_parent_segment` field in `ScenarioConfig` provides
a stopgap. Set it as follows to approximate the CFD setup:

```python
outer_insulation_multiplier_by_parent_segment = {
    "pipeleg_left_04": 0.0,   # test section: bare quartz, no Calzite insulation
    # all other segments: keep at 1.4 in (physical)
}
insulation_thickness_in = 1.4
```

This is still approximate (the test section has quartz + radiation, not just "no
insulation"), but it is closer to the physical setup than the global compensating value.

The proper fix is to add a `insulation_thickness_by_parent_segment` dict to
`ScenarioConfig` and implement per-section thermal resistance computation.

---

## 5. Quick reference: Insulation values

| Value | Meaning | Use case |
|---|---|---|
| 1.4 in | Physical CFD main piplegs | CFD validation IF test section is modeled separately |
| 0.25–0.30 in | Temperature-matching "fitted" value | Loop temperature comparison only |
| 0.0 in on test section | Physical CFD test section | Required for any per-section implementation |

---

## 6. Session history of insulation errors

These errors were documented in multiple sessions to prevent recurrence:

- **2026-07-07**: Multiple friction closure calibrations were run with global
  insulation 0.25–0.30 in and treated as if they matched the physical CFD setup.
  This is acceptable for thermal comparisons but should not be described as "using CFD
  insulation."

- **2026-07-08**: AGENT-202 (codex) performed the definitive CFD scenario contract
  audit. See `work_products/2026-07-08_cfd_scenario_contract/` for the authoritative
  BC audit.

---

## 7. Checklist before insulation-related commits

- [ ] Confirm `insulation_thickness_in` value and document which regime it represents
- [ ] Check that test results note whether 1.4 in (physical) or 0.25–0.30 in (matched)
- [ ] Do NOT call the matched value "the CFD insulation"
- [ ] If using 1.4 in, add a note that loop temperature will NOT match CFD without
      per-section test-section correction

---

**Cross-references:**
- Physical CFD insulation audit: `work_products/2026-07-08_cfd_scenario_contract/`
- Ri characteristic length audit: `operational_notes/07-26/08/2026-07-08_ri_characteristic_length_audit.md`
- Friction Ri failure analysis: `operational_notes/07-26/08/2026-07-08_friction_ri_failure_and_path_forward.md`
