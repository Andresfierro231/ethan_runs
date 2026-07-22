# Dry 1D recirculation switch pseudocode

Inputs are setup-known geometry/source/property quantities plus predeclared
regime indicators. Realized CFD velocity, wallHeatFlux, and validation
temperatures are evidence labels only; they are not predictive runtime inputs.

```text
if reverse_flow_evidence_active is false
   and recirculation_proxy_active is false
   and low_recirc_or_nonrecirc_anchor_admitted is true:
    output = one_stream
    allow only admitted one-stream claims within the anchor envelope

elif reverse_flow_evidence_active is true
   and not (
       closed_recirc_cv_admitted
       and exchange_interface_admitted
       and wall_core_band_admitted
       and same_qoi_uq_admitted
       and mesh_gci_admitted
       and source_property_valid
   ):
    output = signed_flow_junction_network
    status = guarded_dry_fallback_not_net_branch_admission
    forbid Nu/f_D/K/F6/component-K/coefficient claims

elif closed_recirc_cv_admitted
   and exchange_interface_admitted
   and wall_core_band_admitted
   and same_qoi_uq_admitted
   and mesh_gci_admitted
   and source_property_valid:
    output = throughflow_plus_recirc_exchange_cell
    status = exchange_cell_architecture_admitted_no_coefficients
    expose dry QOI slots only; fit coefficients only under a future row

else:
    output = blocked_no_lane
    fail closed with no ordinary or exchange-cell production claim
```
