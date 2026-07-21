# Lit-Rev CFD Validity Diagnostics

Date: `2026-07-13`

Task: `TODO-LITREV-CFD-VALIDITY-DIAGNOSTICS`

Built a CFD single-stream validity package with 18 section rows and 54
coefficient naming rows. Existing recirculation/backflow proxies were consumed
first; exact reverse-flow area/mass and secondary velocity remain future
bounded extraction needs where absent.

Interpretation: section-effective or diagnostic coefficient names must be used
where reverse/recirculating flow is material. Universal `f_D`, `K`, or `Nu`
names are rejected unless plane isolation and single-stream assumptions hold.

Recommended next action: feed `coefficient_naming_limits.csv` into coefficient
export and named-loss handoffs.

