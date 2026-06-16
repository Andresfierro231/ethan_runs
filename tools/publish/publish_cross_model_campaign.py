#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    base_case_id,
    case_variant_label,
    csv_dump,
    date_stamp,
    ensure_dir,
    get_registry_row,
    iso_timestamp,
    json_dump,
    load_workspace_config,
    resolve_workspace_path,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish one or more Ethan intake cases into cross_model_comparison.")
    parser.add_argument("--source-id", action="append", required=True, help="Registered source identifier. Repeat for multi-case campaigns.")
    parser.add_argument("--campaign-slug", help="Explicit campaign slug override. Required for multi-case campaigns.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned paths without writing files.")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_csv_row(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            return row
    return {}


def load_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def build_campaign_slug(case_id: str, prefix: str, multi_case: bool) -> str:
    stamp = date_stamp()
    suffix = "_batch_v1" if multi_case else "_v1"
    return f"{stamp}_{prefix}_{case_id}{suffix}".replace(" ", "_")


def write_text(path: Path, text: str, dry_run: bool) -> None:
    if dry_run:
        return
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def merge_rows(existing: list[dict[str, str]], new_rows: list[dict[str, str]], keys: tuple[str, ...]) -> list[dict[str, str]]:
    merged: dict[tuple[str, ...], dict[str, str]] = {}
    for row in existing + new_rows:
        key = tuple(str(row.get(col, "")) for col in keys)
        merged[key] = row
    return list(merged.values())


def union_fieldnames(rows: list[dict[str, str]], preferred: list[str] | None = None) -> list[str]:
    fieldnames: list[str] = []
    for name in preferred or []:
        if name not in fieldnames:
            fieldnames.append(name)
    for row in rows:
        for name in row.keys():
            if name not in fieldnames:
                fieldnames.append(name)
    return fieldnames


def comparison_ready(qoi_row: dict[str, str]) -> str:
    run_status = qoi_row.get("run_status", "")
    reached = str(qoi_row.get("convergence_reached", "")).lower() == "true"
    if run_status == "completed" and reached:
        return "comparison_candidate"
    if reached:
        return "converged_but_review_required"
    if run_status == "terminated":
        return "convergence_audit_required"
    return "restart_or_audit_required"


def disposition_note(qoi_row: dict[str, str]) -> str:
    run_status = qoi_row.get("run_status", "")
    reached = str(qoi_row.get("convergence_reached", "")).lower() == "true"
    if run_status == "completed" and reached:
        return "Completed normally after reaching the coded convergence monitor."
    if reached:
        return "Reached the coded convergence monitor before final shutdown; review before validation claims."
    if run_status == "terminated":
        return "Stopped without a normal completion marker and without recorded convergence; treat as requiring convergence audit."
    return "No normal completion marker and no recorded convergence; inspect before use."


def load_source_payload(source_id: str, publish_root: Path) -> dict:
    row = get_registry_row(WORKSPACE_ROOT / "registry" / "case_registry.csv", source_id)
    local_manifest = WORKSPACE_ROOT / "imports" / f"{date_stamp()}_{row['source_id']}_import.json"
    local_inventory = WORKSPACE_ROOT / "work_products" / row["source_id"] / "case_inventory.json"
    local_qoi = WORKSPACE_ROOT / "work_products" / row["source_id"] / "qoi_summary.csv"
    local_join = WORKSPACE_ROOT / "work_products" / row["source_id"] / "cross_model_case_contract_joined.csv"
    local_join_summary = WORKSPACE_ROOT / "work_products" / row["source_id"] / "cross_model_join_summary.json"
    local_render_status = WORKSPACE_ROOT / "figures_rendered" / row["source_id"] / "status.json"
    local_render_job = WORKSPACE_ROOT / "staging" / "render_jobs" / f"{row['source_id']}_render.sbatch"
    for required in (local_manifest, local_inventory, local_qoi):
        if not required.exists():
            raise SystemExit(f"Expected local workflow artifact not found: {required}")

    import_path = publish_root / "imports" / f"{date_stamp()}_{row['source_id']}_import.json"
    payload = {
        "registry": row,
        "manifest_path": local_manifest,
        "inventory_path": local_inventory,
        "qoi_path": local_qoi,
        "join_path": local_join,
        "join_summary_path": local_join_summary,
        "render_status_path": local_render_status,
        "render_job_path": local_render_job,
        "published_import_path": import_path,
        "manifest": load_json(local_manifest),
        "inventory": load_json(local_inventory),
        "qoi_row": load_csv_row(local_qoi),
        "join_summary": load_json(local_join_summary) if local_join_summary.exists() else {},
    }
    payload["joined_contract_rows"] = []
    payload["joined_contract_fieldnames"] = []
    if local_join.exists():
        payload["joined_contract_fieldnames"], payload["joined_contract_rows"] = load_csv_rows(local_join)
    return payload


def build_contract_rows(source_payload: dict) -> list[dict[str, str]]:
    row = source_payload["registry"]
    qoi_row = source_payload["qoi_row"]
    variant_label = case_variant_label(row["case_id"])
    matched_test_id = source_payload["join_summary"].get("matched_test_id", base_case_id(row["case_id"]))
    readiness = comparison_ready(qoi_row)
    note = disposition_note(qoi_row)

    if source_payload["joined_contract_rows"]:
        contract_rows = [dict(item) for item in source_payload["joined_contract_rows"]]
    else:
        contract_rows = [
            {
                "test_id": matched_test_id,
                "two_d_case_id": row["source_id"],
                "two_d_selection_basis": "ethan_intake_mean_abs_mdot_from_4_sections",
                "two_d_mdot_full_kgs": qoi_row.get("mdot_mean_abs_kg_s", ""),
                "two_d_q_external_loss_w": qoi_row.get("final_total_wall_heat_abs_w", ""),
                "flow_alignment_note": "No canonical reference join was available at publish time; row carries direct intake metrics only.",
            }
        ]

    enriched = []
    for contract_row in contract_rows:
        enriched_row = dict(contract_row)
        enriched_row.update(
            {
                "ethan_source_id": row["source_id"],
                "ethan_case_id": row["case_id"],
                "ethan_base_test_id": matched_test_id,
                "ethan_variant_label": variant_label,
                "ethan_fluid": qoi_row.get("fluid", ""),
                "ethan_turbulence_model": qoi_row.get("turbulence_model", ""),
                "ethan_run_status": qoi_row.get("run_status", ""),
                "ethan_termination_reason": qoi_row.get("run_termination_reason", ""),
                "ethan_validation_status": qoi_row.get("validation_status", ""),
                "ethan_convergence_reached": qoi_row.get("convergence_reached", ""),
                "ethan_convergence_dTsigma": qoi_row.get("convergence_dTsigma", ""),
                "comparison_ready": readiness,
                "disposition_note": note,
            }
        )
        enriched.append(enriched_row)
    return enriched


def main() -> int:
    args = parse_args()
    config = load_workspace_config()
    publish_root = resolve_workspace_path(config["cross_model_publish_root"])
    multi_case = len(args.source_id) > 1
    if multi_case and not args.campaign_slug:
        raise SystemExit("--campaign-slug is required when publishing multiple source ids into one campaign.")

    source_payloads = [load_source_payload(source_id, publish_root) for source_id in args.source_id]
    source_payloads.sort(key=lambda item: item["registry"]["source_id"])
    first_row = source_payloads[0]["registry"]
    month_stamp = datetime.now().astimezone().strftime("%Y-%m")
    campaign_slug = args.campaign_slug or build_campaign_slug(first_row["case_id"], config["default_campaign_prefix"], multi_case)

    campaign_root = publish_root / "campaigns" / campaign_slug
    journal_path = publish_root / "journals" / month_stamp / f"{campaign_slug}.md"
    checkpoint_path = publish_root / "operational_notes" / campaign_slug / "CHECKPOINT.md"
    manifest_path = campaign_root / "manifest.json"
    provenance_path = campaign_root / "data" / "provenance_index.csv"
    contract_path = campaign_root / "data" / "cross_model_case_contract.csv"
    join_summary_path = campaign_root / "data" / "cross_model_join_summary_by_source.json"

    campaign_manifest = {
        "generated_at": iso_timestamp(),
        "workspace_root": "cross_model_comparison",
        "campaign_root": f"cross_model_comparison/campaigns/{campaign_slug}",
        "native_outputs_policy": config["native_outputs_policy"],
        "source_count": len(source_payloads),
        "import_manifests": {
            payload["registry"]["source_id"]: f"cross_model_comparison/imports/{payload['published_import_path'].name}"
            for payload in source_payloads
        },
    }

    provenance_rows = []
    contract_rows = []
    join_summary_by_source = {}
    for payload in source_payloads:
        row = payload["registry"]
        qoi_row = payload["qoi_row"]
        provenance_rows.append(
            {
                "source_id": row["source_id"],
                "case_id": row["case_id"],
                "source_root": row["source_root"],
                "local_manifest": str(payload["manifest_path"]),
                "published_manifest": str(payload["published_import_path"]),
                "inventory_json": str(payload["inventory_path"]),
                "qoi_csv": str(payload["qoi_path"]),
                "join_summary_json": str(payload["join_summary_path"]) if payload["join_summary_path"].exists() else "",
                "render_status_json": str(payload["render_status_path"]) if payload["render_status_path"].exists() else "",
                "render_job_sbatch": str(payload["render_job_path"]) if payload["render_job_path"].exists() else "",
                "run_status": qoi_row.get("run_status", ""),
                "convergence_reached": qoi_row.get("convergence_reached", ""),
            }
        )
        contract_rows.extend(build_contract_rows(payload))
        if payload["join_summary"]:
            join_summary_by_source[row["source_id"]] = payload["join_summary"]

    if provenance_path.exists():
        _, existing_rows = load_csv_rows(provenance_path)
        provenance_rows = merge_rows(existing_rows, provenance_rows, ("source_id",))
    provenance_rows.sort(key=lambda item: item["source_id"])

    if contract_path.exists():
        _, existing_rows = load_csv_rows(contract_path)
        contract_rows = merge_rows(existing_rows, contract_rows, ("ethan_source_id", "two_d_case_id", "test_id"))
    contract_rows.sort(key=lambda item: (item.get("test_id", ""), item.get("ethan_variant_label", ""), item.get("ethan_source_id", "")))

    provenance_fieldnames = union_fieldnames(provenance_rows, [
        "source_id",
        "case_id",
        "source_root",
        "local_manifest",
        "published_manifest",
        "inventory_json",
        "qoi_csv",
        "join_summary_json",
        "render_status_json",
        "render_job_sbatch",
        "run_status",
        "convergence_reached",
    ])
    contract_fieldnames = union_fieldnames(contract_rows, [
        "test_id",
        "ethan_source_id",
        "ethan_case_id",
        "ethan_base_test_id",
        "ethan_variant_label",
        "ethan_fluid",
        "ethan_turbulence_model",
        "ethan_run_status",
        "ethan_termination_reason",
        "ethan_validation_status",
        "ethan_convergence_reached",
        "ethan_convergence_dTsigma",
        "comparison_ready",
        "disposition_note",
        "two_d_case_id",
        "two_d_selection_basis",
        "two_d_mdot_full_kgs",
        "two_d_q_external_loss_w",
        "flow_alignment_note",
    ])

    if not args.dry_run:
        ensure_dir(campaign_root / "data")
        ensure_dir(campaign_root / "reports")
        ensure_dir((campaign_root / "data" / "source_manifests"))
        ensure_dir((publish_root / "imports"))
        ensure_dir(journal_path.parent)
        ensure_dir(checkpoint_path.parent)
        json_dump(manifest_path, campaign_manifest)
        for payload in source_payloads:
            json_dump(payload["published_import_path"], payload["manifest"])
            json_dump(campaign_root / "data" / "source_manifests" / f"{payload['registry']['source_id']}.json", payload["manifest"])
        csv_dump(provenance_path, provenance_fieldnames, provenance_rows)
        csv_dump(contract_path, contract_fieldnames, contract_rows)
        json_dump(join_summary_path, join_summary_by_source)

    fluids = Counter(payload["qoi_row"].get("fluid", "") for payload in source_payloads)
    run_statuses = Counter(payload["qoi_row"].get("run_status", "") for payload in source_payloads)
    convergence_counts = Counter(str(payload["qoi_row"].get("convergence_reached", "")) for payload in source_payloads)
    comparison_counts = Counter(row.get("comparison_ready", "") for row in contract_rows)
    incomplete_sources = [
        payload["registry"]["source_id"]
        for payload in source_payloads
        if payload["qoi_row"].get("run_status", "") not in {"completed", "terminated"}
        or str(payload["qoi_row"].get("convergence_reached", "")).lower() != "true"
    ]

    write_text(
        campaign_root / "TODO.md",
        "\n".join(
            [
                "# TODO",
                "",
                "- Continue or explicitly disposition rows marked `restart_or_audit_required` or `convergence_audit_required` before paper-facing use.",
                "- Keep Jin and Kirst salt-property variants as separate comparison-contract rows while preserving their shared base `salt_test_n` mapping.",
                "- Do not mix setup-only water `kOmegaSSTLM` cases into result claims until solver outputs exist.",
                "- Submit generated render jobs only when field figures are actually needed for reporting.",
                "",
            ]
        ),
        args.dry_run,
    )
    write_text(
        campaign_root / "reports" / "research_question.md",
        "\n".join(
            [
                "# Research Question",
                "",
                "How should the staged `modern_runs` batch be represented in the canonical cross-model comparison contract so that Jin/Kirst salt-property variants remain separate rows, preserve their shared base test mapping, and carry explicit readiness/disposition status?",
                "",
            ]
        ),
        args.dry_run,
    )
    write_text(
        campaign_root / "reports" / "comparison_overview.md",
        "\n".join(
            [
                "# Comparison Overview",
                "",
                f"- Campaign slug: `{campaign_slug}`",
                f"- Source count: `{len(source_payloads)}`",
                f"- Fluids: `{dict(fluids)}`",
                f"- Run statuses: `{dict(run_statuses)}`",
                f"- Convergence reached counts: `{dict(convergence_counts)}`",
                f"- Comparison-ready counts: `{dict(comparison_counts)}`",
                "- Jin/Kirst salt-property variants are published as separate rows keyed by their own `ethan_source_id` / `two_d_case_id`, while `test_id` remains the shared base `salt_test_n` contract id.",
                "- Water laminar rows are published as direct-intake rows without forcing an unavailable canonical reference join.",
                "",
            ]
        ),
        args.dry_run,
    )
    write_text(
        campaign_root / "reports" / "summary_interpretation.md",
        "\n".join(
            [
                "# Summary Interpretation",
                "",
                "- This campaign now supports multi-row Ethan intake publication rather than overwriting a single case contract row.",
                "- Variant-aware handling is now explicit: Jin and Kirst remain distinct rows while preserving their shared base test mapping.",
                "- Readiness is carried in the contract itself so incomplete, converged-but-review-required, and comparison-candidate rows are distinguishable without relying on memory or ad hoc notes.",
                "",
            ]
        ),
        args.dry_run,
    )
    write_text(
        journal_path,
        "\n".join(
            [
                f"# {campaign_slug}",
                "",
                "## Research question",
                "",
                "Publish the staged `modern_runs` batch into a canonical multi-row comparison contract that keeps Jin/Kirst salt-property variants separate while preserving their shared base test mapping and explicit readiness status.",
                "",
                "## Observed output",
                "",
                f"- Published/updated `{len(source_payloads)}` staged intake rows.",
                f"- Run statuses: `{dict(run_statuses)}`",
                f"- Convergence reached counts: `{dict(convergence_counts)}`",
                f"- Comparison-ready counts: `{dict(comparison_counts)}`",
                "",
                "## Interpretation",
                "",
                "- The campaign contract can now hold multiple Ethan rows in one package instead of a single overwritten row.",
                "- Salt-property variants no longer require an ambiguous one-row mapping strategy.",
                "- Rows still requiring restart or convergence audit remain explicitly flagged inside the contract rather than silently excluded.",
                "",
                "## Sources",
                "",
                *[f"- `{payload['registry']['source_id']}` from `{payload['registry']['source_root']}`" for payload in source_payloads],
                "",
                "## Next suggested analysis or runs",
                "",
                "- Review rows marked `restart_or_audit_required` or `convergence_audit_required` before any validation claims.",
                "- Continue using campaign-level local tables under `work_products/campaigns/2026-06-01_modern_runs_first_batch/` as the local source of truth for diagnostic review.",
                "",
            ]
        ),
        args.dry_run,
    )
    followup_lines = [f"- `{source_id}`" for source_id in incomplete_sources] if incomplete_sources else ["- No immediate restart-or-audit rows remain."]

    write_text(
        checkpoint_path,
        "\n".join(
            [
                "# Checkpoint",
                "",
                f"Date: `{iso_timestamp()}`",
                f"Task: `{campaign_slug}`",
                "",
                "## Goal",
                "",
                "Publish a multi-row Ethan intake campaign package with variant-aware contract handling and explicit readiness/disposition metadata.",
                "",
                "## Key outputs",
                "",
                "- campaign manifest",
                "- published source import manifests",
                "- merged provenance index",
                "- merged cross-model case contract with separate variant rows",
                "- join summaries by source id",
                "- dated journal entry",
                "",
                "## Remaining follow-up",
                "",
                *followup_lines,
                "",
            ]
        ),
        args.dry_run,
    )

    print(
        json.dumps(
            {
                "campaign_slug": campaign_slug,
                "campaign_root": str(campaign_root),
                "journal_path": str(journal_path),
                "checkpoint_path": str(checkpoint_path),
                "source_count": len(source_payloads),
                "comparison_ready_counts": dict(comparison_counts),
                "dry_run": args.dry_run,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
