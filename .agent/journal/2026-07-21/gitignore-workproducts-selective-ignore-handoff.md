---
provenance:
  - .gitignore
  - .agent/status/2026-07-21_TODO-GITIGNORE-WORKPRODUCTS-SELECTIVE-IGNORE-HANDOFF-2026-07-21.md
tags: [cleanup, gitignore, work-products, handoff]
related:
  - operational_notes/07-26/21/2026-07-21_GITIGNORE_WORKPRODUCTS_SELECTIVE_IGNORE_HANDOFF.md
  - imports/2026-07-21_gitignore_workproducts_selective_ignore_handoff.json
task: TODO-GITIGNORE-WORKPRODUCTS-SELECTIVE-IGNORE-HANDOFF-2026-07-21
date: 2026-07-21
role: Cleaner/Coordinator/Writer
type: journal
status: complete
---
# Gitignore Work Products Selective Ignore Handoff

Task: `TODO-GITIGNORE-WORKPRODUCTS-SELECTIVE-IGNORE-HANDOFF-2026-07-21`

## Attempted

The cleanup started from the user request to make `git add` safe and avoid adding junk. A first broad ignore hid `work_products/*`, but the user correctly pushed back: `work_products` contains durable evidence packages, not only junk. I changed direction and treated `work_products` as a mixed tree.

## Observed

The full `work_products` tree has `8117` files and is about `40G`. The heavyweight files are mostly reconstructed OpenFOAM trees under `recon/`, VTK exports, cell-volume/mask/face row dumps, sampled interface/wall detail CSVs, and repeated generated figure PDFs. The useful files are package READMEs, manifests, summary JSON, analysis CSVs, SVG/PNG figures, small reports, and presentation artifacts.

After the selective policy, Git still sees `5830` untracked files under `work_products`, which is intentional. The largest visible files are now mostly multi-megabyte SVG time-series figures and a small PPTX, not solver payloads, raw detail CSVs, or large generated PDF fan-outs.

## Inferred

The right policy is not to ignore `work_products` as a class. It should expose reviewable research outputs while hiding regenerated or raw high-volume payloads. The current rules do that with a conservative allowlist for normal document/table/figure formats followed by targeted re-ignore rules for known heavy artifacts.

## Caveats

Some visible SVGs are still around `5M`. That is acceptable for now because they are likely useful review artifacts, but tomorrow's staging pass should still inspect the visible `work_products` packages before adding them. The `.gitignore` change makes accidental multi-GB staging much less likely; it does not mean every visible work product should be committed.

The broader worktree is still dirty from other agents. This task did not clean, delete, stage, commit, or push anything.

## Next Useful Actions

1. Review the `.gitignore` diff as its own logical commit candidate.
2. Run `git status --short -- .gitignore work_products figures figures_rendered scratchpad registry reports` before staging.
3. Stage only `.gitignore` and this handoff set first, then separately decide which visible `work_products` packages are durable enough to add.
4. Use `git check-ignore -v <path>` for any surprising visible or hidden artifact.
5. If visible `work_products` still includes repeated large exports, add a narrow ignore pattern for that generator rather than reintroducing `work_products/*`.
