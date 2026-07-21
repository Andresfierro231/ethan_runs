# Phase 1 Journal Synthesis

## Purpose

This pass uses the dated journals as the primary chronology for what changed
day by day. The main value of the journals is not just the artifact list; it
is the record of when priorities changed and why.

## Chronology

### `2026-05-29` to `2026-06-02`: intake, publication, and first mismatch checks

- The workspace started by proving local intake and a publish path around
  `val_salt_test_2_coarse_mesh_laminar`.
- By June 1 and June 2, the journals were already pushing beyond intake into
  two early challenges:
  - practical convergence versus coded end-state
  - mismatch between Ethan CFD assumptions and the current 1D model branches
- The June 2 report/journal pair established an early recurring theme:
  staging and metadata work were necessary, but they did not answer whether the
  current assumptions were physically or modeling-wise aligned.

### `2026-06-04` to `2026-06-05`: broad reporting, direct validation, and runtime triage

- June 4 built the first broad reporting stack:
  direct validation, metadata/glossary, runtime/hypothesis matrix, behavior
  packages, steadiness audit, and transient/axial reporting.
- The priority at this stage was breadth. The repo was trying to understand:
  - which cases were usable now
  - which needed continuation
  - which pointed toward alternate assumptions rather than just more runtime
- June 5 sharpened that into campaign decisions. Salt 1 stayed problematic,
  Water laminar claims stayed cautious, and continuation planning became a
  first-class workstream.

### `2026-06-07` to `2026-06-11`: presentation assets and Salt 2 method repair

- June 7 and June 8 added presentation-oriented packaging, rendering helpers,
  and figure refreshes. These entries matter because they show a brief visual
  packaging push before the repo pivoted back to technical method hardening.
- June 9 moved into heat-flow auditing and streamwise friction products.
- June 10 is the key method-repair journal. It documents the Salt 2 hydraulic
  registration repair, the anchored polyline fix, and the provenance fixes that
  made the package scientifically safer to reuse.
- June 11 explicitly stated that the stronger Salt 2 story was still not ready
  to be promoted without a rigor-repair layer. This is one of the clearest
  examples of the repo choosing caution over narrative momentum.

### `2026-06-12` to `2026-06-18`: postprocessing expansion and trust gating

- June 12 established a reusable per-run and campaign packaging workflow.
- June 15 expanded into the detailed field-transport campaign, first on Salt 2,
  then across Salt, then into Water. The same journal also records the board
  choreography around rollout order and acceptance gates.
- June 16 and June 17 pushed paper-facing figures and the nondimensional
  dashboard, but June 17 also strengthened the evidence hierarchy: boundary
  layers, pressure, HTC, and transport outputs were being produced, but not all
  of them were being promoted equally.
- June 18 marks the transition from extraction to interpretation. The journal
  repeatedly emphasizes scrutiny, closure, exclusions, and safe subsets rather
  than new compute.

### `2026-06-19`: explicit pivot into closure-to-modeling planning

- The June 19 journal is the cleanest statement that priorities had changed.
- The goal was no longer "finish the 3D package stack." It was "define the
  first defensible Salt-first 1D bundle and keep Water in readiness."
- This journal also records a more disciplined blocker language:
  missing observables, defended exclusions, and queued CFD follow-ons are all
  described as part of one modeling plan rather than disconnected tasks.

### `2026-06-22` to `2026-06-25`: frozen-state contract and queue-aware follow-ons

- June 22 published the frozen-state and feature-path packages while correcting
  the Salt heat-balance contract and relaunch logic.
- June 23 shows the operational side of the same story:
  normal-queue follow-ons, mistaken cancellation during the checkpoint pass,
  clarification of what "freeze" meant, and requeueing.
- June 25 then restaged the next bounded continuation and boundary wave under a
  more robust normal-queue packaging plan.

## Priority changes captured by the journals

- `priority shift 1`: from workspace setup to scientific usability.
- `priority shift 2`: from all-case reporting breadth to Salt 2 method repair.
- `priority shift 3`: from generating transport outputs to auditing which ones
  were trustworthy.
- `priority shift 4`: from 3D interpretation to bounded 1D closure handoff.
- `priority shift 5`: from generic future work to blocker-specific retained-time
  support and replay refresh tasks.

## Lessons visible in the journal trail

- When the journals became more explicit about contradictions and exclusions,
  the later report stack became more coherent.
- Queue and staging decisions repeatedly fed back into scientific scope.
  Continuation maturity was part of the evidence chain, not just cluster
  operations.
- The repo improved when it stopped collapsing "usable for internal trend
  inspection" and "defensible for closure modeling" into the same category.

## Open questions carried forward from the journals

- Whether mature late windows can materially improve the straight-section
  sensitivity set.
- Whether feature `K_eff` can be hardened without a new upstream extractor.
- Whether Water should ever be part of a shared first-fit closure surface.
- Whether cooler-side boundary semantics can be made more explicit than fixed
  readable sink `Q`.
