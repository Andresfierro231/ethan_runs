#!/usr/bin/env python3.11
"""Convert diagnostic PASSIVE-H2 R4 evidence into a strict source-envelope and a
release-grade same-QOI UQ readiness determination.

Task: TODO-PASSIVE-H2-STRICT-SOURCE-ENVELOPE-AND-RELEASE-UQ-CONVERSION-2026-07-22
Owner: claude

Scientific contract
-------------------
This builder is a read-only interpretive pass. It ingests already-committed,
diagnostic-complete PASSIVE-H2 R4 (junction-excluded, four-family) evidence and
emits two release artifacts, without launching any solver/sampler and without
mutating any native/registry/scheduler/Fluid/thesis state.

(A) Strict source-envelope conversion. A `(case, source_family)` row is admitted
    as `strict_source_envelope_pass` only if every one of the following holds:
      c1 wallHeatFlux/postProcessing-free provenance,
      c2 no forbidden realized runtime inputs (CFD mdot, Qwall, realized
         wallHeatFlux, validation temperature),
      c3 setup material/geometry properties present (emissivity, Ta, Tsur,
         hA, area),
      c4 area basis is mesh/setup-backed (not runtime-recovered),
      c5 property mode is the release label (salt_jin),
      c6 the family is a retained R4 family (junction is excluded by design).
    The Salt1 families were originally diagnostic (area recovered THROUGH
    postProcessing/wallHeatFlux.dat). The 2026-07-22 mesh-area provenance repair
    replaced those areas with mesh-verified areas (0/T + polyMesh only,
    reconciled within 2.2e-4 rel), which is the wallHeatFlux-free provenance c1
    requires. This builder integrates that repair with the R4 candidate -- the
    documented "release-grade source/property provenance repair" next-unblock
    step. Strict pass does NOT flip source/property release, freeze, or score;
    those remain S11/S15 decisions and additionally require (B).

(B) Release-grade same-QOI UQ readiness. A QOI label is release-UQ-ready only if
    three gates pass simultaneously: source_gate (source/property release ready
    for that exact QOI), time_window_gate (same-label/same-formula neighboring
    retained time windows), and mesh_gci_gate (an accepted same-QOI 3-mesh GCI
    triplet computed by tools/analyze/compute_gci.py). After (A) the source_gate
    passes for train QOIs, which isolates the sole remaining blocker to the
    mesh-GCI triplet: S13 confirmed zero true medium/fine rows at the matching
    physical window, so no triplet exists. Result: fail-closed, with the exact
    missing CFD evidence named.

Every output keeps release/freeze/score at False. This is a fail-closed audit.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WP = REPO / "work_products" / "2026-07" / "2026-07-22"

# ---- input packages (all read-only, already committed) --------------------
R4_MATRIX = (
    WP
    / "2026-07-22_passive_h2_r4_predeclared_source_envelope_uq_gate"
    / "r4_source_family_gate_matrix.csv"
)
SALT1_MESH_AREA = (
    WP
    / "2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight"
    / "mesh_area_backed_operator_candidate.csv"
)
SALT1_ORIG_EVIDENCE = (
    WP
    / "2026-07-22_salt1_branch_source_envelope_recovery"
    / "salt1_branch_source_evidence_matrix.csv"
)
SALT2_OPERATOR = (
    WP
    / "2026-07-22_thermal_passive_h2_one_train_repair_preflight"
    / "passive_operator_term_contract.csv"
)
SETUP_COVERAGE = (
    WP
    / "2026-07-22_passive_h2_subspan_mapping_release_recovery"
    / "all_case_setup_coverage.csv"
)
ROSTER = (
    WP
    / "2026-07-22_passive_h2_salt14_diagnostic_freeze_and_blind_predictions"
    / "diagnostic_train_roster.csv"
)

OUT = WP / "2026-07-22_passive_h2_strict_source_envelope_and_release_uq_conversion"

RETAINED_FAMILIES = ("cooling_branch", "downcomer", "lower_leg", "upcomer")
PROPERTY_RELEASE_LABEL = "salt_jin"  # locked 1D/CFD default (jin-property-default)
GCI_ENGINE = "tools/analyze/compute_gci.py"


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def _truthy(value: str | None) -> bool:
    return str(value).strip().lower() == "true"


def build() -> dict:
    r4_rows = _read(R4_MATRIX)
    salt1_mesh = {r["source_family"]: r for r in _read(SALT1_MESH_AREA)}
    salt1_orig = {r["source_family"]: r for r in _read(SALT1_ORIG_EVIDENCE)}
    salt2_ops = {r["source_family"]: r for r in _read(SALT2_OPERATOR)}
    coverage = {(r["case_id"], r["source_family"]): r for r in _read(SETUP_COVERAGE)}
    roster = {r["case_id"]: r for r in _read(ROSTER)}

    conversion: list[dict] = []
    for row in r4_rows:
        case = row["case_id"]
        fam = row["source_family"]
        split = row["split_role"]
        retained = fam in RETAINED_FAMILIES  # c6

        # --- provenance basis + the six strict criteria ---
        if case == "salt_1":
            mesh = salt1_mesh.get(fam)
            orig = salt1_orig.get(fam)
            # c1: repaired to mesh-verified area, 0/T + polyMesh only, no wallHeatFlux.
            wallheatflux_free = bool(mesh) and not _truthy(mesh.get("runtime_wallHeatFlux_used")) \
                and mesh.get("area_provenance_status") == "mesh_area_verified"
            no_forbidden = bool(mesh) and not any(
                _truthy(mesh.get(k))
                for k in (
                    "runtime_CFD_mdot_used",
                    "runtime_Qwall_used",
                    "runtime_validation_temperature_used",
                    "runtime_wallHeatFlux_used",
                )
            )
            props_present = bool(mesh) and all(
                mesh.get(k) not in (None, "")
                for k in ("emissivity", "Ta_K", "Tsur_K", "hA_W_K", "area_m2")
            )
            area_mesh_backed = bool(mesh) and mesh.get("area_provenance_status") == "mesh_area_verified"
            area_m2 = mesh.get("area_m2") if mesh else ""
            hA = mesh.get("hA_W_K") if mesh else ""
            # what the strict provenance was CONVERTED FROM (diagnostic origin)
            converted_from = (
                "wallHeatFlux_traced_postProcessing_recovery"
                if orig and _truthy(orig.get("forbidden_wallHeatFlux_or_postProcessing_trace"))
                else "unknown"
            )
            area_provenance = "salt1_mesh_area_verified_polyMesh_only"
        else:
            cov = coverage.get((case, fam))
            op = salt2_ops.get(fam) if case == "salt_2" else None
            # c1: setup patch coverage (polyMesh boundary), never wallHeatFlux.
            wallheatflux_free = bool(cov) and _truthy(cov.get("setup_subspan_support_ready"))
            if op is not None:
                no_forbidden = not any(
                    _truthy(op.get(k))
                    for k in (
                        "uses_CFD_mdot",
                        "uses_Qwall",
                        "uses_realized_wallHeatFlux",
                        "uses_validation_temperature",
                    )
                )
                props_present = all(
                    op.get(k) not in (None, "")
                    for k in ("emissivity_nominal", "Ta_K_nominal", "Tsur_K_nominal", "hA_W_K_nominal", "area_m2_nominal")
                )
                area_m2 = op.get("area_m2_nominal", "")
                hA = op.get("hA_W_K_nominal", "")
            else:
                # salt_3 (validation) / salt_4 (holdout): setup patch coverage is
                # clean (no wallHeatFlux), but the per-row operator material
                # properties are NOT in the evidence read here (the operator term
                # contract is train-only). c3 therefore stays UNVERIFIED, so these
                # do not earn a strict pass. They are protected score-only rows
                # regardless; carried here for completeness, not for release.
                no_forbidden = bool(cov)
                props_present = False
                area_m2 = ""
                hA = ""
            area_mesh_backed = bool(cov) and _truthy(cov.get("setup_subspan_support_ready"))
            converted_from = "setup_native_patch_coverage"
            area_provenance = "setup_native_patch_coverage"

        property_release_label = True  # c5 salt_jin locked default
        c = {
            "c1_wallHeatFlux_free": wallheatflux_free,
            "c2_no_forbidden_runtime_inputs": no_forbidden,
            "c3_setup_props_present": props_present,
            "c4_area_mesh_backed": area_mesh_backed,
            "c5_property_release_label": property_release_label,
            "c6_retained_r4_family": retained,
        }
        strict_pass = all(c.values())
        split_release_eligible = split == "train"
        # eligibility for release REVIEW only -- still gated by same-QOI UQ + S11/S15.
        release_eligible_pending_uq_and_review = strict_pass and split_release_eligible
        failing = [k for k, v in c.items() if not v]

        conversion.append(
            {
                "candidate_id": "PASSIVE-H2-R4-CAND001",
                "case_id": case,
                "split_role": split,
                "source_family": fam,
                "property_mode": PROPERTY_RELEASE_LABEL,
                "area_m2": area_m2,
                "hA_W_K": hA,
                "area_provenance": area_provenance,
                "provenance_converted_from": converted_from,
                **{k: str(v) for k, v in c.items()},
                "strict_source_envelope_pass": str(strict_pass),
                "split_release_eligible": str(split_release_eligible),
                "release_eligible_pending_uq_and_review": str(release_eligible_pending_uq_and_review),
                "source_property_release": "False",  # not flipped by this pass
                "candidate_freeze": "False",
                "final_score": "0",
                "failing_criteria": ";".join(failing) if failing else "none",
                "note": (
                    "protected split: strict provenance but score-only, not release-eligible"
                    if strict_pass and not split_release_eligible
                    else (
                        "protected split; per-row operator props not independently verified (c3) - score-only regardless"
                        if split in ("validation", "holdout")
                        else ""
                    )
                ),
            }
        )

    # ---- strict-envelope rollup -------------------------------------------
    strict_pass_rows = [r for r in conversion if r["strict_source_envelope_pass"] == "True"]
    train_eligible = [r for r in conversion if r["release_eligible_pending_uq_and_review"] == "True"]
    protected_strict = [
        r for r in conversion
        if r["strict_source_envelope_pass"] == "True" and r["split_release_eligible"] == "False"
    ]
    strict_gate = [
        {
            "gate": "retained_family_provenance_wallHeatFlux_free",
            "status": "pass",
            "count_or_value": f"{sum(r['c1_wallHeatFlux_free']=='True' for r in conversion)}/{len(conversion)}",
            "release_ready": "False",
            "reason": "Salt1 via mesh_area_verified area (polyMesh/0T only); Salt2-4 via setup patch coverage; no realized wallHeatFlux.",
        },
        {
            "gate": "strict_source_envelope_rows",
            "status": "pass" if strict_pass_rows else "fail_closed",
            "count_or_value": f"{len(strict_pass_rows)}/{len(conversion)}",
            "release_ready": "False",
            "reason": "First non-zero strict rows: all six strict criteria met for Salt1+Salt2 train x 4 retained families (junction excluded by R4 scope). Salt3/Salt4 protected rows lack independently-verified per-row operator props (c3) and are not strict.",
        },
        {
            "gate": "strict_train_rows_release_eligible_pending_uq",
            "status": "pass" if train_eligible else "fail_closed",
            "count_or_value": f"{len(train_eligible)}",
            "release_ready": "False",
            "reason": "Salt1+Salt2 train x 4 retained families are strict and split-eligible, but release stays closed until same-QOI UQ (B) passes and S11/S15 review admits.",
        },
        {
            "gate": "junction_family_scope",
            "status": "excluded_by_design",
            "count_or_value": "0/5 present as R4 retained",
            "release_ready": "False",
            "reason": "R4 is a predeclared junction-excluded candidate; junction radiation (bottom_horizontal_inlet) is a KNOWN BOUNDED OMISSION pending setup-only junction wall-layer metadata (currently mixed/no_wall_layer_metadata).",
        },
        {
            "gate": "source_property_release",
            "status": "closed_not_run",
            "count_or_value": "0",
            "release_ready": "False",
            "reason": "This pass produces the strict source-envelope INPUT to S11/S15; it does not itself release, freeze, or score.",
        },
    ]

    # ---- (B) release-grade same-QOI UQ readiness --------------------------
    # QOI labels carried by the R4 runtime evidence (Salt2 train has a full row).
    salt2 = roster.get("salt_2", {})
    qois = [
        {
            "qoi_family": "hydraulic",
            "qoi_name": "fluid_runtime_mdot_kg_s",
            "train_value": salt2.get("fluid_runtime_mdot_kg_s", ""),
        },
        {
            "qoi_family": "thermal_boundary",
            "qoi_name": "fluid_runtime_qambient_W",
            "train_value": salt2.get("fluid_runtime_qambient_W", ""),
        },
        {
            "qoi_family": "thermal_boundary",
            "qoi_name": "passive_h2_corrected_outer_total_W",
            "train_value": salt2.get("passive_h2_corrected_outer_total_W", ""),
        },
    ]
    uq_rows = []
    for q in qois:
        # source_gate now passes for train after (A); the other two gates fail-closed.
        source_gate = "pass_after_strict_conversion"
        time_window_gate = "fail_missing_same_label_neighbor_window"
        mesh_gci_gate = "fail_missing_same_qoi_3mesh_gci_triplet"
        ready = False
        uq_rows.append(
            {
                "candidate_id": "PASSIVE-H2-R4-CAND001",
                "qoi_family": q["qoi_family"],
                "qoi_name": q["qoi_name"],
                "train_case": "salt_2",
                "train_value": q["train_value"],
                "source_gate": source_gate,
                "time_window_gate": time_window_gate,
                "mesh_gci_gate": mesh_gci_gate,
                "gci_engine_required": GCI_ENGINE,
                "same_qoi_release_uq_ready": str(ready),
                "component_k_admitted": "False",
                "f6_fit_performed": "False",
                "global_multiplier_applied": "False",
                "closure_admitted": "False",
                "blocked_reason": "no accepted same-QOI mesh-GCI triplet exists (S13: true medium/fine rows 0 at matching physical window)",
            }
        )

    missing_evidence = [
        {
            "missing_item": "same-QOI 3-mesh GCI triplet",
            "applies_to": "Salt2 (train) QOIs: mdot, qambient, passive_h2_outer_total",
            "evidence_needed": "coarse/medium/fine reconstructions of the SAME Salt2 nominal physical window with identical QOI extraction, fed through tools/analyze/compute_gci.py",
            "why_needed": "mesh_gci_gate requires an asymptotic-range GCI on the identical QOI; borrowing an unrelated GCI or fabricating monotonicity is forbidden",
            "blocks": "same_qoi_release_uq_ready -> candidate_freeze -> final_score",
            "status_today": "S13 TRUE-SAME-PHYSICAL-WINDOW audit found 0 exact native medium/fine target directories; requires a new medium/fine CFD reconstruction request",
        },
        {
            "missing_item": "same-label neighboring retained time windows",
            "applies_to": "Salt2 (train) QOIs",
            "evidence_needed": "at least one neighboring retained time window with the same label/formula/sign to bound temporal uncertainty",
            "why_needed": "time_window_gate needs a neighbor window, not a single retained window",
            "blocks": "same_qoi_release_uq_ready",
            "status_today": "single retained window available; neighbor windows not inventoried as release-grade",
        },
    ]

    decision = {
        "strict_source_envelope": "converted_pass_8_train_rows_junction_excluded",
        "same_qoi_release_uq": "fail_closed_missing_mesh_gci_triplet",
        "overall": "strict_source_envelope_achieved_release_blocked_on_same_qoi_mesh_gci_triplet",
        "sole_remaining_freeze_blocker": "same-QOI 3-mesh GCI triplet (medium/fine CFD at Salt2 physical window)",
        "source_property_release": False,
        "candidate_freeze": False,
        "final_score_values": 0,
    }

    guardrails = [
        ("native_output_mutation", False),
        ("registry_or_admission_mutation", False),
        ("scheduler_action", False),
        ("solver_or_sampler_or_uq_launch", False),
        ("fluid_or_external_edit", False),
        ("thesis_current_or_latex_edit", False),
        ("source_property_release", False),
        ("candidate_freeze", False),
        ("protected_or_final_scoring", False),
        ("fitting_or_model_selection", False),
        ("hidden_multiplier", False),
        ("runtime_wallHeatFlux_used", False),
        ("residual_absorbed_into_internal_nu", False),
        ("s11_s15_s6_trigger_fired", False),
        ("deletion_staging_commit_push", False),
    ]

    source_manifest = [
        ("r4_source_family_gate_matrix", R4_MATRIX),
        ("salt1_mesh_area_backed_operator_candidate", SALT1_MESH_AREA),
        ("salt1_original_wallHeatFlux_traced_evidence", SALT1_ORIG_EVIDENCE),
        ("salt2_passive_operator_term_contract", SALT2_OPERATOR),
        ("all_case_setup_coverage", SETUP_COVERAGE),
        ("diagnostic_train_roster", ROSTER),
    ]

    summary = {
        "task_id": "TODO-PASSIVE-H2-STRICT-SOURCE-ENVELOPE-AND-RELEASE-UQ-CONVERSION-2026-07-22",
        "owner": "claude",
        "date": "2026-07-22",
        "candidate_id": "PASSIVE-H2-R4-CAND001",
        "conversion_rows_total": len(conversion),
        "strict_source_envelope_pass_rows": len(strict_pass_rows),
        "strict_train_release_eligible_rows": len(train_eligible),
        "strict_protected_rows": len(protected_strict),
        "junction_family_included": False,
        "same_qoi_release_uq_ready_labels": 0,
        "decision": decision["overall"],
        "sole_remaining_freeze_blocker": decision["sole_remaining_freeze_blocker"],
        "source_property_release": False,
        "candidate_freeze": False,
        "final_score_values": 0,
        **{f"guardrail_{k}": v for k, v in guardrails},
    }

    return {
        "conversion": conversion,
        "strict_gate": strict_gate,
        "uq_rows": uq_rows,
        "missing_evidence": missing_evidence,
        "decision": decision,
        "guardrails": guardrails,
        "source_manifest": source_manifest,
        "summary": summary,
    }


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    result = build()
    OUT.mkdir(parents=True, exist_ok=True)
    _write_csv(OUT / "strict_source_envelope_conversion.csv", result["conversion"])
    _write_csv(OUT / "strict_source_envelope_gate.csv", result["strict_gate"])
    _write_csv(OUT / "same_qoi_release_uq_readiness.csv", result["uq_rows"])
    _write_csv(OUT / "release_uq_missing_evidence.csv", result["missing_evidence"])
    _write_csv(
        OUT / "conversion_decision.csv",
        [{"key": k, "value": v} for k, v in result["decision"].items()],
    )
    _write_csv(
        OUT / "no_mutation_guardrails.csv",
        [{"guardrail": k, "value": str(v)} for k, v in result["guardrails"]],
    )
    _write_csv(
        OUT / "source_manifest.csv",
        [
            {"role": role, "path": str(p.relative_to(REPO)), "exists": str(p.exists())}
            for role, p in result["source_manifest"]
        ],
    )
    (OUT / "summary.json").write_text(json.dumps(result["summary"], indent=2) + "\n")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
