#!/usr/bin/env python3
"""Build thesis main-text write-up and table polish package."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_maintext_writeup_table_polish_pack"

SRC = {
    "s6_gate": ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s6_blocked_scorecard_shell/s0_s11_gate_flow_table.csv",
    "s6_scorecard": ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s6_blocked_scorecard_shell/blocked_scorecard_visual_table.csv",
    "s7_sensor": ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s7_sensor_map_overlay/sensor_overlay_table.csv",
    "s8_negative": ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s8_wall_test_section_axial_mixing_candidate/negative_or_admission_ready_summary.csv",
    "s9_exchange": ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s9_upcomer_exchange_evidence/exchange_qoi_figure_contract.csv",
    "s10_pressure": ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s10_pressure_f6_gate_waterfall/pressure_f6_gate_waterfall.csv",
    "s13_heat": ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_seeded_heat_path_lane_release/heat_path_lane_table.csv",
    "s14_scorecard": ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/f6_branch_use_scorecard.csv",
    "h2_waterfall": ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution/tw5_response_waterfall.csv",
    "velocity_ranges": ROOT / "work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/shared_velocity_ranges.csv",
    "velocity_analysis": ROOT / "work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/velocity_magnitude_side_z_thesis_analysis.md",
    "writer_handoff": ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_post_study_writing_refresh/thesis_writer_handoff.md",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def fmt_float(value: str, digits: int = 3) -> str:
    if value == "":
        return ""
    return f"{float(value):.{digits}f}"


def boolish_count(rows: list[dict[str, str]], field: str, value: str) -> int:
    return sum(1 for row in rows if row.get(field) == value)


def build_s6_gate(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    out = []
    for row in rows:
        out.append(
            {
                "gate": row["study_id"],
                "short_name": row["gate_name"],
                "main_text_status": row["status"].replace("_", " "),
                "thesis_message": row["thesis_visual_use"],
                "score_values_released": row["final_score_values_released"],
                "fit_or_selection": row["fit_or_model_selection_use"],
                "claim_boundary": "gate evidence only; no final predictive score",
            }
        )
    return out


def build_s7_sensor(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    by_class = Counter(row["acceptance_class"] for row in rows)
    by_kind = Counter(row["kind"] for row in rows)
    runtime_allowed = sum(1 for row in rows if not row["runtime_use"].startswith("forbidden"))
    fit_allowed = sum(1 for row in rows if not row["fit_use"].startswith("forbidden"))
    selection_allowed = sum(1 for row in rows if not row["model_selection_use"].startswith("forbidden"))
    return [
        {"policy_row": "sensor_count", "value": len(rows), "thesis_use": "TP/TW score-target inventory", "claim_boundary": "post-solve score targets only"},
        {"policy_row": "mapped", "value": by_class["mapped"], "thesis_use": "exact/projected map count", "claim_boundary": "mapping does not authorize runtime use"},
        {"policy_row": "bounded", "value": by_class["bounded"], "thesis_use": "bounded path-position evidence", "claim_boundary": "bounded probes remain score targets"},
        {"policy_row": "excluded", "value": by_class["excluded"], "thesis_use": "excluded sensor count", "claim_boundary": "excluded rows do not enter score"},
        {"policy_row": "tp_tw_split", "value": f"TP={by_kind['TP']}; TW={by_kind['TW']}", "thesis_use": "probe-family summary", "claim_boundary": "secondary to energy and branch heat parity"},
        {"policy_row": "runtime_permissions", "value": runtime_allowed, "thesis_use": "runtime leakage audit", "claim_boundary": "0 temperature runtime inputs"},
        {"policy_row": "fit_permissions", "value": fit_allowed, "thesis_use": "fit leakage audit", "claim_boundary": "0 TP/TW fit targets"},
        {"policy_row": "model_selection_permissions", "value": selection_allowed, "thesis_use": "model-selection leakage audit", "claim_boundary": "0 TP/TW model-selection permissions"},
    ]


def build_s10_pressure(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    out = []
    for row in rows:
        out.append(
            {
                "gate_order": row["gate_order"],
                "lane": row["lane"],
                "gate": row["gate_name"],
                "status": row["gate_status"],
                "admission_label": row["admission_label"],
                "blocks_admission": row["blocks_admission"],
                "reader_message": row["basis_requirement"],
                "claim_boundary": "diagnostic/non-admission; no component K, F6, clipped K, or hidden multiplier",
            }
        )
    return out


def build_s14_summary(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    use_counts = Counter(row["use_label"] for row in rows)
    admission_counts = Counter(row["admission_status"] for row in rows)
    future_lanes = sorted({row["branch_or_feature"] for row in rows if row["use_label"] == "future_candidate"})
    return [
        {"summary_row": "rows_scored", "value": len(rows), "thesis_use": "branch-use scorecard breadth", "claim_boundary": "diagnostic review only"},
        {"summary_row": "admitted_rows", "value": admission_counts["admitted"], "thesis_use": "admission status", "claim_boundary": "0 admitted pressure/F6 rows"},
        {"summary_row": "not_admitted_rows", "value": admission_counts["not_admitted"], "thesis_use": "non-admission status", "claim_boundary": "do not convert to F6/component K"},
        {"summary_row": "future_candidate_rows", "value": use_counts["future_candidate"], "thesis_use": "narrowed future ordinary lanes", "claim_boundary": "future-candidate only"},
        {"summary_row": "do_not_use_rows", "value": use_counts["do_not_use"], "thesis_use": "excluded ordinary F6/component-K use", "claim_boundary": "appendix can carry full details"},
        {"summary_row": "preferred_future_lanes", "value": ";".join(future_lanes), "thesis_use": "future work target", "claim_boundary": "not current admission"},
    ]


def build_h2_response(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    out = []
    for row in rows:
        out.append(
            {
                "case": row["stage"],
                "kind": row["sensitivity_kind"],
                "description": row["description"],
                "tw5_abs_residual_K": fmt_float(row["tw5_abs_residual_K"]),
                "tw5_improvement_K": fmt_float(row["tw5_abs_improvement_vs_phase_e_K"]),
                "all_probe_mae_K": fmt_float(row["all_mae_K"]),
                "all_probe_mae_delta_K": fmt_float(row["delta_all_mae_vs_phase_e_K"]),
                "interpretation": row["interpretation"],
                "claim_boundary": "train-only diagnostic; no repair, freeze, validation, holdout, external score, or passive-hA fit",
            }
        )
    return out


def build_s9_exchange(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    return [
        {
            "qoi": row["qoi_name"],
            "model_role": row["model_role"],
            "current_status": row["current_status"],
            "existing_rows": row["available_existing_rows"],
            "new_sampling_needed": row["requires_new_sampler_or_harvest"],
            "admission_now": row["admission_use_now"],
            "claim_boundary": "requirement row only; no exchange-cell coefficient admission",
        }
        for row in rows
    ]


def build_s13_heat(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    return [
        {
            "lane": row["heat_path_lane"],
            "current_status": row["current_status"],
            "allowed_inputs": row["allowed_inputs"],
            "blocked_or_forbidden": row["forbidden_inputs"],
            "needed_before_claim": row["required_before_claim"],
            "release_status": row["release_status"],
        }
        for row in rows
    ]


def write_text(name: str, text: str) -> None:
    (OUT / name).write_text(text.strip() + "\n", encoding="utf-8")


def build_markdown_outputs(summary: dict[str, object]) -> None:
    write_text(
        "negative_results_scientific_contribution.md",
        f"""
---
provenance:
  - {rel(SRC['s8_negative'])}
  - {rel(SRC['s9_exchange'])}
  - {rel(SRC['s10_pressure'])}
  - {rel(SRC['s14_scorecard'])}
  - {rel(SRC['h2_waterfall'])}
tags: [thesis, negative-results, admission, csem]
task: TODO-THESIS-MAINTEXT-WRITEUP-TABLE-POLISH-PACK-2026-07-21
date: 2026-07-21
role: Writer/Reviewer
type: work_product
status: complete
---
# Negative Results As A Thesis Contribution

The current negative results are not failed attempts to hide in an appendix.
They are the evidence that keeps the reduced model from becoming a tuned replay
of the CFD. S8, S9, S10, S13, S14, and H2 each remove a tempting shortcut and
replace it with a narrower physical requirement.

S8 shows that the current wall/test-section and axial-mixing candidate family
does not produce an S11-ready candidate. Its result is a falsification of the
available setup-only candidates, not a statement that wall physics is
irrelevant. S9 shows that the upcomer cannot be treated as an ordinary
single-stream pipe while exchange-state variables remain missing or
uncertain. S10 and S14 show that finite pressure evidence does not become an
ordinary component `K` or F6 correction when pressure basis, ordinary-flow,
component isolation, and same-QOI UQ gates fail. H2 shows that passive heat
loss is responsive, but the response is broad enough that an independent
physical basis is required before any repair.

The thesis claim is therefore methodological and scientific: the workflow
turns high-fidelity CFD evidence into a controlled admission ledger. It records
which rows can explain a residual, which rows can motivate a model-form slot,
which rows are score-only, and which rows are forbidden as predictive inputs.
The blocked scorecard is part of that result because it prevents a premature
accuracy number before a runtime-legal candidate exists.
""",
    )

    write_text(
        "upcomer_physics_subsection.md",
        f"""
---
provenance:
  - {rel(SRC['velocity_analysis'])}
  - {rel(SRC['velocity_ranges'])}
  - {rel(SRC['s9_exchange'])}
  - {rel(SRC['s13_heat'])}
tags: [thesis, upcomer, recirculation, velocity-figure]
task: TODO-THESIS-MAINTEXT-WRITEUP-TABLE-POLISH-PACK-2026-07-21
date: 2026-07-21
role: Writer/Reviewer
type: work_product
status: complete
---
# Upcomer Velocity Behavior And Model-Form Meaning

The matched Salt1-Salt4 upcomer velocity figure should be read as a model-form
diagnostic. The shared axis and velocity range make the cases comparable, and
the resultant speed panels show that the upcomer is not a uniform one-stream
pipe. High-speed paths coexist with weak-flow or downward-flow regions. This is
the visual reason ordinary upcomer `Nu`, `f_D`, and `K` labels remain unsafe
for the current recirculating evidence.

The physical interpretation is a throughflow-plus-exchange structure. The main
circulation still carries net loop flow, but local buoyancy, pressure recovery,
geometry, and heat-path coupling allow part of the upcomer volume to exchange
with slower or reversed regions. A one-dimensional model can represent that
only by adding a recirculation/exchange lane or by explicitly disabling
ordinary single-stream closure language where recirculation is material.

The figure does not by itself provide a recirculation fraction, exchange mass
flow, residence time, or exchange-cell coefficient. Those require same-window
`V_recirc`, `mdot_exchange`, `tau_recirc`, wall/core/bulk temperature contrast,
pressure/energy residual support, and same-QOI UQ. The current image is
therefore thesis-ready as diagnostic visual evidence, while the S9/S13 tables
define the missing quantitative evidence needed before admission.
""",
    )

    write_text(
        "pressure_f6_sidebar.md",
        f"""
---
provenance:
  - {rel(SRC['s10_pressure'])}
  - {rel(SRC['s14_scorecard'])}
tags: [thesis, pressure, F6, non-admission]
task: TODO-THESIS-MAINTEXT-WRITEUP-TABLE-POLISH-PACK-2026-07-21
date: 2026-07-21
role: Writer/Reviewer
type: work_product
status: complete
---
# Sidebar: Why Finite Pressure Evidence Is Not An Admitted `K`

The pressure evidence is useful precisely because it is decomposed before a
coefficient label is assigned. A finite pressure difference across a natural
circulation feature includes hydrostatic contribution, kinetic change,
straight/developing reference loss, local recovery or residual behavior, and
recirculation effects. If these terms are not separated, an apparent local
loss coefficient can absorb the wrong physics.

The current lower-right corner evidence passes some pressure-basis checks, but
it fails ordinary component admission. The velocity or reference-pressure basis
is invalid under material reverse flow, component isolation is not available,
same-basis straight/developing references are missing, and same-QOI UQ is not
accepted. The S14 branch-use scorecard broadens this conclusion: current
pressure/F6 rows are diagnostic, future-candidate, or do-not-use rows, with no
admitted component-K or F6 row.

The allowed result statement is conservative: the evidence motivates a
section-effective or hybrid pressure-residual lane. It does not authorize a
clipped `K`, hidden global multiplier, ordinary component `K`, cluster `K`, or
F6 recorrection.
""",
    )

    write_text(
        "thermal_attribution_subsection.md",
        f"""
---
provenance:
  - {rel(SRC['h2_waterfall'])}
tags: [thesis, thermal, heat-loss, passive-boundary]
task: TODO-THESIS-MAINTEXT-WRITEUP-TABLE-POLISH-PACK-2026-07-21
date: 2026-07-21
role: Writer/Reviewer
type: work_product
status: complete
---
# Thermal Attribution And Passive Heat-Loss Interpretation

The H2 passive heat-loss result is a diagnostic attribution result, not a
repair. The Phase E/F-J baseline has a large TW5 residual. Local lower-leg
passive `hA` changes move the residual only weakly, while a global passive
`hA` reduction produces a much larger TW5 and all-probe response. This pattern
is scientifically useful because it says the residual is heat-path responsive
and broad, rather than isolated to a single lower-leg multiplier.

The broad response is also why the result is not admissible as a fitted
passive `hA`. A global multiplier would improve the train diagnostic for the
wrong thesis reason if it were introduced without independent setup, geometry,
or literature basis. The current result localizes the next uncertainty to
external heat-path physical basis, source/sink distribution, or missing
redistribution physics.

The thesis should present this as residual ownership and candidate
predeclaration evidence. It should not present it as passive-wall closure,
repair execution, validation/holdout/external score, freeze, or final
predictive accuracy.
""",
    )

    write_text(
        "runtime_leakage_methods_box.md",
        f"""
---
provenance:
  - {rel(SRC['writer_handoff'])}
tags: [thesis, runtime-leakage, methods-box]
task: TODO-THESIS-MAINTEXT-WRITEUP-TABLE-POLISH-PACK-2026-07-21
date: 2026-07-21
role: Writer/Reviewer
type: work_product
status: complete
---
# Methods Box: Runtime Inputs Versus Diagnostic Evidence

| Category | Allowed thesis use | Forbidden predictive-runtime use |
| --- | --- | --- |
| Geometry and setup fields | Runtime model inputs when source-backed. | Fill missing setup fields from scored CFD response. |
| External boundary dictionary | Setup-facing heat-path model inputs. | Realized CFD `wallHeatFlux` as runtime heat loss. |
| CFD pressure and heat fields | Targets, diagnostics, residual ownership, admission gates. | Pressure/heat target from the scored row as a model input. |
| CFD mass flow | Score target or diagnostic reference. | Runtime `mdot` input for prediction. |
| TP/TW temperatures | Post-solve score targets and residual diagnostics. | Runtime temperature input, fit target, or model-selection signal. |
| Holdout and external rows | Post-freeze scoring only. | Fitting, tuning, model selection, or candidate choice. |

This separation is the difference between a CFD-informed reduced model and a
CFD replay. A row can explain a residual without being legal as a runtime
input.
""",
    )

    write_text(
        "blocked_scorecard_and_future_work_figure.md",
        f"""
---
provenance:
  - {rel(SRC['s6_scorecard'])}
  - {rel(SRC['s9_exchange'])}
  - {rel(SRC['s10_pressure'])}
  - {rel(SRC['h2_waterfall'])}
tags: [thesis, figure-draft, blocked-scorecard, future-work]
task: TODO-THESIS-MAINTEXT-WRITEUP-TABLE-POLISH-PACK-2026-07-21
date: 2026-07-21
role: Writer/Reviewer/Figures
type: work_product
status: complete
---
# Figure Draft: Blocked Scorecard And Future-Work Release Path

```mermaid
flowchart LR
    A[Current CFD evidence] --> B[Admission gates]
    B --> C{{Runtime-legal candidate named?}}
    C -- No --> D[Blocked scorecard shell: 0 final scores]
    C -- Yes --> E[S11 source/property refresh]
    E --> F[S15 freeze/release decision]
    F --> G[S6 final scorecard]

    H[S13 exchange harvest + same-QOI UQ] --> C
    I[Passive heat-loss physical basis] --> C
    J[Right-leg/test-section pressure anchors] --> C
```

Caption draft: The final scorecard is intentionally blocked until exactly one
runtime-legal candidate passes source/property, split, and uncertainty gates.
The next release paths are not broad tuning sweeps: they are S13 exchange
harvest/UQ, passive heat-loss physical-basis evidence, and ordinary pressure
anchors in `right_leg` or `test_section_span`. No final predictive score is
released from the current evidence.
""",
    )

    write_text(
        "caption_bank.md",
        f"""
---
provenance:
  - {rel(SRC['velocity_analysis'])}
  - {rel(SRC['s6_gate'])}
  - {rel(SRC['s10_pressure'])}
  - {rel(SRC['s14_scorecard'])}
  - {rel(SRC['h2_waterfall'])}
tags: [thesis, captions, figure-table-polish]
task: TODO-THESIS-MAINTEXT-WRITEUP-TABLE-POLISH-PACK-2026-07-21
date: 2026-07-21
role: Writer/Reviewer
type: work_product
status: complete
---
# Caption Bank

**Matched upcomer velocity figure.** Matched Salt1-Salt4 side-view upcomer
velocity magnitude under a shared scale. The panels show asymmetric high-speed
and weak or downward-flow regions, motivating a throughflow-plus-exchange
model form. Diagnostic visual evidence only; no ordinary upcomer `Nu`, `f_D`,
`K`, recirculation fraction, or exchange-cell coefficient is admitted.

**S6 blocked scorecard shell.** Gate-flow summary for the current predictive
path. The empty final score cells are intentional: no runtime-legal candidate
has been frozen, and no protected holdout or external row is released for
model selection.

**S10 pressure/F6 waterfall.** Ordered pressure and F6 admission gates for the
current candidate rows. Finite pressure evidence remains diagnostic when
ordinary-flow, component-isolation, straight-reference, source-envelope, and
same-QOI uncertainty gates fail.

**S14 branch-use summary.** Pressure/F6 branch-use scorecard summarizing
diagnostic, future-candidate, and do-not-use rows. `right_leg` and
`test_section_span` are future ordinary lanes, not admitted current
coefficients.

**H2 passive heat-loss response.** Train-only passive heat-loss sensitivity
showing broad heat-path response. The result motivates physical-basis recovery
for passive heat loss; it does not admit a global passive `hA` fit, repair,
freeze, validation score, holdout score, external score, or final prediction.
""",
    )

    write_text(
        "README.md",
        f"""
---
provenance:
  - {rel(SRC['writer_handoff'])}
  - {rel(SRC['s6_gate'])}
  - {rel(SRC['s7_sensor'])}
  - {rel(SRC['s8_negative'])}
  - {rel(SRC['s9_exchange'])}
  - {rel(SRC['s10_pressure'])}
  - {rel(SRC['s13_heat'])}
  - {rel(SRC['s14_scorecard'])}
  - {rel(SRC['h2_waterfall'])}
tags: [thesis, main-text, polish, tables, writeup]
related:
  - .agent/status/2026-07-21_TODO-THESIS-MAINTEXT-WRITEUP-TABLE-POLISH-PACK-2026-07-21.md
  - .agent/journal/2026-07-21/thesis-maintext-writeup-table-polish-pack.md
task: TODO-THESIS-MAINTEXT-WRITEUP-TABLE-POLISH-PACK-2026-07-21
date: 2026-07-21
role: Writer/Reviewer/Tester
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Thesis Main-Text Write-Up And Table Polish Pack

## Purpose

This package executes the thesis-facing polish plan without editing the LaTeX
repository or current thesis body. It converts existing ledgers into compact
main-text tables, drafts copy-ready explanatory sections, and supplies a
caption bank plus blocked-scorecard/future-work figure draft.

## Outputs

- `main_text_table_s6_gate_flow.csv`
- `main_text_table_s7_sensor_policy.csv`
- `main_text_table_s9_exchange_requirements.csv`
- `main_text_table_s10_pressure_gate_waterfall.csv`
- `main_text_table_s13_exchange_scaffold.csv`
- `main_text_table_s14_branch_use_summary.csv`
- `main_text_table_h2_passive_heat_response.csv`
- `runtime_input_methods_table.csv`
- `latex_import_manifest.csv`
- `negative_results_scientific_contribution.md`
- `upcomer_physics_subsection.md`
- `pressure_f6_sidebar.md`
- `thermal_attribution_subsection.md`
- `runtime_leakage_methods_box.md`
- `blocked_scorecard_and_future_work_figure.md`
- `caption_bank.md`
- `source_manifest.csv`
- `summary.json`

## Result

The thesis writer now has compact main-text entry points for the highest-value
current evidence: upcomer velocity behavior, S6 blocked scorecard, S7 sensor
policy, S8/S9/S10/S13/S14 negative or diagnostic results, H2 passive heat-loss
attribution, runtime leakage discipline, and the future-work release path.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
Fluid source, external repository, LaTeX file, blocker register, fitting/model
selection, source/property release, closure admission, final score, validation,
holdout, external-test score, or runtime-leakage rule changed.
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    s6_gate = read_csv(SRC["s6_gate"])
    s7_sensor = read_csv(SRC["s7_sensor"])
    s9_exchange = read_csv(SRC["s9_exchange"])
    s10_pressure = read_csv(SRC["s10_pressure"])
    s13_heat = read_csv(SRC["s13_heat"])
    s14_scorecard = read_csv(SRC["s14_scorecard"])
    h2_waterfall = read_csv(SRC["h2_waterfall"])

    write_csv(OUT / "main_text_table_s6_gate_flow.csv", ["gate", "short_name", "main_text_status", "thesis_message", "score_values_released", "fit_or_selection", "claim_boundary"], build_s6_gate(s6_gate))
    write_csv(OUT / "main_text_table_s7_sensor_policy.csv", ["policy_row", "value", "thesis_use", "claim_boundary"], build_s7_sensor(s7_sensor))
    write_csv(OUT / "main_text_table_s9_exchange_requirements.csv", ["qoi", "model_role", "current_status", "existing_rows", "new_sampling_needed", "admission_now", "claim_boundary"], build_s9_exchange(s9_exchange))
    write_csv(OUT / "main_text_table_s10_pressure_gate_waterfall.csv", ["gate_order", "lane", "gate", "status", "admission_label", "blocks_admission", "reader_message", "claim_boundary"], build_s10_pressure(s10_pressure))
    write_csv(OUT / "main_text_table_s13_exchange_scaffold.csv", ["lane", "current_status", "allowed_inputs", "blocked_or_forbidden", "needed_before_claim", "release_status"], build_s13_heat(s13_heat))
    write_csv(OUT / "main_text_table_s14_branch_use_summary.csv", ["summary_row", "value", "thesis_use", "claim_boundary"], build_s14_summary(s14_scorecard))
    write_csv(OUT / "main_text_table_h2_passive_heat_response.csv", ["case", "kind", "description", "tw5_abs_residual_K", "tw5_improvement_K", "all_probe_mae_K", "all_probe_mae_delta_K", "interpretation", "claim_boundary"], build_h2_response(h2_waterfall))

    runtime_rows = [
        {"category": "setup_geometry", "allowed_use": "runtime model input when source-backed", "forbidden_use": "fill missing setup fields from scored CFD response"},
        {"category": "external_boundary_dictionary", "allowed_use": "setup-facing heat-path input", "forbidden_use": "realized CFD wallHeatFlux as runtime heat loss"},
        {"category": "CFD_pressure_heat_fields", "allowed_use": "target, diagnostic, residual ownership, admission gate", "forbidden_use": "scored-row pressure/heat as model input"},
        {"category": "CFD_mdot", "allowed_use": "score target or diagnostic reference", "forbidden_use": "runtime mass-flow input"},
        {"category": "TP_TW_temperatures", "allowed_use": "post-solve score target and residual diagnostic", "forbidden_use": "runtime input, fit target, or model-selection signal"},
        {"category": "holdout_external_rows", "allowed_use": "post-freeze scoring only", "forbidden_use": "fitting, tuning, model selection, or candidate choice"},
    ]
    write_csv(OUT / "runtime_input_methods_table.csv", ["category", "allowed_use", "forbidden_use"], runtime_rows)

    import_rows = [
        {"chapter": "Ch5/Ch7", "artifact": "upcomer_physics_subsection.md", "writer_action": "import as explanatory subsection beside matched upcomer figure", "claim_boundary": "diagnostic visual evidence"},
        {"chapter": "Ch6", "artifact": "main_text_table_s6_gate_flow.csv", "writer_action": "format as compact gate-flow table or figure", "claim_boundary": "0 final score values"},
        {"chapter": "Ch6", "artifact": "main_text_table_s7_sensor_policy.csv", "writer_action": "format as score-only sensor policy table", "claim_boundary": "0 runtime/fit/model-selection permissions"},
        {"chapter": "Ch6/Ch7", "artifact": "main_text_table_s9_exchange_requirements.csv", "writer_action": "pair with F03 upcomer schematic", "claim_boundary": "requirements only, no exchange-cell coefficient"},
        {"chapter": "Ch7", "artifact": "negative_results_scientific_contribution.md", "writer_action": "use as bridge from diagnostics to blocked scorecard", "claim_boundary": "negative result is not admission"},
        {"chapter": "Ch7", "artifact": "pressure_f6_sidebar.md", "writer_action": "insert as pressure/F6 sidebar", "claim_boundary": "no component K, F6, clipped K, or hidden multiplier"},
        {"chapter": "Ch7", "artifact": "thermal_attribution_subsection.md", "writer_action": "insert as passive heat-loss attribution result", "claim_boundary": "train-only diagnostic"},
        {"chapter": "Ch8", "artifact": "blocked_scorecard_and_future_work_figure.md", "writer_action": "render mermaid or redraw as thesis flowchart", "claim_boundary": "future-work path, no final score"},
    ]
    write_csv(OUT / "latex_import_manifest.csv", ["chapter", "artifact", "writer_action", "claim_boundary"], import_rows)

    source_rows = [{"source_id": key, "path": rel(path), "used_for": key, "mutation_status": "read_only"} for key, path in SRC.items()]
    write_csv(OUT / "source_manifest.csv", ["source_id", "path", "used_for", "mutation_status"], source_rows)

    summary = {
        "task": "TODO-THESIS-MAINTEXT-WRITEUP-TABLE-POLISH-PACK-2026-07-21",
        "date": "2026-07-21",
        "status": "complete",
        "s6_gate_rows": len(s6_gate),
        "s7_sensor_rows": len(s7_sensor),
        "s9_exchange_rows": len(s9_exchange),
        "s10_pressure_rows": len(s10_pressure),
        "s13_heat_rows": len(s13_heat),
        "s14_scorecard_rows": len(s14_scorecard),
        "h2_response_rows": len(h2_waterfall),
        "main_text_tables": 8,
        "writeup_sections": 6,
        "latex_import_rows": len(import_rows),
        "runtime_leakage_relaxed": False,
        "closure_admission": False,
        "final_score_claim": False,
        "native_outputs_mutated": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    build_markdown_outputs(summary)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
