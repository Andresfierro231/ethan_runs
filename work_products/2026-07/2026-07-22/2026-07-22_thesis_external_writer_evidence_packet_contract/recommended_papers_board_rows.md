# Recommended Papers-board Rows

These rows should be added to `../papers/.agent/BOARD.md` only by a coordinator
task that explicitly claims the papers board. They are not active from this
package alone.

## csem-latex-evidence-directory-contract-2026-07-22

Role: Coordinator / Writer / Reviewer

Goal: Create a compact `evidence/` directory plan for the CSEM dissertation
that stores small external-writer packets, not raw CFD outputs.

Likely paths:

- `UTexas_Research/csem-Masters_dissertation/evidence/README.md`
- selected small packet files under `UTexas_Research/csem-Masters_dissertation/evidence/**`
- `.agent/status/csem-latex-evidence-directory-contract-2026-07-22.md`
- `.agent/journal/2026-07-22/csem-latex-evidence-directory-contract-2026-07-22.md`

Open first:

- `ethan_runs/work_products/2026-07/2026-07-22/2026-07-22_thesis_external_writer_evidence_packet_contract/README.md`
- `ethan_runs/work_products/2026-07/2026-07-22/2026-07-22_thesis_external_writer_evidence_packet_contract/latex_repo_compact_evidence_manifest.csv`

Validation: `scripts/check_guardrails.sh`; `scripts/build_thesis.sh` if any
LaTeX includes are changed.

Guardrail: do not copy native OpenFOAM outputs, raw sampled fields, broad
generated figure folders, or unreviewed work-product trees.

## csem-latex-ch4-evidence-packet-sync-2026-07-22

Role: Writer / Reviewer

Goal: Use the Chapter 1-4 foundations packet to update Chapter 4 prose and, if
approved, copy only the compact supporting packet into the dissertation
`evidence/` directory.

Likely paths:

- `UTexas_Research/csem-Masters_dissertation/chapters/04_cfd_to_1d_reduction.tex`
- optional `UTexas_Research/csem-Masters_dissertation/evidence/ch04_reduction_split_packet.md`
- `.agent/status/csem-latex-ch4-evidence-packet-sync-2026-07-22.md`
- `.agent/journal/2026-07-22/csem-latex-ch4-evidence-packet-sync-2026-07-22.md`

Guardrail: no coefficient admission, no final score claim, no runtime leakage.

## csem-latex-results-evidence-packet-review-2026-07-22

Role: Reviewer / Writer

Goal: Review the Chapter 7/8 results packet before prose expansion, confirming
which negative, diagnostic, and blocked results can be described in the actual
LaTeX.

Likely paths:

- read-only `UTexas_Research/csem-Masters_dissertation/chapters/07_reduced_cfd_evidence.tex`
- read-only `UTexas_Research/csem-Masters_dissertation/chapters/08_predictive_model_assessment.tex`
- optional small review note under `.agent/status/` and `.agent/journal/`

Guardrail: final predictive score values remain zero until a frozen candidate
exists.
