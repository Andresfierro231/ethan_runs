---
provenance:
  - tools/extract/build_s13_upcomer_exchange_exact_pressure_qwall_compute.py
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute/summary.json
tags: [s13, upcomer-exchange, pressure, wallHeatFlux, q-wall]
related:
  - .agent/journal/2026-07-21/s13-upcomer-exchange-exact-pressure-qwall-compute.md
  - imports/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute.json
task: TODO-S13-UPCOMER-EXCHANGE-EXACT-PRESSURE-QWALL-COMPUTE-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: status
status: complete
---
# TODO-S13-UPCOMER-EXCHANGE-EXACT-PRESSURE-QWALL-COMPUTE-2026-07-21

## Objective

Sample and reduce exact target-window `p`/`p_rgh`, then integrate trusted-wall
`wallHeatFlux` into `Q_wall_W` for the S13 seeded upcomer exchange package.

## Outcome

Complete. The reducer parsed read-only native collated OpenFOAM fields through
`cellProcAddressing` and `faceProcAddressing` and wrote:

- `3/3` exact pressure-basis rows released.
- `3/3` exact `Q_wall_W` rows released.
- `233280` selected pressure detail rows.
- `116640` trusted-wall heat-flux detail rows.
- `Q_wall_W`: Salt2 `23.1161370708 W`, Salt3 `25.3465488205 W`, Salt4 `28.1231837021 W`, positive into seeded recirculation fluid.

All three Qwall rows have full trusted-wall face and area coverage. Each case
has a tiny NCC seam patch-label mismatch (`0.000596-0.000722 W`, about
`2.57e-05` of the native integral), recorded in
`trusted_wall_Q_wall_summary.csv`; the global face-id mapping is complete.

## Changes Made

- `tools/extract/build_s13_upcomer_exchange_exact_pressure_qwall_compute.py`
- `tools/extract/test_s13_upcomer_exchange_exact_pressure_qwall_compute.py`
- `work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute/**`
- `.agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-EXACT-PRESSURE-QWALL-COMPUTE-2026-07-21.md`
- `.agent/journal/2026-07-21/s13-upcomer-exchange-exact-pressure-qwall-compute.md`
- `imports/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute.json`
- `.agent/BOARD.md` own row

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_upcomer_exchange_exact_pressure_qwall_compute.py tools/extract/test_s13_upcomer_exchange_exact_pressure_qwall_compute.py` passed.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_exact_pressure_qwall_compute` passed: `5` tests in about `30 s`.
- `python3.11 tools/extract/build_s13_upcomer_exchange_exact_pressure_qwall_compute.py` passed and regenerated the package.

## Guardrails

- Native solver outputs were read only and not mutated.
- No scheduler action was needed; the reducer completed under the 5-minute threshold on the compute node.
- No OpenFOAM solver or postProcess command was launched.
- No sampler refresh, production harvest, same-QOI UQ, fitting, coefficient admission, registry mutation, Fluid/external edit, blocker-register change, thesis edit, or S11/S12/S13/S15/S6 trigger occurred.
- Heat residual was not hidden in internal `Nu`; `Q_wall_W` is a separate released heat path.

## Remaining Blockers

- Production sampler manifest refresh must consume this package in a separate row.
- Same-QOI UQ remains blocked until neighboring-window and mesh/GCI Qwall/pressure support exists.
- Production harvest/admission remains blocked until sampler refresh and same-QOI UQ are completed.
