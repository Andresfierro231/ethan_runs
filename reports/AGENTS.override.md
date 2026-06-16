# Reports Override

Read this after the repo-root `AGENTS.md` when working anywhere under
`reports/`.

## Scope

`reports/` is a dated package tree containing scientific summaries, figures,
CSV outputs, machine-readable summaries, and some manuscript-facing notes.

## Local rules

- Claim one dated report package at a time unless the coordinator records a
  broader package-refresh task.
- Treat each package `README.md` as the first local source of truth for what
  the package means and which upstream products it reuses.
- Distinguish generated outputs from interpretive prose. Manual edits are most
  appropriate for `README.md`, `scientific_*`, `presentation_takeaways.md`, and
  `slide_outline.md`.
- Prefer regenerating figures and CSVs through scripts rather than editing them
  by hand.
- Keep dated package names stable. Create a new dated package instead of
  silently rewriting the meaning of an older one unless the task is an explicit
  refresh of that package.
- When conclusions depend on current run state, cross-check recent
  `journals/`, `operational_notes/`, and continuation-diagnosis packages before
  tightening the wording.

## Important recurring contexts

- Salt usability and representative-case logic:
  `2026-06-04_all_salt_behavior_package/`
- Pressure-drop and resistance narrative:
  `2026-06-04_ethan_section_transport_package/`,
  `2026-06-05_ethan_wall_loss_resistance_coupling/`
- Continuation status and runtime interpretation:
  `2026-06-05_ethan_continuation_diagnosis/`
- Presentation/sponsor framing:
  `2026-06-08_ethan_presentation_figure_package/`,
  `2026-06-08_sponsor_salt_status_deck/`
