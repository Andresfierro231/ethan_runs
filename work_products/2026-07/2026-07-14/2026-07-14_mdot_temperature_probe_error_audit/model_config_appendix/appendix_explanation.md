# Model Configuration Appendix

This directory contains compact copies of the 1D model setup used by AGENT-360.
The copied YAML files are read-only snapshots from external Fluid configs. The
CSV files resolve those configs into the case inputs, model modes, closure
terms, and source/loss assignments used by the audit.

Runtime classes are deliberately separated: setup inputs are allowed for
predictive-style modes, CFD mdot is validation-only except fixed-mdot
diagnostics, and realized CFD wallHeatFlux is diagnostic evidence consumed only
by explicitly CFD-informed modes.
