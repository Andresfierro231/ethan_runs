---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract/
tags: [journal, internal-nu, extraction-contract, therm-reconstr]
related:
  - .agent/status/2026-07-14_AGENT-339.md
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/
task: AGENT-339
date: 2026-07-14
role: Implementer/Tester/Writer
type: journal
status: complete
---
# Upcomer Internal-Nu Extraction Contract

Implemented the follow-on contract requested after the zero-fit upcomer
internal-Nu admission decision. The package tells `therm-reconstr` exactly what
to extract and how each row will be admitted or rejected.

Outputs:

- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract/upcomer_extraction_contract.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract/upcomer_nu_admission_criteria.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract/coefficient_naming_policy.md`
- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract/README.md`

Key decisions:

- Plane normals for admission must be geometric upcomer station tangents in the
  nominal inlet-to-outlet direction, not mean-velocity normals.
- Reverse area fraction, reverse mass fraction, secondary velocity fraction,
  mass-flux-weighted bulk T, wall T, wallHeatFlux, Re/Pr/Ri/Gr/Ra/Gz, plane
  location, and exact time window are all required by contract.
- `Nu_section_effective_upcomer_diagnostic` remains distinct from true
  `Nu_fit_admissible_upcomer_single_stream`.
- Internal-Nu fitting reopens only after at least three admitted upcomer rows
  satisfy `fit_admissible_Nu`, including an ordinary-pipe non-recirculating
  anchor and a near-transition or higher-Re row.

Validation:

```bash
python3.11 tools/analyze/build_upcomer_internal_nu_extraction_contract.py
python3.11 -m unittest tools.analyze.test_upcomer_internal_nu_extraction_contract
```
