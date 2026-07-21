---
task: TODO-F6-ENDPOINT-FACE-UQ-EXECUTION
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: journal
status: complete
---
# F6 endpoint face UQ execution

Task: `TODO-F6-ENDPOINT-FACE-UQ-EXECUTION`

Implemented the execution package for endpoint face RAF/RMF, same-QOI time UQ, and same-QOI mesh/GCI follow-up.
The package remains launch-capable but no-submit by default: scripts perform preflight and require explicit later compute-node execution for harvested face metrics.

The scientific state remains conservative: clean endpoint labels are fixed, Salt2 mesh spread is diagnostic only, Salt3/Salt4 mesh UQ is missing, time-UQ is pending sampled neighbor windows, and no F6 fit is allowed.
