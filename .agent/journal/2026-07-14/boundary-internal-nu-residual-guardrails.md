---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_internal_nu_residual_guardrails/README.md
tags: [boundary-modeling, internal-nu, guardrails, journal]
related:
  - .agent/status/2026-07-14_AGENT-336.md
  - imports/2026-07-14_boundary_internal_nu_residual_guardrails.json
task: AGENT-336
date: 2026-07-14
role: BC-modeling/Implementer/Tester/Writer
type: journal
status: complete
---
# Boundary/Internal-Nu Residual Guardrails

Converted the internal-Nu zero-fit decision and upcomer recirculation admission
rule into boundary-model guardrails.

The new residual ownership table assigns heat residuals to physical lanes before
any Nu fit can be reopened:

- heater/source residuals -> heater realized-fraction/source contract;
- cooler/HX residuals -> cooler/HX UA/effectiveness model;
- passive wall residuals -> wall-layer/external convection dictionary;
- radiation -> boundary metadata/semantics, embedded in CFD wallHeatFlux during
  replay with no separate exported qr;
- storage -> wall/storage or transient residual ledger;
- branch mixing/recirculation -> section-effective admission/naming, not
  transferable single-stream Nu.

The extraction-field table asks therm-reconstr/upcomer work to use matched case
paths, property lanes, segment/patch maps, time windows, and inlet/mid/outlet
planes for boundary and Nu metrics. Fields include bulk T, wall-inner T,
wall-shell T, wallHeatFlux, Tsur/Ta/emissivity, external h/UA, reverse/secondary
flow metrics, Re/Pr/Ri/Ra/Gr/Gz, and storage time metrics.

Validation:

```text
python3.11 -m unittest tools.analyze.test_boundary_internal_nu_residual_guardrails
....
Ran 4 tests in 0.015s
OK
```

No solver outputs, registry/admission state, scheduler state, generated indexes,
or external Fluid files were modified.
