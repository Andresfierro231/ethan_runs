#!/usr/bin/env python3
"""Build a starter upcomer-onset regime table and figure."""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_upcomer_onset"
DATA = ROOT / "work_products/2026-07/2026-07-07/2026-07-07_upcomer_correlation_v2/upcomer_dataset.csv"
FIT = ROOT / "work_products/2026-07/2026-07-07/2026-07-07_upcomer_correlation_v2/upcomer_correlation_fit.csv"
CURRENT_UQ = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_study_upcomer_onset_anchor_design_and_recirc_fraction_uq/diagnostic_onset_evidence_table.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def fnum(value: Any) -> float:
    return float(value)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def classify(row: dict[str, str]) -> tuple[str, str, str]:
    backflow = fnum(row["backflow_fraction"])
    ri = fnum(row["Ri_median"])
    if backflow >= 0.10 or ri >= 1.0:
        return (
            "recirculation_cell_observed",
            "exclude_from_pipe_friction_fit",
            "ordinary_pipe_friction_invalid",
        )
    if backflow > 0.02 or ri >= 0.3:
        return (
            "transition_mixed_convection",
            "validation_only",
            "needs_dense_design_points",
        )
    return ("ordinary_pipe_friction_candidate", "fit_candidate_after_mesh_gate", "needs_confirmation")


def build_rows() -> list[dict[str, Any]]:
    fit = read_csv(FIT)[0]
    rows = []
    for raw in read_csv(DATA):
        regime, admission, uncertainty = classify(raw)
        wall_bulk_delta_t = ""  # Not directly available in AGENT-196 table.
        rows.append(
            {
                "label": raw["label"],
                "source_id": raw["source_id"],
                "Re_upcomer": raw["Re_upcomer"],
                "Pr_median": raw["Pr_median"],
                "Ri_median": raw["Ri_median"],
                "Ra_median": raw["Ra_median"],
                "Gr_proxy_from_Ra_Pr": fnum(raw["Ra_median"]) / fnum(raw["Pr_median"]),
                "wall_bulk_delta_T_K": wall_bulk_delta_t,
                "backflow_fraction": raw["backflow_fraction"],
                "recirculation_intensity": raw["recirculation_intensity"],
                "Nu_upcomer": raw["Nu_upcomer"],
                "T_bulk_K": raw["T_bulk_K"],
                "regime_class": regime,
                "fit_admission_status": admission,
                "onset_criterion": "observed_backflow_fraction>=0.10_or_Ri>=1; route_A_onset_Re_240_260; route_B_onset_Re_100_235",
                "onset_Re_route_A_mid": fit["onset_Re_route_A_mid"],
                "onset_Re_route_B_mid": fit["onset_Re_route_B_mid"],
                "uncertainty": uncertainty + ";three_point_extrapolation;coarse_no_gci",
                "minimal_cfd_design_recommendation": "add admitted points near Re 150, 200, 250 plus wall-core DeltaT extraction and mesh/GCI evidence",
                "current_uq_context": "recirculation_fraction_uq_available_if_case_label_matches",
            }
        )
    return rows


def current_uq_rows() -> list[dict[str, Any]]:
    if not CURRENT_UQ.exists():
        return [
            {
                "source_path": rel(CURRENT_UQ),
                "status": "missing_optional_current_uq_table",
                "use": "not_available",
                "admission_effect": "none",
            }
        ]
    rows = read_csv(CURRENT_UQ)
    return [
        {
            "source_path": rel(CURRENT_UQ),
            "status": "available",
            "use": "diagnostic_context_only",
            "admission_effect": "none",
            "row_count": len(rows),
            "reverse_candidate_fraction_min": min((row.get("reverse_candidate_fraction_of_right_leg_roi", "") for row in rows), default=""),
            "reverse_candidate_fraction_max": max((row.get("reverse_candidate_fraction_of_right_leg_roi", "") for row in rows), default=""),
        }
    ]


def write_svg(rows: list[dict[str, Any]]) -> Path:
    path = OUT / "figures/upcomer_onset_regime.svg"
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 820, 520
    left, top, plot_w, plot_h = 80, 70, 650, 320
    re_vals = [fnum(row["Re_upcomer"]) for row in rows] + [250.0]
    bf_vals = [fnum(row["backflow_fraction"]) for row in rows] + [0.0, 0.30]
    re_min, re_max = min(re_vals) - 10, max(re_vals) + 20
    bf_min, bf_max = 0.0, max(bf_vals) + 0.03

    def x(value: float) -> float:
        return left + (value - re_min) / (re_max - re_min) * plot_w

    def y(value: float) -> float:
        return top + (bf_max - value) / (bf_max - bf_min) * plot_h

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#111827}.title{font-size:22px;font-weight:700}.small{font-size:11px;fill:#4B5563}.axis{stroke:#374151}.grid{stroke:#E5E7EB}</style>',
        '<text x="40" y="35" class="title">Upcomer Recirculation Onset Regime</text>',
        '<text x="40" y="55" class="small">Observed Salt 2/3/4 points remain in recirculation-cell regime; onset band is extrapolated.</text>',
    ]
    for tick in [0.0, 0.1, 0.2, 0.3]:
        parts.append(f'<line x1="{left}" x2="{left + plot_w}" y1="{y(tick)}" y2="{y(tick)}" class="grid"/>')
        parts.append(f'<text x="35" y="{y(tick)+4}" class="small">{tick:.1f}</text>')
    for tick in [75, 100, 150, 200, 250]:
        parts.append(f'<line x1="{x(tick)}" x2="{x(tick)}" y1="{top}" y2="{top + plot_h}" class="grid"/>')
        parts.append(f'<text x="{x(tick)-10}" y="{top + plot_h + 20}" class="small">{tick}</text>')
    parts.append(f'<line x1="{left}" x2="{left + plot_w}" y1="{top + plot_h}" y2="{top + plot_h}" class="axis"/>')
    parts.append(f'<line x1="{left}" x2="{left}" y1="{top}" y2="{top + plot_h}" class="axis"/>')
    parts.append(f'<rect x="{x(100)}" y="{top}" width="{x(260)-x(100)}" height="{plot_h}" fill="#FDE68A" opacity="0.25"/>')
    parts.append(f'<text x="{x(105)}" y="{top + 18}" class="small">onset bracket</text>')
    for row in rows:
        parts.append(f'<circle cx="{x(fnum(row["Re_upcomer"]))}" cy="{y(fnum(row["backflow_fraction"]))}" r="7" fill="#D97706"/>')
        parts.append(f'<text x="{x(fnum(row["Re_upcomer"])) + 9}" y="{y(fnum(row["backflow_fraction"])) - 8}" class="small">{row["label"]}</text>')
    parts.append(f'<text x="{left + plot_w / 2 - 40}" y="{height - 45}" class="small">Re_upcomer</text>')
    parts.append('<text x="20" y="250" class="small" transform="rotate(-90 20,250)">backflow fraction</text>')
    parts.append('<text x="40" y="485" class="small">Source: AGENT-196 upcomer dataset and fit. Mesh/GCI and corrected-Q perturbation conclusions remain work in progress.</text>')
    parts.append("</svg>\n")
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def write_readme(rows: list[dict[str, Any]]) -> None:
    text = f"""# Upcomer Onset Regime Table

Generated: `{datetime.now().isoformat(timespec='seconds')}`

## Scope

Starter package for `TODO-UPCOMER-ONSET`. It converts the AGENT-196 upcomer
correlation output into a regime table and figure. It does not admit corrected
Salt perturbation rows and does not claim mesh-qualified onset.

## Observed Facts

- Rows: `{len(rows)}` admitted Salt 2/3/4 mainline points.
- All current points classify as `recirculation_cell_observed`.
- Backflow fraction decreases with Re across the admitted range, but remains
  nonzero at Salt 4.
- Route A onset midpoint from AGENT-196 is `250`; Route B midpoint is `167.5`.

## Inferred Interpretation

The upcomer is currently a mixed-convection recirculation-cell problem rather
than an ordinary pipe-friction span. Onset thresholds are still extrapolated
because all admitted points are inside the recirculating regime.

## Blockers

- Only three admitted operating points.
- No mesh/GCI uncertainty.
- Corrected Salt perturbation conclusions remain work in progress and are not
  used here.
- Wall-core Delta T is not yet directly available in the regime table source.
- Current recirculation-fraction UQ context is included only as diagnostic
  context; it does not admit an onset threshold or exchange coefficient.

## Recommended Next Action

Use `figures/upcomer_onset_regime.svg` as a regime-table figure, with caveats.
Add new CFD/design points near Re 150, 200, and 250 before fitting a threshold.

## Guardrails

No ordinary upcomer `Nu`, `f_D`, component `K`, exchange-cell coefficient,
source/property release, validation/holdout/external scoring, native-output
mutation, registry/admission mutation, scheduler action, Fluid/external edit,
final score, or residual absorption into internal Nu was performed.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    rows = build_rows()
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(
        OUT / "upcomer_onset_regime_table.csv",
        rows,
        [
            "label",
            "source_id",
            "Re_upcomer",
            "Pr_median",
            "Ri_median",
            "Ra_median",
            "Gr_proxy_from_Ra_Pr",
            "wall_bulk_delta_T_K",
            "backflow_fraction",
            "recirculation_intensity",
            "Nu_upcomer",
            "T_bulk_K",
            "regime_class",
            "fit_admission_status",
            "onset_criterion",
            "onset_Re_route_A_mid",
            "onset_Re_route_B_mid",
            "uncertainty",
            "minimal_cfd_design_recommendation",
            "current_uq_context",
        ],
    )
    write_csv(
        OUT / "current_uq_context.csv",
        current_uq_rows(),
        ["source_path", "status", "use", "admission_effect", "row_count", "reverse_candidate_fraction_min", "reverse_candidate_fraction_max"],
    )
    write_csv(
        OUT / "source_manifest.csv",
        [
            {"source_path": rel(DATA), "role": "legacy_upcomer_regime_dataset", "mutation_status": "read_only"},
            {"source_path": rel(FIT), "role": "legacy_onset_fit_source", "mutation_status": "read_only"},
            {"source_path": rel(CURRENT_UQ), "role": "current_recirc_fraction_uq_context", "mutation_status": "read_only"},
        ],
        ["source_path", "role", "mutation_status"],
    )
    fig = write_svg(rows)
    write_readme(rows)
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task": "TODO-UPCOMER-ONSET",
        "rows": len(rows),
        "regime_classes": sorted({row["regime_class"] for row in rows}),
        "figure": rel(fig),
        "inputs": [rel(DATA), rel(FIT), rel(CURRENT_UQ)],
        "outputs": ["upcomer_onset_regime_table.csv", "current_uq_context.csv", "source_manifest.csv", "figures/upcomer_onset_regime.svg", "README.md", "summary.json"],
        "mesh_uncertainty_status": "current_gate_open_elsewhere_no_formal_gci_here",
        "ordinary_pipe_admission_rows": 0,
        "exchange_coefficient_admission_rows": 0,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
