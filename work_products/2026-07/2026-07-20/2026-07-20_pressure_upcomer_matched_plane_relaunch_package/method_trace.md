---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_extraction_plan/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract/upcomer_extraction_contract.csv
tags: [therm-reconstr, upcomer-recirculation, internal-nu, method]
task: AGENT-344
date: 2026-07-20
role: Implementer/Tester/Writer
type: method
status: active
---
# Matched Upcomer Plane Compute Method

## Method

The extractor samples three fixed geometric planes: `upcomer_inlet`,
`upcomer_mid`, and `upcomer_outlet`. Plane normals come from
`mesh_stations.json`; they are not inferred from the mean velocity.

The compute lane writes scratch-only OpenFOAM controlDicts. It first generates
`wallHeatFlux` in the scratch reconstructed case when needed, then samples VTK
surfaces for plane fields and upcomer wall patches.

Plane metrics are true face-area weighted when VTK geometry is present:

- reverse area fraction = reverse-flow face area / total face area;
- reverse mass fraction = reverse `rho * U_n * A` / total absolute mass flux;
- secondary velocity fraction = RMS tangential velocity / RMS speed;
- bulk T = signed mass-flux-weighted T, with forward-dominant fallback only when
  signed flux is singular;
- Re/Pr/Ri/Gr/Ra = area-weighted sampled values;
- Gz = Re * Pr * D_h / streamwise length from upcomer inlet.

Wall metrics use the upcomer wall-patch surface and keep faces within
`0.5*bore_m` of each station plane along the station normal. `wallHeatFlux` is
the total OpenFOAM field; `rcExternalTemperature` radiation is embedded and no
separate `qr` residual is added.

## Classification

Rows are fit-admissible only if they pass all current scalar gates:
reverse area fraction < 0.02, reverse mass fraction < 0.02, secondary velocity
fraction < 0.20, Ri < 0.30, and |T_wall - T_bulk| >= 0.5 K. The heat-balance
residual gate remains pending until matched enthalpy residual rows are wired in.
