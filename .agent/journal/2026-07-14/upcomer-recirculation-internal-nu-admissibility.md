---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/
tags: [journal, upcomer-recirculation, internal-nu, admission]
related:
  - .agent/status/2026-07-14_AGENT-330.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
task: AGENT-330
date: 2026-07-14
role: Implementer/Tester/Writer
type: journal
status: complete
---
# Upcomer Recirculation Internal-Nu Admissibility

Claimed AGENT-330 for a disjoint package from the active AGENT-324 onset
blocker row, then consolidated the current onset, single-stream validity,
coefficient-naming, and thermal admission evidence.

Outputs:

- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/upcomer_recirculation_onset_conditions.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/coefficient_naming_rules_for_recirculation.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/README.md`

Findings:

- The available admitted upcomer onset evidence remains Salt2-4 only:
  Re_upcomer `71.125` to `134.883`, backflow fraction `0.278` to `0.172`,
  and Ri_median `2.634` to `1.498`.
- Candidate onset rows with matched Re/Pr/Ri/Gz/wall-bulk Delta T and
  reverse-flow metrics were not present in the cited onset packages; the work
  product records that as an extraction blocker rather than manufacturing rows
  from timeseries-only evidence.
- Higher Re correlates with lower backflow fraction and lower recirculation
  intensity across the three rows, but all rows are still recirculating and no
  ordinary-pipe anchor exists.
- Internal Nu remains validation-only/diagnostic; `0` rows are fit-admissible.
- Radiation semantics stay explicit: CFD `rcExternalTemperature` wallHeatFlux
  includes radiation where that BC is used, and no separate exported `qr` term
  should be added to an internal-Nu residual.

Validation:

```bash
python3.11 tools/analyze/build_upcomer_recirculation_internal_nu_admissibility.py
python3.11 -m unittest tools.analyze.test_upcomer_recirculation_internal_nu_admissibility
```
