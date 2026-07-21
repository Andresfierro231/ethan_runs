---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight/recirc_segmentation_case_summary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight/recirc_component_summary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight/s14_pressure_anchor_recirc_linkage.csv
tags: [journal, upcomer, recirculation, segmentation, s13, s14, no-admission]
related:
  - .agent/status/2026-07-21_TODO-S13-S14-RECIRC-CV-SEGMENTATION-PREFLIGHT-2026-07-21.md
  - imports/2026-07-21_s13_s14_recirc_cv_segmentation_preflight.json
task: TODO-S13-S14-RECIRC-CV-SEGMENTATION-PREFLIGHT-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# S13/S14 Recirculation CV Segmentation Preflight

## Attempted

Implemented a reproducible VTK-only preflight for recirculation control-volume
segmentation. The builder parses the validated whole-mesh Salt2/Salt3/Salt4
cell VTKs, computes cell centroids, restricts to a right-leg ROI, identifies
cells with velocity opposite the dominant right-leg throughflow direction, and
labels point-connected reverse-flow components.

## Observed

All three cases produce large reverse-flow candidate masks. The right-leg ROI
contains `863270` cells in each case. Reverse-flow candidates increase from
Salt2 to Salt4: `136140`, `138382`, and `139994` cells. The largest connected
component is consistent in size and location but accounts for only about `53%`
of candidates in each case.

S14 linkage remains unchanged in admission terms. Right-leg and
test-section-span F6 lanes remain future candidates or diagnostic rows, and the
F3 Shah apparent comparison remains blocked because no ordinary/admitted F6
candidate exists.

## Inferred

The velocity evidence supports a real recirculation topology, but the VTK-only
candidate mask is not a defensible released control volume. Fragmentation means
the next task must use face-neighbor topology, not point-connected components
alone, before deriving an exchange interface or wall/core band.

## Contradictions Or Caveats

The masks are useful diagnostic artifacts, not released sampler inputs. The ROI
uses the right-leg coordinate envelope from whole-mesh VTK geometry and the
throughflow axis `y`. This is enough for preflight and S14 context, but not
enough for `mdot_exchange`, `Q_wall_W`, or coefficient work.

## Next Useful Actions

1. Build a face-neighbor map from VTK cell connectivity or OpenFOAM polyMesh
   owner/neighbour files for the same cases.
2. Re-label the reverse-flow candidate masks using face-connected components
   and boundary closure checks.
3. If one component becomes defensible, derive internal faces between the
   recirculation component and main-flow cells with the positive
   `mdot_exchange` convention.
4. Intersect the released volume with wall-face adjacency before any wall/core
   or `Q_wall_W` extraction.
