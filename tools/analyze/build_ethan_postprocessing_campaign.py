#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TMP_MPL_ROOT = ROOT / "tmp" / "mplconfig"
TMP_MPL_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(TMP_MPL_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    csv_dump,
    date_stamp,
    ensure_dir,
    iso_timestamp,
    json_dump,
    load_workspace_config,
    read_registry_rows,
    resolve_workspace_path,
)
from tools.analyze.build_ethan_run_postprocessing_package import (  # noqa: E402
    FIELD_ORDER,
    build_run_package,
    default_source_ids,
)


DEFAULT_SLUG = f"{date_stamp()}_ethan_postprocessing_all_runs_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the canonical all-run Ethan postprocessing campaign.")
    parser.add_argument("--source-id", action="append", dest="source_ids", help="Repeat to restrict the campaign to selected registered source ids.")
    parser.add_argument("--campaign-slug", default=DEFAULT_SLUG, help="Campaign slug under cross_model_comparison/campaigns/.")
    parser.add_argument("--campaign-root", help="Explicit campaign root override. Defaults to the configured cross_model publish root.")
    parser.add_argument("--reuse-existing-renders", action="store_true", help="Record already-generated field renders when they already exist.")
    return parser.parse_args()


def write_markdown(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def plot_campaign_metric(
    rows: list[dict[str, Any]],
    y_key: str,
    title: str,
    ylabel: str,
    output_root: Path,
    field: str,
    stem: str,
) -> dict[str, str] | None:
    usable = [(index + 1, row) for index, row in enumerate(rows) if row.get(y_key) not in ("", None)]
    if not usable:
        return None
    fig, ax = plt.subplots(figsize=(10.4, 5.0), constrained_layout=True)
    xs = [index for index, _row in usable]
    ys = [float(row[y_key]) for _index, row in usable]
    labels = [row["display_label"] for _index, row in usable]
    ax.plot(xs, ys, marker="o", linewidth=1.6)
    ax.set_title(title)
    ax.set_xlabel("Run index")
    ax.set_ylabel(ylabel)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
    ax.grid(True, alpha=0.25)

    csv_path = output_root / "data" / f"{stem}.csv"
    csv_dump(csv_path, list(rows[0].keys()), rows)
    svg_path = ensure_dir(output_root / "figures" / field / "svg") / f"{stem}.svg"
    pdf_path = ensure_dir(output_root / "figures" / field / "pdf") / f"{stem}.pdf"
    tikz_path = ensure_dir(output_root / "figures" / field / "tikz") / f"{stem}.tex"
    fig.savefig(svg_path)
    fig.savefig(pdf_path)
    tikz_text = "\n".join(
        [
            "\\begin{tikzpicture}",
            f"\\begin{{axis}}[title={{{title}}}, xlabel={{Run index}}, ylabel={{{ylabel}}}, width=13cm, height=7cm, grid=both]",
            f"\\addplot table [col sep=comma, x=run_index, y={y_key}] {{{os.path.relpath(csv_path, tikz_path.parent)}}};",
            "\\end{axis}",
            "\\end{tikzpicture}",
            "",
        ]
    )
    tikz_path.write_text(tikz_text, encoding="utf-8")
    plt.close(fig)
    return {"svg": str(svg_path.resolve()), "pdf": str(pdf_path.resolve()), "tikz": str(tikz_path.resolve()), "table_csv": str(csv_path.resolve())}


def inside_cross_model_root(path: Path, cross_model_root: Path) -> bool:
    try:
        path.resolve().relative_to(cross_model_root.resolve())
    except ValueError:
        return False
    return True


def append_daily_journal(cross_model_root: Path, slug: str, summary_rows: list[dict[str, Any]]) -> None:
    journal_path = cross_model_root / "journals" / date_stamp()[:7] / f"{date_stamp()}_workflow_journal.md"
    ready_counts = Counter(row["readiness_label"] for row in summary_rows)
    run_status_counts = Counter(row["run_status"] for row in summary_rows)
    lines = []
    if journal_path.exists():
        lines.append(journal_path.read_text(encoding="utf-8").rstrip())
        lines.append("")
    lines.extend(
        [
            f"## {slug}",
            "",
            "### Research question",
            "",
            "Build a canonical per-run plus cross-run monitor-analysis campaign for all 13 registered Ethan CFD cases using the existing labeled native `postProcessing` outputs as the baseline evidence stack.",
            "",
            "### Observed output",
            "",
            f"- Run count: `{len(summary_rows)}`",
            f"- Readiness counts: `{dict(ready_counts)}`",
            f"- Runtime status counts: `{dict(run_status_counts)}`",
            "",
            "### Interpretation",
            "",
            "- The canonical `cross_model_comparison` subtree now holds both per-run monitor packages and one cross-run synthesis package for the Ethan 3D CFD intake rows.",
            "- The workflow stays conservative about pressure: it records the missing baseline native pressure monitor family explicitly instead of fabricating pressure figures from incomplete evidence.",
            "- All runs are retained, but maturity labels separate manuscript-ready comparison candidates from continuation-affected or audit-required rows.",
            "",
            "### Sources",
            "",
        ]
    )
    for row in summary_rows:
        lines.append(f"- `{row['source_id']}` from `{row['source_root']}`")
    write_markdown(journal_path, "\n".join(lines))


def build_campaign_reports(campaign_root: Path, slug: str, summary_rows: list[dict[str, Any]]) -> None:
    reports_root = ensure_dir(campaign_root / "reports")
    data_root = ensure_dir(campaign_root / "data")
    run_status_counts = Counter(row["run_status"] for row in summary_rows)
    readiness_counts = Counter(row["readiness_label"] for row in summary_rows)
    fluid_counts = Counter(row["fluid"] for row in summary_rows)

    executive = f"""
# Ethan postprocessing campaign executive summary

- Campaign slug: `{slug}`
- Run count: `{len(summary_rows)}`
- Fluid counts: `{dict(fluid_counts)}`
- Runtime status counts: `{dict(run_status_counts)}`
- Readiness counts: `{dict(readiness_counts)}`

Key boundary choices:

- The baseline evidence set is the easy labeled native `postProcessing` stack already present in each run.
- Each run gets its own package with report layers, figures, tables, and artifact maps.
- Pressure remains an explicit availability boundary in this v1 campaign because the baseline native monitor family does not publish direct pressure histories.
"""
    technical = f"""
# Ethan postprocessing campaign technical analysis

## Scope

- Registered CFD runs processed: `{len(summary_rows)}`
- Scope excludes the `inventory_only` registry row.
- Each per-run package is built from the native labeled monitor stack first, with previously generated richer artifacts only recorded as reused context.

## Cross-run patterns

- Readiness classes: `{dict(readiness_counts)}`
- Runtime states: `{dict(run_status_counts)}`
- Fluids/property branches: `{dict(fluid_counts)}`

## Interpretation boundary

- This campaign is monitor-first. It is designed to be paper-reusable without requiring fresh OpenFOAM reconstruction as a prerequisite.
- Pressure is intentionally handled conservatively: the campaign records availability and provenance explicitly rather than extrapolating unsupported pressure narratives from incomplete native monitor coverage.
- Non-converged or continuation-affected rows remain inside the campaign, but the maturity labels must stay attached to any later manuscript use.

## Generated indexes

- `data/run_index.csv`
- `data/readiness_matrix.csv`
- `data/cross_run_summary.csv`
- one per-run package under `runs/<source_id>/`
"""
    methodology = """
# Methodology

1. Read the registry, June 4 metadata index, June 4 direct-validation table, and June 9 steady-state heat audit.
2. For each run, read the native labeled `postProcessing` files:
   - `mdot_*`
   - `temperature_probes`
   - `wall_temperature_probes`
   - `total_Q.dat`
   - `piv_slab_velocity`
   - `wallHeatFlux`
   - `yPlus`
   - `wallShearStress`
   - `velocity_profiles`
3. Export cleaned CSV tables for every plotted figure.
4. Save the figure bundle in SVG, PDF, and PGFPlots/TikZ `.tex`.
5. Write per-run report layers and artifact maps.
6. Build the cross-run synthesis from the resulting per-run summary JSON files.
"""
    write_markdown(reports_root / "executive_summary.md", executive)
    write_markdown(reports_root / "technical_analysis.md", technical)
    write_markdown(reports_root / "methodology.md", methodology)

    todo_lines = [
        "# TODO",
        "",
        "- Add baseline native pressure monitor families if future runs publish them directly.",
        "- Decide whether a v2 should require fresh reconstruction-driven temperature/velocity/pressure field slices for every run.",
        "- Revisit maturity labels before any manuscript text treats non-converged rows as direct validation evidence.",
    ]
    write_markdown(campaign_root / "TODO.md", "\n".join(todo_lines))


def build_cross_model_checkpoint(cross_model_root: Path, slug: str, campaign_root: Path, summary_rows: list[dict[str, Any]]) -> None:
    note_root = ensure_dir(cross_model_root / "operational_notes" / slug)
    checkpoint = f"""
# Checkpoint

Date: `{iso_timestamp()}`
Task: `{slug}`

## Goal

Build a canonical all-run Ethan postprocessing campaign under `cross_model_comparison` with per-run packages, cross-run synthesis, artifact maps, and report-ready vector/TikZ outputs.

## Key outputs

- campaign manifest
- cross-run summary tables
- per-run report packages
- daily journal update
- TODO note for remaining pressure/render maturity work
"""
    write_markdown(note_root / "CHECKPOINT.md", checkpoint)
    json_dump(
        note_root / "MANIFEST.json",
        {
            "generated_at": iso_timestamp(),
            "campaign_root": str(campaign_root.resolve()),
            "source_count": len(summary_rows),
            "source_ids": [row["source_id"] for row in summary_rows],
            "reports": {
                "executive_summary": str((campaign_root / "reports" / "executive_summary.md").resolve()),
                "technical_analysis": str((campaign_root / "reports" / "technical_analysis.md").resolve()),
                "methodology": str((campaign_root / "reports" / "methodology.md").resolve()),
            },
        },
    )


def main() -> int:
    args = parse_args()
    config = load_workspace_config()
    cross_model_root = resolve_workspace_path(config["cross_model_publish_root"]).resolve()
    campaign_root = Path(args.campaign_root).resolve() if args.campaign_root else (cross_model_root / "campaigns" / args.campaign_slug).resolve()
    source_ids = args.source_ids or default_source_ids()

    summary_rows: list[dict[str, Any]] = []
    for source_id in source_ids:
        summary = build_run_package(source_id, campaign_root, reuse_existing_renders=args.reuse_existing_renders)
        summary_rows.append(summary)
    summary_rows.sort(key=lambda row: row["source_id"])
    for index, row in enumerate(summary_rows, start=1):
        row["run_index"] = index
        row["source_root"] = get_source_root(row["source_id"])

    data_root = ensure_dir(campaign_root / "data")
    manifest_path = campaign_root / "manifest.json"

    run_index_rows = [
        {
            "run_index": row["run_index"],
            "source_id": row["source_id"],
            "display_label": row["display_label"],
            "fluid": row["fluid"],
            "variant_label": row["variant_label"],
            "base_case_id": row["base_case_id"],
            "readiness_label": row["readiness_label"],
            "run_status": row["run_status"],
            "convergence_reached": row["convergence_reached"],
            "source_root": row["source_root"],
            "report_path": row["report_paths"]["technical_analysis"],
        }
        for row in summary_rows
    ]
    csv_dump(data_root / "run_index.csv", list(run_index_rows[0].keys()), run_index_rows)

    readiness_rows = [
        {
            "run_index": row["run_index"],
            "source_id": row["source_id"],
            "display_label": row["display_label"],
            "readiness_label": row["readiness_label"],
            "run_status": row["run_status"],
            "convergence_reached": row["convergence_reached"],
            "final_time_metadata_s": row["final_time_metadata_s"],
            "latest_heat_time_s": row["latest_heat_time_s"],
            "latest_probe_time_s": row["latest_probe_time_s"],
        }
        for row in summary_rows
    ]
    csv_dump(data_root / "readiness_matrix.csv", list(readiness_rows[0].keys()), readiness_rows)

    csv_dump(data_root / "cross_run_summary.csv", list(summary_rows[0].keys()), summary_rows)

    campaign_figures: list[dict[str, str]] = []
    figure_specs = [
        ("runtime", "final_time_metadata_s", "Final extracted/metadata time by run", "Final time [s]", "runtime_final_time_by_run"),
        ("velocity", "mdot_mean_abs_kg_s", "Mean absolute monitored mass flow by run", "Mass flow [kg/s]", "velocity_mdot_by_run"),
        ("temperature", "probe_T_avg_K", "Average fluid probe temperature by run", "Temperature [K]", "temperature_probe_avg_by_run"),
        ("heat_transfer", "ambient_proxy_w", "Ambient-loss proxy by run", "Heat [W]", "heat_transfer_ambient_proxy_by_run"),
        ("wall_quality", "avg_yplus", "Average yPlus by run", "Average yPlus", "wall_quality_avg_yplus_by_run"),
        ("comparison", "exp_tw_rmse_k", "Wall-temperature RMSE by run", "TW RMSE [K]", "comparison_tw_rmse_by_run"),
    ]
    for field, y_key, title, ylabel, stem in figure_specs:
        bundle = plot_campaign_metric(summary_rows, y_key, title, ylabel, campaign_root, field, stem)
        if bundle:
            campaign_figures.append({"field": field, "figure_id": stem, **bundle})

    build_campaign_reports(campaign_root, args.campaign_slug, summary_rows)

    json_dump(
        manifest_path,
        {
            "generated_at": iso_timestamp(),
            "workspace_root": "cross_model_comparison" if inside_cross_model_root(campaign_root, cross_model_root) else str(campaign_root.parent),
            "campaign_root": str(campaign_root.resolve()),
            "native_outputs_policy": "analysis compiled from existing registered case postProcessing, existing metadata indices, and existing validation reports only; imported solver output roots were not mutated and no new OpenFOAM postprocessing was launched",
            "source_count": len(summary_rows),
            "source_ids": source_ids,
            "scripts": [
                "tools/analyze/build_ethan_run_postprocessing_package.py",
                "tools/analyze/build_ethan_postprocessing_campaign.py",
            ],
            "commands": ["python -m py_compile tools/analyze/build_ethan_run_postprocessing_package.py tools/analyze/build_ethan_postprocessing_campaign.py"],
            "campaign_tables": {
                "run_index": str((data_root / "run_index.csv").resolve()),
                "readiness_matrix": str((data_root / "readiness_matrix.csv").resolve()),
                "cross_run_summary": str((data_root / "cross_run_summary.csv").resolve()),
            },
            "campaign_figures": campaign_figures,
            "per_run_reports": {row["source_id"]: row["report_paths"] for row in summary_rows},
        },
    )

    if inside_cross_model_root(campaign_root, cross_model_root):
        build_cross_model_checkpoint(cross_model_root, args.campaign_slug, campaign_root, summary_rows)
        append_daily_journal(cross_model_root, args.campaign_slug, summary_rows)

    print(json.dumps({"campaign_root": str(campaign_root), "source_count": len(summary_rows)}, indent=2))
    return 0


def get_source_root(source_id: str) -> str:
    row = next(row for row in default_registry_rows if row["source_id"] == source_id)
    return row["source_root"]


default_registry_rows = [
    row
    for row in read_registry_rows(WORKSPACE_ROOT / "registry" / "case_registry.csv")
    if row.get("source_id")
]


if __name__ == "__main__":
    raise SystemExit(main())
