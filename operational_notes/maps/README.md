---
task: AGENT-294
date: 2026-07-13
role: Coordinator/Writer
type: map
status: reference
tags: [map-of-content, research-index, provenance, thesis-source]
related:
  - operational_notes/07-26/13/2026-07-13_external_report_research_index_and_blocker_audit.md
  - operational_notes/07-26/13/2026-07-13_CURRENT_CLOSURE_AND_PREDICTIVE_MODEL_START_HERE.md
  - .agent/STATE.md
  - .agent/BLOCKERS.md
---
# Topic Maps of Content (MOCs)

These are **living hub notes** — one per durable research theme. Each is the
canonical entry point to its thread: what's trusted, what's open, every research
avenue tried (with outcome + provenance), and the key artifacts. An agent (or a
thesis writer) starting on a topic should read that topic's hub first and follow
its links, instead of grepping ~1000 docs.

Unlike dated notes, these are **updated in place** as the thread evolves. Keep them
short (pointers + one-line status), not a copy of the packages they link to. When
a hub's thread produces a new durable result, add a link and update the status
line; when a claim is overturned, update it here and set `superseded_by` on the
old doc.

## The maps

| Topic | Hub | Primary tags |
|---|---|---|
| Friction closures | `friction-closures.md` | #friction #closure-ledger |
| Thermal closures & internal Nu | `thermal-closures-and-internal-nu.md` | #thermal-closure #internal-nu |
| Mesh, GCI & uncertainty | `mesh-gci-and-uncertainty.md` | #mesh-gci #uncertainty |
| Forward predictive model | `forward-predictive-model.md` | #forward-model #predictive-1d |
| CFD runs & admission | `cfd-runs-and-admission.md` | #salt-q-perturbation #admission #steady-state |
| Pressure & momentum budget | `pressure-and-momentum-budget.md` | #pressure-ledger #momentum-budget |
| Geometry & mesh truth | `geometry-and-mesh-truth.md` | #geometry #mesh-truth |
| Thermal boundary & radiation | `thermal-boundary-and-radiation.md` | #thermal-parity #rcExternalTemperature #radiation |
| Literature synthesis & gates | `literature-synthesis-and-gates.md` | #litrev-synthesis #closure-ledger |
| Latest LitRev modeling handoff | `../../reports/2026-07/2026-07-22/2026-07-22_litrev_latest_modeling_handoff/README.md` | #litrev-synthesis #model-forms #source-gates |
| Thesis and weekly presentation dossier | `../../reports/thesis_dossier/README.md` | #thesis-dossier #weekly-presentation #thesis-source |
| Project mission & scientific questions | `../07-26/14/2026-07-14_PROJECT_MISSION_AND_SCIENTIFIC_QUESTIONS.md` | #mission #scientific-questions #coordination |
| Agent operations & repo efficiency | `agent-operations.md` | #agent-operations #coordination #tooling |

## How this fits the generated index

- `.agent/STATE.md`, `.agent/catalog.json/csv`, `.agent/BLOCKERS.md` are
  **machine-generated** by `tools/docs/build_repo_index.py` and cannot drift.
- These MOCs are the **human/agent-curated** layer on top: narrative threads and
  the "why", cross-linked to the generated facts.
- Frontmatter schema that powers both: `.agent/DOC_FRONTMATTER_SCHEMA.md`.

## Related

- `operational_notes/07-26/13/2026-07-13_external_report_research_index_and_blocker_audit.md`
- `operational_notes/07-26/14/2026-07-14_PROJECT_MISSION_AND_SCIENTIFIC_QUESTIONS.md`
- `reports/2026-07/2026-07-22/2026-07-22_litrev_latest_modeling_handoff/README.md`
- `reports/thesis_dossier/README.md`
- `.agent/STATE.md`
- `.agent/BLOCKERS.md`
- `.agent/DOC_FRONTMATTER_SCHEMA.md`
