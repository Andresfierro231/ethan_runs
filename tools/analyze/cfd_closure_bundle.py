#!/usr/bin/env python3
"""Package defended CFD-derived closure terms for downstream 1D modeling.

Workflow role:
    This is a closure-contract bundler. It reads the current defended Salt CFD
    closure recommendation tables, branch-development summaries, stale/data-need
    markers, and blocked dependency requirements, then publishes a compact
    bundle for local 1D experiments.

Inputs:
    Existing report tables from the June closure bakeoff and closure handoff
    packages. The script does not sample solver fields directly.

Outputs:
    `salt_closure_bundle.json`, closure-term contract CSV, branch policy CSV,
    README/provenance files, and an import manifest.

CLI modifiers:
    - `--output-dir` chooses the bundle destination.
    - `--manifest-path` chooses the import/provenance manifest path.

Boundaries:
    The bundle is a contract packaging layer, not new evidence and not a fit.
    It should point back to pressure, heat, time-window, and observation-table
    ledgers once those become the canonical sources.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import WORKSPACE_ROOT, csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace, safe_float


DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "work_products" / "2026-06-26_ethan_cfd_closure_bundle"
DEFAULT_MANIFEST_PATH = WORKSPACE_ROOT / "imports" / "2026-06-26_ethan_cfd_closure_bundle.json"

CLOSURE_TERM_RECOMMENDATIONS = (
    WORKSPACE_ROOT
    / "reports"
    / "2026-06"
    / "2026-06-23"
    / "2026-06-23_ethan_1d_closure_bakeoff"
    / "closure_term_recommendations.csv"
)
BRANCH_DEVELOPMENT_SUMMARY = (
    WORKSPACE_ROOT
    / "reports"
    / "2026-06"
    / "2026-06-23"
    / "2026-06-23_ethan_1d_closure_bakeoff"
    / "branch_development_summary.csv"
)
STALE_AND_DATA_NEEDS = (
    WORKSPACE_ROOT
    / "reports"
    / "2026-06"
    / "2026-06-23"
    / "2026-06-23_ethan_1d_closure_bakeoff"
    / "stale_and_data_needs.csv"
)
BLOCKED_REQUIREMENTS = (
    WORKSPACE_ROOT
    / "reports"
    / "2026-06"
    / "2026-06-19"
    / "2026-06-19_ethan_closure_to_modeling_handoff"
    / "blocked_dependency_requirements.csv"
)


@dataclass(frozen=True)
class PowerLawClosure:
    name: str
    output: str
    target_regions: tuple[str, ...]
    status: str
    current_recommendation: str
    coefficients: dict[str, float]
    re_min: float
    re_max: float
    mathematical_form: str
    validity_window: str
    recommendation_note: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Package the current defended Salt CFD-derived closure terms into a "
            "local reusable bundle for downstream 1D modeling."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--manifest-path", default=str(DEFAULT_MANIFEST_PATH))
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_bundle_payload(bundle_dir: Path) -> dict[str, Any]:
    with (bundle_dir / "salt_closure_bundle.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_bundle_term_contract_rows(bundle_dir: Path) -> list[dict[str, str]]:
    return load_csv_rows(bundle_dir / "closure_term_contract.csv")


def load_bundle_branch_policy_rows(bundle_dir: Path) -> list[dict[str, str]]:
    return load_csv_rows(bundle_dir / "branch_state_surface_policy.csv")


def parse_region_list(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in str(value).split("|") if part.strip())


def parse_coefficients(value: str) -> dict[str, float]:
    coefficients: dict[str, float] = {}
    for token in str(value).split("|"):
        token = token.strip()
        if not token or "=" not in token:
            continue
        key, raw = token.split("=", 1)
        numeric = safe_float(raw.strip())
        if numeric is not None:
            coefficients[key.strip()] = float(numeric)
    return coefficients


def parse_re_domain(value: str) -> tuple[float, float]:
    numbers = [float(match) for match in re.findall(r"-?\d+(?:\.\d+)?", str(value))]
    if len(numbers) < 2:
        raise ValueError(f"Could not parse Reynolds domain from: {value}")
    return numbers[0], numbers[1]


def load_power_law_closure(rows: list[dict[str, str]], closure_name: str) -> PowerLawClosure:
    for row in rows:
        if row.get("closure_name") != closure_name:
            continue
        re_min, re_max = parse_re_domain(row.get("validity_window", ""))
        return PowerLawClosure(
            name=closure_name,
            output=row.get("output", ""),
            target_regions=parse_region_list(row.get("target_region", "")),
            status=row.get("status", ""),
            current_recommendation=row.get("current_bakeoff_recommendation", ""),
            coefficients=parse_coefficients(row.get("coefficients_or_rule", "")),
            re_min=re_min,
            re_max=re_max,
            mathematical_form=row.get("mathematical_form", ""),
            validity_window=row.get("validity_window", ""),
            recommendation_note=row.get("recommendation_note", ""),
        )
    raise KeyError(f"Missing closure recommendation row: {closure_name}")


def evaluate_log_power_law(reynolds_number: float, coefficients: dict[str, float], indicator_value: float = 0.0) -> float:
    if reynolds_number <= 0.0:
        raise ValueError("Reynolds number must be positive")
    a = coefficients.get("a", 0.0)
    b = coefficients.get("b", 0.0)
    c = coefficients.get("c", 0.0)
    return math.exp(a + b * math.log(reynolds_number) + c * indicator_value)


def evaluate_straight_friction_factor(
    reynolds_number: float,
    region_name: str,
    closure: PowerLawClosure,
) -> dict[str, Any]:
    if region_name not in closure.target_regions:
        raise ValueError(f"Unsupported straight-friction region: {region_name}")
    indicator_value = 1.0 if region_name == "test_section_span" else 0.0
    value = evaluate_log_power_law(reynolds_number, closure.coefficients, indicator_value=indicator_value)
    return {
        "closure_name": closure.name,
        "region_name": region_name,
        "reynolds_number": reynolds_number,
        "darcy_friction_factor": value,
        "within_defended_re_domain": closure.re_min <= reynolds_number <= closure.re_max,
        "status": closure.status,
        "recommendation": closure.current_recommendation,
    }


def evaluate_left_lower_leg_nusselt(reynolds_number: float, closure: PowerLawClosure) -> dict[str, Any]:
    if "left_lower_leg" not in closure.target_regions:
        raise ValueError("Loaded Nu closure is not configured for left_lower_leg")
    value = evaluate_log_power_law(reynolds_number, closure.coefficients, indicator_value=0.0)
    return {
        "closure_name": closure.name,
        "region_name": "left_lower_leg",
        "reynolds_number": reynolds_number,
        "nusselt_number": value,
        "within_defended_re_domain": closure.re_min <= reynolds_number <= closure.re_max,
        "status": closure.status,
        "recommendation": closure.current_recommendation,
    }


def reference_curve_rows(closure: PowerLawClosure, region_names: tuple[str, ...]) -> list[dict[str, Any]]:
    sample_res = [
        closure.re_min,
        closure.re_min + 0.25 * (closure.re_max - closure.re_min),
        closure.re_min + 0.50 * (closure.re_max - closure.re_min),
        closure.re_min + 0.75 * (closure.re_max - closure.re_min),
        closure.re_max,
    ]
    rows: list[dict[str, Any]] = []
    for region_name in region_names:
        for reynolds_number in sample_res:
            if closure.output == "fD":
                evaluation = evaluate_straight_friction_factor(reynolds_number, region_name, closure)
                rows.append(
                    {
                        "closure_name": closure.name,
                        "region_name": region_name,
                        "reynolds_number": reynolds_number,
                        "output_name": "darcy_friction_factor",
                        "output_value": evaluation["darcy_friction_factor"],
                        "within_defended_re_domain": evaluation["within_defended_re_domain"],
                    }
                )
            else:
                evaluation = evaluate_left_lower_leg_nusselt(reynolds_number, closure)
                rows.append(
                    {
                        "closure_name": closure.name,
                        "region_name": region_name,
                        "reynolds_number": reynolds_number,
                        "output_name": "nusselt_number",
                        "output_value": evaluation["nusselt_number"],
                        "within_defended_re_domain": evaluation["within_defended_re_domain"],
                    }
                )
    return rows


def build_branch_policy_rows(branch_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    for row in branch_rows:
        branch_name = row.get("branch_name", "")
        branch_role = row.get("branch_role", "")
        dominant_fit_status = row.get("dominant_fit_status", "")
        if branch_name == "left_lower_leg":
            primary_mode = "primary_ua_and_direct_nu"
        elif branch_name in {"left_upper_leg", "test_section_span"}:
            primary_mode = "primary_ua_state_surface_only"
        elif branch_name == "upcomer":
            primary_mode = "primary_ua_sensitivity_only"
        else:
            primary_mode = "residual_or_blocked"
        output_rows.append(
            {
                "branch_name": branch_name,
                "branch_role": branch_role,
                "primary_model_mode": primary_mode,
                "direct_nu_allowed": branch_name == "left_lower_leg",
                "direct_nu_status": "provisional_defended_limited_domain" if branch_name == "left_lower_leg" else "not_admitted",
                "primary_ua_allowed": branch_name in {"left_lower_leg", "left_upper_leg", "test_section_span", "upcomer"},
                "secondary_htc_allowed": branch_name in {"left_lower_leg", "left_upper_leg", "test_section_span", "upcomer"},
                "mean_re_effective": safe_float(row.get("mean_re_effective")),
                "mean_nu_effective": safe_float(row.get("mean_nu_effective")),
                "mean_htc_effective_w_m2_k": safe_float(row.get("mean_htc_effective_w_m2_k")),
                "ua_start_w_m_k": safe_float(row.get("ua_start_w_m_k")),
                "ua_end_w_m_k": safe_float(row.get("ua_end_w_m_k")),
                "mean_support_fraction": safe_float(row.get("mean_support_fraction")),
                "mean_residual_fraction_of_wall_heat": safe_float(row.get("mean_residual_fraction_of_wall_heat")),
                "dominant_fit_status": dominant_fit_status,
                "domain_note": row.get("domain_note", ""),
                "modeling_note": row.get("modeling_note", ""),
            }
        )
    return output_rows


def build_bundle_payload(
    *,
    friction_closure: PowerLawClosure,
    nu_closure: PowerLawClosure,
    closure_rows: list[dict[str, str]],
    branch_policy_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, str]],
    blocked_rows: list[dict[str, str]],
) -> dict[str, Any]:
    recommendation_rows = {
        row["closure_name"]: row
        for row in closure_rows
        if row.get("closure_name")
    }
    return {
        "generated_at": iso_timestamp(),
        "family_scope": "salt_only",
        "distributed_friction": {
            "closure_name": friction_closure.name,
            "status": friction_closure.status,
            "current_recommendation": friction_closure.current_recommendation,
            "target_regions": list(friction_closure.target_regions),
            "coefficients": friction_closure.coefficients,
            "reynolds_domain": {"min": friction_closure.re_min, "max": friction_closure.re_max},
            "mathematical_form": friction_closure.mathematical_form,
            "note": friction_closure.recommendation_note,
        },
        "direct_nusselt": {
            "closure_name": nu_closure.name,
            "status": nu_closure.status,
            "current_recommendation": nu_closure.current_recommendation,
            "target_regions": list(nu_closure.target_regions),
            "coefficients": nu_closure.coefficients,
            "reynolds_domain": {"min": nu_closure.re_min, "max": nu_closure.re_max},
            "mathematical_form": nu_closure.mathematical_form,
            "note": nu_closure.recommendation_note,
        },
        "primary_ua_surface": {
            "closure_name": "primary_ua_profile_library",
            "status": recommendation_rows["primary_ua_profile_library"]["status"],
            "current_recommendation": recommendation_rows["primary_ua_profile_library"]["current_bakeoff_recommendation"],
            "target_regions": list(parse_region_list(recommendation_rows["primary_ua_profile_library"]["target_region"])),
            "note": recommendation_rows["primary_ua_profile_library"]["recommendation_note"],
        },
        "secondary_htc_surface": {
            "closure_name": "secondary_htc_profile_library",
            "status": recommendation_rows["secondary_htc_profile_library"]["status"],
            "current_recommendation": recommendation_rows["secondary_htc_profile_library"]["current_bakeoff_recommendation"],
            "target_regions": list(parse_region_list(recommendation_rows["secondary_htc_profile_library"]["target_region"])),
            "note": recommendation_rows["secondary_htc_profile_library"]["recommendation_note"],
        },
        "residual_terms": {
            "hydraulic": recommendation_rows["hydraulic_residual_bucket"],
            "thermal": recommendation_rows["thermal_residual_bucket"],
        },
        "blocked_terms": {
            row["dependency_or_gap"]: {
                "current_status": row.get("current_status", ""),
                "missing_requirement": row.get("missing_requirement", ""),
            }
            for row in blocked_rows
        },
        "branch_policy": branch_policy_rows,
        "follow_on_gaps": stale_rows,
    }


def write_readme(output_dir: Path, payload: dict[str, Any]) -> None:
    friction = payload["distributed_friction"]
    nu_term = payload["direct_nusselt"]
    ua_term = payload["primary_ua_surface"]
    blocked_topics = ", ".join(sorted(payload["blocked_terms"].keys()))
    readme = f"""# Ethan CFD Closure Bundle

Generated: `{payload["generated_at"]}`

## Purpose

This bundle packages the current defended Salt CFD-derived closure terms into a
single local machine-readable contract for downstream 1D modeling work.

## Current admitted terms

- straight distributed friction: `{friction["closure_name"]}` on `{", ".join(friction["target_regions"])}` with defended Reynolds window `{friction["reynolds_domain"]["min"]:.2f}` to `{friction["reynolds_domain"]["max"]:.2f}`
- primary thermal conductance surface: `{ua_term["closure_name"]}` on `{", ".join(ua_term["target_regions"])}`
- limited direct `Nu`: `{nu_term["closure_name"]}` on `{", ".join(nu_term["target_regions"])}` with defended Reynolds window `{nu_term["reynolds_domain"]["min"]:.2f}` to `{nu_term["reynolds_domain"]["max"]:.2f}`

## Explicitly not promoted

- blocked or incomplete topics carried through from the source handoff: `{blocked_topics}`
- direct downcomer or cooler-side internal `Nu`
- feature-resolved defended `K_eff`

## Artifacts

- `salt_closure_bundle.json`: machine-readable closure contract
- `closure_term_contract.csv`: normalized closure-term table
- `branch_state_surface_policy.csv`: branchwise `UA'` / HTC / direct-`Nu` policy rows
- `reference_curve_samples.csv`: sampled friction and direct-`Nu` values across the defended Reynolds windows
- `blocked_term_followons.csv`: exact blocked or missing follow-on requirements
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def build_bundle(output_dir: Path, manifest_path: Path) -> dict[str, Any]:
    ensure_dir(output_dir)
    closure_rows = load_csv_rows(CLOSURE_TERM_RECOMMENDATIONS)
    branch_rows = load_csv_rows(BRANCH_DEVELOPMENT_SUMMARY)
    stale_rows = load_csv_rows(STALE_AND_DATA_NEEDS)
    blocked_rows = load_csv_rows(BLOCKED_REQUIREMENTS)

    friction_closure = load_power_law_closure(closure_rows, "straight_friction_class_aware_re_power_law")
    nu_closure = load_power_law_closure(closure_rows, "left_lower_leg_nu_branch_aware_re_power_law")

    branch_policy_rows = build_branch_policy_rows(branch_rows)
    reference_rows = reference_curve_rows(friction_closure, friction_closure.target_regions) + reference_curve_rows(
        nu_closure, nu_closure.target_regions
    )
    combined_followon_rows: list[dict[str, Any]] = []
    for row in blocked_rows:
        combined_followon_rows.append(
            {
                "source_kind": "blocked_requirement",
                "topic": row.get("dependency_or_gap", ""),
                "status": row.get("current_status", ""),
                "missing_requirement": row.get("missing_requirement", ""),
                "why_it_matters": "",
                "can_use_frozen_now": "",
                "next_artifact_or_action": row.get("missing_requirement", ""),
            }
        )
    for row in stale_rows:
        combined_followon_rows.append(
            {
                "source_kind": "stale_or_data_need",
                "topic": row.get("topic", ""),
                "status": row.get("current_gap", ""),
                "missing_requirement": row.get("current_gap", ""),
                "why_it_matters": row.get("why_it_matters", ""),
                "can_use_frozen_now": row.get("can_use_frozen_now", ""),
                "next_artifact_or_action": row.get("next_artifact_or_action", ""),
            }
        )
    closure_contract_rows: list[dict[str, Any]] = []
    for row in closure_rows:
        normalized = dict(row)
        normalized["parsed_target_regions"] = "|".join(parse_region_list(row.get("target_region", "")))
        try:
            re_min, re_max = parse_re_domain(row.get("validity_window", ""))
        except ValueError:
            re_min = math.nan
            re_max = math.nan
        normalized["re_min"] = re_min
        normalized["re_max"] = re_max
        normalized["parsed_coefficients_json"] = json.dumps(parse_coefficients(row.get("coefficients_or_rule", "")), sort_keys=True)
        closure_contract_rows.append(normalized)

    bundle_payload = build_bundle_payload(
        friction_closure=friction_closure,
        nu_closure=nu_closure,
        closure_rows=closure_rows,
        branch_policy_rows=branch_policy_rows,
        stale_rows=stale_rows,
        blocked_rows=blocked_rows,
    )

    csv_dump(output_dir / "closure_term_contract.csv", list(closure_contract_rows[0].keys()), closure_contract_rows)
    csv_dump(output_dir / "branch_state_surface_policy.csv", list(branch_policy_rows[0].keys()), branch_policy_rows)
    csv_dump(output_dir / "reference_curve_samples.csv", list(reference_rows[0].keys()), reference_rows)
    csv_dump(output_dir / "blocked_term_followons.csv", list(combined_followon_rows[0].keys()), combined_followon_rows)
    json_dump(output_dir / "salt_closure_bundle.json", bundle_payload)
    write_readme(output_dir, bundle_payload)

    summary = {
        "generated_at": bundle_payload["generated_at"],
        "family_scope": "salt_only",
        "straight_friction_status": friction_closure.status,
        "straight_friction_region_count": len(friction_closure.target_regions),
        "direct_nu_status": nu_closure.status,
        "direct_nu_region_count": len(nu_closure.target_regions),
        "primary_ua_region_count": len(bundle_payload["primary_ua_surface"]["target_regions"]),
        "blocked_term_count": len(bundle_payload["blocked_terms"]),
        "follow_on_gap_count": len(stale_rows),
    }
    json_dump(output_dir / "summary.json", summary)

    manifest = {
        "generated_at": bundle_payload["generated_at"],
        "task_id": "AGENT-138",
        "purpose": "Local Salt CFD closure bundle for downstream 1D modeling",
        "source_artifacts": [
            relative_to_workspace(CLOSURE_TERM_RECOMMENDATIONS),
            relative_to_workspace(BRANCH_DEVELOPMENT_SUMMARY),
            relative_to_workspace(STALE_AND_DATA_NEEDS),
            relative_to_workspace(BLOCKED_REQUIREMENTS),
        ],
        "output_root": relative_to_workspace(output_dir),
        "outputs": [
            relative_to_workspace(output_dir / "README.md"),
            relative_to_workspace(output_dir / "closure_term_contract.csv"),
            relative_to_workspace(output_dir / "branch_state_surface_policy.csv"),
            relative_to_workspace(output_dir / "reference_curve_samples.csv"),
            relative_to_workspace(output_dir / "blocked_term_followons.csv"),
            relative_to_workspace(output_dir / "salt_closure_bundle.json"),
            relative_to_workspace(output_dir / "summary.json"),
        ],
        "summary": summary,
    }
    json_dump(manifest_path, manifest)
    return summary


def main() -> int:
    args = parse_args()
    build_bundle(Path(args.output_dir), Path(args.manifest_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
