#!/usr/bin/env python3
"""Build report and presentation outline for mdot vs TP/TW error audit."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
TASK = "AGENT-420"
DATE = "2026-07-15"
SRC = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit"
OUT = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_mdot_temperature_error_report_and_presentation"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str] | None = None) -> int:
    materialized = list(rows)
    if fieldnames is None:
        fieldnames = list(materialized[0].keys()) if materialized else []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(materialized)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def fmt(value: Any, digits: int = 3) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(number):
        return ""
    return f"{number:.{digits}f}".rstrip("0").rstrip(".")


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else math.nan


def mode_label(mode_id: str) -> str:
    labels = {
        "M1_full_cfd_segment_heat_flux_pressure_root": "M1 full CFD segment heat ledger, pressure-root mdot",
        "M1b_full_cfd_segment_heat_flux_fixed_mdot": "M1b full CFD segment heat ledger, fixed CFD mdot",
        "M2_cfd_heater_test_section_cooler_pressure_root": "M2 CFD heater + test-section net + cooler, pressure-root mdot",
        "M3_cfd_heater_cooler_pressure_root": "M3 CFD heater + cooler only, pressure-root mdot",
    }
    return labels.get(mode_id, mode_id)


def load() -> dict[str, Any]:
    return {
        "summary": json.loads((SRC / "summary.json").read_text(encoding="utf-8")),
        "cases": read_csv(SRC / "case_admission_and_use_table.csv"),
        "modes": read_csv(SRC / "model_mode_matrix.csv"),
        "mdot": read_csv(SRC / "mdot_error_summary.csv"),
        "temps": read_csv(SRC / "temperature_probe_error_summary.csv"),
        "sensor": read_csv(SRC / "sensor_level_errors.csv"),
        "corr": read_csv(SRC / "mdot_temperature_error_correlation.csv"),
        "trends": read_csv(SRC / "trend_conclusion_register.csv"),
        "test_section": read_csv(SRC / "part3_test_section_error_increment.csv"),
        "cooling": read_csv(SRC / "part4_cooling_rmse_summary.csv"),
        "heating": read_csv(SRC / "part5_heating_rmse_summary.csv"),
        "assumptions": read_csv(SRC / "study_assumption_register.csv"),
    }


def executed_non_salt1(rows: list[dict[str, str]], mode_id: str) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("mode_id") == mode_id and row.get("case_id") != "salt_1" and row.get("result_status") == "executed"
    ]


def all_probe_rows(temps: list[dict[str, str]], mode_id: str) -> list[dict[str, str]]:
    return [row for row in temps if row.get("mode_id") == mode_id and row.get("case_id") != "salt_1" and row.get("kind") == "all"]


def build_mode_summary(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for mode in data["modes"]:
        mode_id = mode["mode_id"]
        mdot_rows = executed_non_salt1(data["mdot"], mode_id)
        temp_rows = all_probe_rows(data["temps"], mode_id)
        rows.append(
            {
                "mode_id": mode_id,
                "part": mode["part"],
                "label": mode_label(mode_id),
                "predictivity_class": mode["predictivity_class"],
                "uses_cfd_mdot_runtime": mode["uses_cfd_mdot_runtime"],
                "uses_realized_cfd_wallHeatFlux_runtime": mode["uses_realized_cfd_wallHeatFlux_runtime"],
                "n_executed_non_salt1": len(mdot_rows),
                "mean_abs_mdot_error_pct": fmt(mean([abs(float(row["mdot_error_pct"])) for row in mdot_rows])),
                "mean_abs_mdot_error_kg_s": fmt(mean([abs(float(row["mdot_error_kg_s"])) for row in mdot_rows]), 6),
                "mean_all_probe_rmse_K": fmt(mean([float(row["rmse_K"]) for row in temp_rows])),
                "runtime_input_policy": mode["runtime_input_policy"],
                "closure_terms": mode["closure_terms"],
                "admission_note": (
                    "diagnostic only: consumes CFD mdot"
                    if mode["uses_cfd_mdot_runtime"] == "yes"
                    else "diagnostic CFD-informed mode: not setup-only predictive"
                    if mode["uses_realized_cfd_wallHeatFlux_runtime"] == "yes"
                    else "candidate setup-only mode"
                ),
            }
        )
    return rows


def build_case_mode_table(data: dict[str, Any]) -> list[dict[str, Any]]:
    temp_by_key = {
        (row["case_id"], row["mode_id"], row["kind"]): row
        for row in data["temps"]
    }
    rows: list[dict[str, Any]] = []
    for row in data["mdot"]:
        if row["case_id"] == "salt_1" or row["result_status"] != "executed":
            continue
        all_t = temp_by_key.get((row["case_id"], row["mode_id"], "all"), {})
        tp_t = temp_by_key.get((row["case_id"], row["mode_id"], "TP"), {})
        tw_t = temp_by_key.get((row["case_id"], row["mode_id"], "TW"), {})
        rows.append(
            {
                "case_id": row["case_id"],
                "split": row["split"],
                "mode_id": row["mode_id"],
                "part": row["part"],
                "mdot_pred_kg_s": row["mdot_pred_kg_s"],
                "cfd_mdot_kg_s": row["cfd_mdot_kg_s"],
                "mdot_error_pct": fmt(row["mdot_error_pct"]),
                "all_probe_rmse_K": fmt(all_t.get("rmse_K", "")),
                "tp_rmse_K": fmt(tp_t.get("rmse_K", "")),
                "tw_rmse_K": fmt(tw_t.get("rmse_K", "")),
                "Tmean_error_K": fmt(row["Tmean_error_K"]),
                "loop_delta_error_K": fmt(row["loop_delta_error_K"]),
                "admission_use_class": row["admission_use_class"],
            }
        )
    return rows


def build_key_findings(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for trend in data["trends"]:
        rows.append(
            {
                "finding_id": trend["finding_id"],
                "topic": trend["topic"],
                "observation": trend["observation"],
                "interpretation": trend["interpretation"],
                "recommended_next_action": trend["next_action"],
                "evidence_file": trend["evidence_file"],
            }
        )
    return rows


def build_figure_plan(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "figure_id": "FIG-01",
            "title": "mdot absolute error vs all-probe TP/TW RMSE",
            "status": "available_existing",
            "source_or_creation_note": rel(SRC / "figures/mdot_error_vs_probe_rmse.svg"),
            "message": "The current association is descriptive: Pearson r=0.47 across pressure-root non-Salt1 rows, not a causal fit objective.",
        },
        {
            "figure_id": "FIG-02",
            "title": "Boundary-mode ladder: mdot error and all-probe RMSE",
            "status": "create_from_summary_table",
            "source_or_creation_note": "Use boundary_mode_performance_summary.csv; grouped bars for M1/M2/M3 mean abs mdot error pct and mean all-probe RMSE.",
            "message": "More CFD boundary information does not monotonically improve both hydraulic and thermal metrics.",
        },
        {
            "figure_id": "FIG-03",
            "title": "Per-case Part2 vs Part3 tradeoff",
            "status": "create_from_existing_audit_csv",
            "source_or_creation_note": rel(SRC / "part3_test_section_error_increment.csv"),
            "message": "Omitting the test-section term improves probe RMSE but worsens mdot error in the current model form.",
        },
        {
            "figure_id": "FIG-04",
            "title": "Cooling-leg heat removed RMSE by model form",
            "status": "create_from_existing_audit_csv",
            "source_or_creation_note": rel(SRC / "part4_cooling_rmse_summary.csv"),
            "message": "The current cooler model under-removes heat by about 103 W RMSE; Salt2-fit constant-UA bulk-drive transfers much better.",
        },
        {
            "figure_id": "FIG-05",
            "title": "Heating-leg heat added RMSE by model form",
            "status": "create_from_existing_audit_csv",
            "source_or_creation_note": rel(SRC / "part5_heating_rmse_summary.csv"),
            "message": "A scalar heater-efficiency model is a tractable improvement candidate, but must become setup-only before admission.",
        },
        {
            "figure_id": "FIG-06",
            "title": "Evidence ladder and admission status",
            "status": "create_as_schematic",
            "source_or_creation_note": "Use model_mode_matrix.csv, study_assumption_register.csv, and final report Section 2.",
            "message": "Separate diagnostic CFD-informed modes from setup-only predictive evidence.",
        },
    ]


def sensor_set(data: dict[str, Any], kind: str) -> str:
    return ", ".join(sorted({row["sensor"] for row in data["sensor"] if row["kind"] == kind}))


def first_row(rows: list[dict[str, str]], **criteria: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(k) == v for k, v in criteria.items()):
            return row
    return {}


def report_text(data: dict[str, Any], mode_summary: list[dict[str, Any]], key_findings: list[dict[str, Any]]) -> str:
    corr = first_row(data["corr"], scope="all_non_salt1", part="all_parts", mode_id="all_modes", kind="all")
    cooling_current = first_row(data["cooling"], part="part4", model_form="current_fluid_airside_hx_fixed_mdot", scope="all_non_salt1")
    cooling_fit = first_row(data["cooling"], part="part4", model_form="salt2_fit_constant_UA_bulk_drive", scope="all_non_salt1")
    heating_current = first_row(data["heating"], part="part5", model_form="electrical_heater_power_1_to_1", scope="all_non_salt1")
    heating_fit = first_row(data["heating"], part="part5", model_form="salt2_fit_constant_heater_efficiency", scope="all_non_salt1")
    m1 = next(row for row in mode_summary if row["mode_id"] == "M1_full_cfd_segment_heat_flux_pressure_root")
    m2 = next(row for row in mode_summary if row["mode_id"] == "M2_cfd_heater_test_section_cooler_pressure_root")
    m3 = next(row for row in mode_summary if row["mode_id"] == "M3_cfd_heater_cooler_pressure_root")
    assumptions = "\n".join(
        f"- `{row['assumption_id']}` {row['topic']}: {row['statement']} Risk: {row['risk_or_consequence']}"
        for row in data["assumptions"]
    )
    mode_lines = "\n".join(
        f"| `{row['mode_id']}` | {row['part']} | {row['predictivity_class']} | {row['uses_cfd_mdot_runtime']} | {row['uses_realized_cfd_wallHeatFlux_runtime']} | {row['mean_abs_mdot_error_pct']} | {row['mean_all_probe_rmse_K']} |"
        for row in mode_summary
    )
    finding_lines = "\n".join(
        f"- **{row['finding_id']} {row['topic']}.** {row['observation']} Interpretation: {row['interpretation']} Next: {row['recommended_next_action']}"
        for row in key_findings
    )
    return f"""# mdot Error vs TP/TW Temperature Error: Report-Ready Synthesis

## Executive Summary

This report synthesizes the AGENT-360 audit of the current 1D model against
Salt-family CFD. The audit compares mass-flow error (`mdot`) with TP/TW
temperature-probe error under a ladder of boundary-condition modes. The central
result is that hydraulic and thermal errors are coupled, but not in a way that
can be collapsed to a single scalar correction. Boundary choices move mdot,
mean thermal state, loop temperature rise, and local probe errors in different
directions.

The best current diagnostic boundary subset is **M2**, which imposes CFD heater
heat entry, CFD test-section net heat, and CFD cooler heat removal while solving
mdot from pressure balance. Across Salt2/Salt3/Salt4, M2 has mean absolute mdot
error `{m2['mean_abs_mdot_error_pct']}` pct and mean all-probe RMSE
`{m2['mean_all_probe_rmse_K']}` K. Omitting the test-section term in **M3**
improves mean all-probe RMSE to `{m3['mean_all_probe_rmse_K']}` K but worsens
mean absolute mdot error to `{m3['mean_abs_mdot_error_pct']}` pct. Full realized
segment heat flux in **M1** does not solve the state problem: mean absolute mdot
error is `{m1['mean_abs_mdot_error_pct']}` pct and mean all-probe RMSE is
`{m1['mean_all_probe_rmse_K']}` K.

The highest-leverage model improvements are the cooling/HX closure and heater
heat-entry fraction. The current fixed-mdot cooler model has all-non-Salt1 RMSE
`{fmt(cooling_current.get('rmse_W'))}` W, while a Salt2-fit constant-UA
bulk-drive diagnostic has RMSE `{fmt(cooling_fit.get('rmse_W'))}` W. The
current electrical 1:1 heater model has RMSE `{fmt(heating_current.get('rmse_W'))}`
W, while a Salt2-fit scalar heater efficiency has RMSE `{fmt(heating_fit.get('rmse_W'))}`
W. These are strong diagnostic signals, but the final predictive model must use
setup-only boundary parameters rather than realized CFD heat rates.

## Study Design

The study uses Salt2 as the training row, Salt3 as validation, and Salt4 as
holdout. Salt1 is diagnostic/context only because the consumed source set lacks
a current admitted Salt1 patch heat ledger. No closure should be fitted on
Salt3 or Salt4.

The temperature comparison uses TP probes `{sensor_set(data, 'TP')}` and TW
probes `{sensor_set(data, 'TW')}`. TP targets are CFD core/bulk probe
references. TW targets are CFD wall references from the local validation
refresh. The audit generated `{data['summary']['sensor_error_rows']}` sensor
error rows, `{data['summary']['model_result_rows']}` model-result rows, and
`{data['summary']['heat_score_rows']}` heat-score rows.

## Boundary-Condition and Model Modes

| Mode | Part | Predictivity class | Uses CFD mdot at runtime | Uses realized CFD wallHeatFlux at runtime | Mean abs mdot error pct | Mean all-probe RMSE K |
| --- | --- | --- | --- | --- | ---: | ---: |
{mode_lines}

Important interpretation:

- M1 and M1b are diagnostic upper bounds because they prescribe realized CFD
  segment heat ledgers.
- M1b, Part4, and Part5 fixed-mdot rows isolate thermal behavior only; they are
  not hydraulic predictions.
- M2 and M3 remain CFD-informed diagnostic boundary subsets because they impose
  CFD heater/cooler/test-section heat terms.
- A setup-only predictive row must not consume CFD mdot, realized CFD
  wallHeatFlux, CFD cooler duty, CFD heater heat entry, or validation
  temperatures at runtime.

## Results by Study Part

### Part 1: Full CFD segment heat fluxes

Matching the full realized CFD segment heat ledger is not sufficient. M1
pressure-root rows reproduce net heat balance but still leave large state
errors. This means the problem is not only total heat accounting; reference
temperature handling, boundary placement, passive losses, and hydraulic
pressure closure still matter.

M1b fixes mdot to the CFD value and therefore should not be read as hydraulic
predictivity. It is useful because it shows that even with CFD mdot and full
realized heat rates, thermal state can remain badly biased when the model's
state/reference handling is inconsistent.

### Part 2: CFD heater + test-section net + cooler

M2 is the best current balance between mdot and probe error among pressure-root
CFD-informed modes. It keeps the test-section net term and solves mdot. The
mean all-probe RMSE is `{m2['mean_all_probe_rmse_K']}` K and mean absolute mdot
error is `{m2['mean_abs_mdot_error_pct']}` pct across Salt2/Salt3/Salt4.

The caveat is scientific, not clerical: the test-section term is currently
encoded as a compatibility negative source, not as a first-class distributed
external boundary model.

### Part 3: CFD heater + cooler only

M3 removes the CFD test-section net term. Probe RMSE improves, but mdot error
worsens. This is the clearest evidence that the test section cannot simply be
dropped. In the current model, removing it redistributes thermal and buoyancy
error rather than eliminating an irrelevant term.

### Part 4: Cooling leg heat removed

The cooling leg is the strongest near-term boundary-model lever. The current
fixed-mdot Fluid cooler model under-predicts heat removal with RMSE
`{fmt(cooling_current.get('rmse_W'))}` W. The Salt2-fit constant-UA bulk-drive
diagnostic transfers to Salt3/Salt4 with all-non-Salt1 RMSE
`{fmt(cooling_fit.get('rmse_W'))}` W. This suggests the model needs a better
setup-only cooler/HX UA or effectiveness representation.

### Part 5: Heating leg heat added

The current electrical 1:1 heater entry has RMSE
`{fmt(heating_current.get('rmse_W'))}` W. The Salt2-fit scalar heater-efficiency
diagnostic has RMSE `{fmt(heating_fit.get('rmse_W'))}` W. The heater boundary
therefore looks tractable, but the fitted scalar must be converted into a
documented setup-only heater efficiency or thermal-resistance model before it
can be used predictively.

## mdot vs Temperature-Error Correlation

Across pressure-root non-Salt1 rows, the audit reports Pearson r=
`{fmt(corr.get('pearson_r'))}` with n=`{corr.get('n_pairs')}` between absolute
mdot error and all-probe RMSE. This is a triage statistic, not a causal model.
Boundary modes change heat placement and buoyancy forcing at the same time, so
mdot and temperature errors can move together or trade off depending on the
mode.

## Assumptions and Guardrails

{assumptions}

## Conclusions

{finding_lines}

## Recommended Next Work

1. Promote the cooling model from diagnostic Salt2-fit evidence to a setup-only
   HX/cooler formulation, then score Salt3 and Salt4 without realized CFD cooler
   heat.
2. Replace electrical 1:1 heater entry with a setup-documented heater
   efficiency or thermal-resistance model.
3. Build a first-class distributed test-section boundary model. Do not keep the
   compatibility negative-source encoding as the final scientific model.
4. Audit reference-state/start-temperature handling before interpreting full
   CFD heat-ledger rows as validation evidence.
5. Keep the mdot-vs-temperature-error correlation as a diagnostic plot, not a
   fitting objective, until more setup-only cases exist.

## Reproducibility

Primary source package: `{rel(SRC)}`.

Appendix configuration snapshots are in
`{rel(SRC / 'model_config_appendix')}`. The most important appendix files are
`resolved_scenario_config_by_mode.csv`, `closure_terms_by_mode.csv`,
`segment_source_loss_assignment_by_mode.csv`, `cases.yaml`, `campaigns.yaml`,
and `scenarios.yaml`.
"""


def slide(title: str, bullets: list[str], figure: str, notes: str) -> str:
    bullet_text = "\n".join(f"- {item}" for item in bullets)
    return f"""## {title}

{bullet_text}

Suggested figure: {figure}

Speaker notes:
{notes}
"""


def presentation_text(data: dict[str, Any], mode_summary: list[dict[str, Any]]) -> str:
    corr = first_row(data["corr"], scope="all_non_salt1", part="all_parts", mode_id="all_modes", kind="all")
    m1 = next(row for row in mode_summary if row["mode_id"] == "M1_full_cfd_segment_heat_flux_pressure_root")
    m2 = next(row for row in mode_summary if row["mode_id"] == "M2_cfd_heater_test_section_cooler_pressure_root")
    m3 = next(row for row in mode_summary if row["mode_id"] == "M3_cfd_heater_cooler_pressure_root")
    slides = [
        slide(
            "Slide 1: Audit Question and Takeaway",
            [
                "Question: how do mdot errors compare with TP/TW temperature-probe errors?",
                "The current 1D model is auditable, but not yet setup-only predictive.",
                "Boundary placement drives a hydraulic/thermal tradeoff.",
            ],
            "Create title slide with small schematic of 1D loop plus TP/TW/mdot labels.",
            "Open by framing this as a model audit, not a claim of final predictive closure. Emphasize that the study separates diagnostic CFD-informed rows from setup-only predictive rows.",
        ),
        slide(
            "Slide 2: Case Split and Admission Discipline",
            [
                "Salt2 is training; Salt3 is validation; Salt4 is holdout.",
                "Salt1 is diagnostic/context only in this audit.",
                "No closure is fit on Salt3 or Salt4.",
            ],
            "Table from case_admission_and_use_table.csv.",
            "This slide prevents overclaiming. Salt1 appears in the package, but heat-flux modes are blocked because a current admitted Salt1 patch heat ledger was not available in the consumed source set.",
        ),
        slide(
            "Slide 3: Boundary-Condition Ladder",
            [
                "M1: full CFD segment heat ledger, pressure-root mdot.",
                "M1b: same heat ledger, fixed CFD mdot; thermal diagnostic only.",
                "M2: CFD heater + test-section net + cooler, pressure-root mdot.",
                "M3: CFD heater + cooler only, pressure-root mdot.",
            ],
            "Schematic evidence ladder from model_mode_matrix.csv.",
            "Explain that the ladder intentionally becomes less complete in heat-boundary information to expose what each boundary class controls.",
        ),
        slide(
            "Slide 4: What Is Compared",
            [
                f"TP probes: {sensor_set(data, 'TP')}.",
                f"TW probes: {sensor_set(data, 'TW')}.",
                "TP targets are CFD core/bulk references; TW targets are CFD wall references.",
                "mdot is solved from pressure balance except fixed-mdot diagnostics.",
            ],
            "Create annotated loop diagram with TP/TW markers.",
            "Make clear which TP and TW families are scored. This avoids ambiguity about whether we are comparing wall temperatures, bulk temperatures, or mixed references.",
        ),
        slide(
            "Slide 5: Boundary Ladder Performance",
            [
                f"M1: mean abs mdot error {m1['mean_abs_mdot_error_pct']} pct; all-probe RMSE {m1['mean_all_probe_rmse_K']} K.",
                f"M2: mean abs mdot error {m2['mean_abs_mdot_error_pct']} pct; all-probe RMSE {m2['mean_all_probe_rmse_K']} K.",
                f"M3: mean abs mdot error {m3['mean_abs_mdot_error_pct']} pct; all-probe RMSE {m3['mean_all_probe_rmse_K']} K.",
            ],
            "Grouped bar chart from boundary_mode_performance_summary.csv.",
            "This is the core performance slide. The important story is that the lowest thermal-probe RMSE is not the same as the lowest mdot error.",
        ),
        slide(
            "Slide 6: Full CFD Heat Ledger Is Not Enough",
            [
                "M1 prescribes realized CFD segment heat fluxes.",
                "Large Tmean and probe errors remain.",
                "Reference state and model-form issues remain even when net heat is matched.",
            ],
            "M1 per-case bars from case_mode_error_table.csv.",
            "Use this to rule out a simplistic explanation that the model only needs the right total heat input/output.",
        ),
        slide(
            "Slide 7: Test Section Tradeoff",
            [
                "Part3 omits the CFD test-section net term.",
                "Probe RMSE improves on average.",
                "mdot error worsens on average.",
                "Conclusion: the test section is not negligible; it needs a physical boundary model.",
            ],
            "Part2 vs Part3 paired bars from part3_test_section_error_increment.csv.",
            "Describe this as a tradeoff, not an improvement. A boundary deletion can make one score better while degrading circulation physics.",
        ),
        slide(
            "Slide 8: Cooling Leg Is the Largest Boundary Lever",
            [
                "Current fixed-mdot cooler RMSE is about 102.9 W.",
                "Salt2-fit constant-UA bulk-drive RMSE is about 4.64 W.",
                "A setup-only HX/cooler UA/effectiveness model is the next priority.",
            ],
            "Bar chart from part4_cooling_rmse_summary.csv.",
            "This slide motivates concrete model development. Do not present the zero-error imposed-CFD cooler row as predictive.",
        ),
        slide(
            "Slide 9: Heater Entry Is Tractable",
            [
                "Electrical 1:1 heater RMSE is about 24.6 W.",
                "Salt2-fit heater efficiency RMSE is about 0.68 W.",
                "A scalar heater-efficiency model may transfer, but must be setup-only.",
            ],
            "Bar chart from part5_heating_rmse_summary.csv.",
            "The heater is less complex than the cooler in this diagnostic exercise. The scientific requirement is to justify the scalar from setup or independent evidence.",
        ),
        slide(
            "Slide 10: mdot Error vs Temperature Error",
            [
                f"Pearson r={fmt(corr.get('pearson_r'))}, n={corr.get('n_pairs')} across pressure-root non-Salt1 rows.",
                "Association is descriptive, not causal.",
                "Use as a triage view, not a fitting objective.",
            ],
            f"Existing figure: {rel(SRC / 'figures/mdot_error_vs_probe_rmse.svg')}.",
            "This plot helps communicate coupling. Stress that each point changes boundary conditions, so correlation is not a physical law.",
        ),
        slide(
            "Slide 11: Assumptions That Matter",
            [
                "Positive wallHeatFlux heats the fluid; negative cools it.",
                "CFD rcExternalTemperature includes radiation; no separate qr term is added.",
                "Realized CFD wallHeatFlux rows are diagnostic unless explicitly declared CFD-informed.",
                "Fixed-mdot rows are thermal diagnostics only.",
            ],
            "Assumption table from study_assumption_register.csv.",
            "This slide is for scientific defensibility. It should be included in a technical presentation or appendix.",
        ),
        slide(
            "Slide 12: What To Do Next",
            [
                "Build setup-only cooler/HX model and rescore Salt3/Salt4.",
                "Build setup-only heater efficiency or resistance model.",
                "Replace test-section compatibility sink with a distributed boundary model.",
                "Audit reference-state handling before using full heat-ledger rows as validation.",
            ],
            "Roadmap graphic with three branches: cooler, heater, test section.",
            "End with executable next steps, not only conclusions. The model audit has identified where development should focus.",
        ),
    ]
    return "# Presentation Outline: mdot Error vs TP/TW Temperature Error\n\n" + "\n".join(slides)


def write_readme(summary: dict[str, Any]) -> None:
    write_text(
        OUT / "README.md",
        f"""# mdot Temperature Error Report and Presentation

This AGENT-420 package converts the AGENT-360 mdot/TP/TW audit into a
report-ready synthesis and presentation outline.

## Outputs

- `mdot_temperature_error_report.md`
- `presentation_outline.md`
- `boundary_mode_performance_summary.csv`
- `case_mode_error_table.csv`
- `key_findings_for_paper.csv`
- `suggested_figure_plan.csv`
- `summary.json`

## Summary

- Boundary-mode summary rows: `{summary['boundary_mode_rows']}`
- Case-mode error rows: `{summary['case_mode_rows']}`
- Slide count: `{summary['slide_count']}`
- Source package: `{rel(SRC)}`

No native CFD outputs, scheduler state, registry/admission state, or external
Fluid code were mutated.
""",
    )


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    data = load()
    mode_summary = build_mode_summary(data)
    case_table = build_case_mode_table(data)
    key_findings = build_key_findings(data)
    figure_plan = build_figure_plan(data)

    write_csv(OUT / "boundary_mode_performance_summary.csv", mode_summary)
    write_csv(OUT / "case_mode_error_table.csv", case_table)
    write_csv(OUT / "key_findings_for_paper.csv", key_findings)
    write_csv(OUT / "suggested_figure_plan.csv", figure_plan)
    write_text(OUT / "mdot_temperature_error_report.md", report_text(data, mode_summary, key_findings))
    deck = presentation_text(data, mode_summary)
    write_text(OUT / "presentation_outline.md", deck)
    write_csv(
        OUT / "source_manifest.csv",
        [
            {"source_id": "agent360_audit", "path": rel(SRC), "role": "primary mdot-temperature audit source"},
            {"source_id": "paper_ready_report", "path": rel(SRC / "paper_ready_report.md"), "role": "prior report text"},
            {"source_id": "trend_register", "path": rel(SRC / "trend_conclusion_register.csv"), "role": "finding register"},
            {"source_id": "config_appendix", "path": rel(SRC / "model_config_appendix"), "role": "1D configuration appendix source"},
        ],
    )

    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_package": rel(SRC),
        "work_product": rel(OUT),
        "boundary_mode_rows": len(mode_summary),
        "case_mode_rows": len(case_table),
        "key_findings": len(key_findings),
        "figure_plan_rows": len(figure_plan),
        "slide_count": deck.count("\n## Slide "),
        "native_cfd_outputs_mutated": False,
        "external_cfd_modeling_tools_mutated": False,
        "scheduler_state_mutated": False,
        "registry_or_admission_state_mutated": False,
    }
    write_text(OUT / "summary.json", json.dumps(summary, indent=2, sort_keys=True))
    write_readme(summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
