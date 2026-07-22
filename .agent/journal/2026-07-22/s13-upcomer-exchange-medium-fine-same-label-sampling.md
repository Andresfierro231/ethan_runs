---
provenance:
  - tools/analyze/build_s13_upcomer_exchange_medium_fine_same_label_sampling.py
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_same_label_sampling/summary.json
task: TODO-S13-UPCOMER-EXCHANGE-MEDIUM-FINE-SAME-LABEL-SAMPLING-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: journal
status: complete
tags: [journal, s13, upcomer-exchange, medium-fine, mesh-gci, same-label]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_same_label_sampling
---

# S13 medium/fine same-label sampling preflight

## Attempted

Claimed a narrow S13 row to resolve the ambiguity between missing medium/fine
runs and missing medium/fine exact-label rows. Inventoried the live `/home1`
Salt2/Salt3/Salt4 medium/fine source directories, checked terminal processor
times and latest primitive fields, compared them to the exact S13 mesh-family
generation contract, and wrote a no-submit sampling command contract.

## Observed

All six medium/fine source runs exist and have readable processor directories.
The latest terminal field directories include `U`, `T`, `rho`, and
`wallHeatFlux`, which are enough raw fields for the four S13 labels if the
mesh-level geometry masks and normals are available or generated. Salt3
medium/fine exists even though the July 9 endpoint coverage package did not
include Salt3 rows.

The strict current-coarse target windows are absent on medium/fine. The
available terminal candidate windows are Salt2 `516;517;518` and `397;398;399`,
Salt3 `1338;1339;1340` and `531;532;533`, and Salt4 `1157;1158;1159` and
`415;416;417`.

Existing postProcessing results are useful for provenance, stationarity, and
sanity checks, but they are not exact S13 rows. Pipeleg mdot is not the
exchange-interface flux, velocity profiles are not closed surface integrals,
probe means are not S13 wall/core/bulk masks, and July 9 endpoint GCI rows are
different QOI labels.

## Inferred

The project does not need to rerun CFD to make the next S13 step. It needs a
scheduler-authorized compute-node sampler that reads the medium/fine terminal
fields and produces exact S13 labels over mesh-level S13 geometry. Because
strict coarse-contract times are not available, the next row must include a
terminal-window mesh-time equivalence gate before using the results for GCI.

## Contradictions or Caveats

The prior shorthand "medium/fine rows missing" was correct only for derived
S13 exact-label rows, not for CFD source runs. The source runs are present. The
scientific blocker is that the exact S13 rows have not been sampled and cannot
be replaced by existing endpoint/probe/profile outputs.

## Next Useful Actions

Claim a compute-node sampling row using
`work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_same_label_sampling/sampling_command_contract.csv`.
Generate the mesh-level trusted wall, exchange-interface, recirculation-CV, and
wall/core/bulk masks for medium/fine, sample the four S13 labels at terminal
candidate windows, then run a mesh-family monotonicity/GCI or fail-closed mesh
spread gate before production harvest.
