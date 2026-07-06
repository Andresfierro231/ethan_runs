# Upstream Method Requirements

## feature_keff_full_path_closure
- current status: `provisional_defended`
- missing requirement: retained-time feature-path hydro-integral or equivalent direct pathwise closure, not just patch-endpoint p_rgh plus local straight reference
- why it matters: removes the main remaining method caveat on the defended feature K_eff fit
- current bias risk: feature excess may be over- or under-attributed when the local boundary reference is not a faithful proxy for the full feature path
- next owning work type: `upstream extractor hardening`

## salt_nu_defended_dependency
- current status: `not_defensible_yet`
- missing requirement: more direct closure-supported thermal rows plus stronger separation between intended transfer, parasitic wall loss, junction exchange, and residual imbalance
- why it matters: without more closure-supported rows the Salt Nu fit is underdetermined and not trustworthy
- current bias risk: residual heat imbalance could be misread as fluid-side Nu behavior
- next owning work type: `thermal closure hardening`

## hydraulic_late_window_sensitivity
- current status: `not_run`
- missing requirement: retained-time defended straight-section hydraulic rows instead of case-level means only
- why it matters: needed to show whether the defended friction model is stable to late-window selection
- current bias risk: temporal averaging may hide sensitivity in the admitted hydraulic subset
- next owning work type: `upstream or intermediate defended-row rebuild`
