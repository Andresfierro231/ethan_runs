#!/usr/bin/env python3.11
"""Stationary-terminal-window mesh GCI for the S13 seeded exchange-CV QOIs.

Task: TODO-S13-STATIONARY-WINDOW-QWALL-MESH-GCI-2026-07-23
Owner: claude

Scientific contract
-------------------
The S13 formal Grid Convergence Index (GCI) was previously fail-closed with
`blocked_missing_same_label_coarse_member` / `blocked_unmatched_physical_time_indices`:
the coarse continuation windows (Salt2 ~7914 s, Salt3 ~7617 s, Salt4 ~9999 s)
are at different ABSOLUTE physical times than the medium/fine terminal windows
(~517 s / ~398 s, etc.), and the packages declined to treat them as equivalent.

This builder makes the equivalence argument explicit and testable rather than
assumed: for a QOI that has reached a STATISTICALLY STATIONARY state on each
mesh, the absolute time index is immaterial -- the converged value is a property
of the (case, mesh) steady attractor, and comparing those converged values
across meshes is exactly a mesh-convergence comparison. We (1) quantify
within-window stationarity per (case, mesh, qoi) from the three sampled sub-
windows, (2) form the coarse/medium/fine triplet of stationary window means, and
(3) run the repo's ASME/Roache GCI engine (tools/analyze/compute_gci.py). Mesh-UQ
is admitted ONLY where stationarity holds AND the GCI verdict is monotonic
convergence AND the asymptotic-range ratio is within tolerance -- never on a
borrowed GCI or an assumed order.

This is a read-only interpretive pass over already-committed native-sampled
rows. It releases no source/property, freezes no candidate, and scores nothing.
It admits a mesh-UQ diagnostic (the `mesh_gci_gate` component of same-QOI UQ)
only where the math earns it.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from compute_gci import compute_gci

REPO = Path(__file__).resolve().parents[2]
WP07 = REPO / "work_products" / "2026-07"

COARSE_ROWS = (
    WP07
    / "2026-07-22"
    / "2026-07-22_s13_direct_coarse_extraction_gci_uq_chain"
    / "direct_sampled_coarse_surface_field_rows.csv"
)
MEDIUM_FINE_ROWS = (
    WP07
    / "2026-07-22"
    / "2026-07-22_s13_medium_fine_exact_label_split_rerun"
    / "aggregated_exact_label_qoi_rows.csv"
)
MESH_INVENTORY = (
    WP07
    / "2026-07-09"
    / "2026-07-09_salt_mesh_refinement_discovery"
    / "mesh_case_inventory.csv"
)

OUT = WP07 / "2026-07-23" / "2026-07-23_s13_stationary_window_qwall_mesh_gci"

QOIS = (
    "Q_wall_W",
    "mdot_exchange_positive_outward_proxy_kg_s",
    "tau_recirc_proxy_s",
    "wall_core_bulk_temperature_contrast_K",
)
CASES = ("salt_2", "salt_3", "salt_4")
# Q_wall is the trusted-wall wallHeatFlux integral (an integral heat QOI);
# the other three are local recirculation-cell exchange proxies.
STEADY_INTEGRAL_QOIS = {"Q_wall_W"}
STATIONARITY_HALF_RANGE_PCT_MAX = 0.10  # window half-range must be < 0.1% of |mean|


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def _window_stats(values: list[float]) -> dict:
    mean = sum(values) / len(values)
    half_range = (max(values) - min(values)) / 2.0
    denom = abs(mean) if mean != 0.0 else float("inf")
    half_range_pct = 100.0 * half_range / denom
    return {
        "window_mean": mean,
        "window_half_range": half_range,
        "window_half_range_pct": half_range_pct,
        "n_sub_windows": len(values),
    }


def _cell_counts() -> dict[str, int]:
    rows = _read(MESH_INVENTORY)
    counts: dict[str, int] = {}
    for r in rows:
        # Jin family, any salt test -> identical mesh topology per level.
        if r.get("fluid_variant") == "jin" and r["mesh_level"] in ("coarse", "medium", "fine"):
            counts[r["mesh_level"]] = int(r["cell_count"])
    return counts


def build() -> dict:
    coarse = _read(COARSE_ROWS)
    medfine = _read(MEDIUM_FINE_ROWS)
    counts = _cell_counts()

    n_coarse, n_medium, n_fine = counts["coarse"], counts["medium"], counts["fine"]
    # ASME V&V20 representative grid size h ~ N^(-1/3) for 3D -> ratios:
    r21 = (n_fine / n_medium) ** (1.0 / 3.0)   # h_medium / h_fine
    r32 = (n_medium / n_coarse) ** (1.0 / 3.0)  # h_coarse / h_medium

    # --- collect stationary window means per (case, mesh, qoi) ---
    def collect(rows, mesh_filter):
        acc: dict[tuple, list[float]] = {}
        for r in rows:
            case = r["case_id"]
            qoi = r["qoi_label"]
            if case not in CASES or qoi not in QOIS:
                continue
            mesh = mesh_filter(r)
            if mesh is None:
                continue
            acc.setdefault((case, mesh, qoi), []).append(float(r["value"]))
        return acc

    coarse_acc = collect(coarse, lambda r: "coarse")
    medfine_acc = collect(medfine, lambda r: r["mesh_level"] if r["mesh_level"] in ("medium", "fine") else None)

    stationarity_rows: list[dict] = []
    means: dict[tuple, float] = {}
    stationary: dict[tuple, bool] = {}
    for acc in (coarse_acc, medfine_acc):
        for (case, mesh, qoi), vals in acc.items():
            st = _window_stats(vals)
            is_stat = st["window_half_range_pct"] < STATIONARITY_HALF_RANGE_PCT_MAX
            means[(case, mesh, qoi)] = st["window_mean"]
            stationary[(case, mesh, qoi)] = is_stat
            stationarity_rows.append(
                {
                    "case_id": case,
                    "mesh_level": mesh,
                    "qoi_label": qoi,
                    "window_mean": st["window_mean"],
                    "window_half_range": st["window_half_range"],
                    "window_half_range_pct": st["window_half_range_pct"],
                    "n_sub_windows": st["n_sub_windows"],
                    "stationary": str(is_stat),
                    "stationarity_threshold_pct": STATIONARITY_HALF_RANGE_PCT_MAX,
                }
            )
    stationarity_rows.sort(key=lambda d: (d["case_id"], d["qoi_label"], d["mesh_level"]))

    # --- GCI per (case, qoi) ---
    gci_rows: list[dict] = []
    for case in CASES:
        for qoi in QOIS:
            key = lambda m: (case, m, qoi)
            if not all(key(m) in means for m in ("coarse", "medium", "fine")):
                continue
            cvals = {m: means[key(m)] for m in ("coarse", "medium", "fine")}
            all_stationary = all(stationary[key(m)] for m in ("coarse", "medium", "fine"))
            g = compute_gci(cvals["coarse"], cvals["medium"], cvals["fine"], r21, r32)
            # Mesh-UQ admission requires: all three windows stationary AND a
            # trustworthy GCI (monotonic convergence + in asymptotic range).
            mesh_uq_admitted = bool(all_stationary and g["gci_trustworthy"])
            gci_rows.append(
                {
                    "case_id": case,
                    "qoi_label": qoi,
                    "qoi_class": "steady_integral" if qoi in STEADY_INTEGRAL_QOIS else "recirc_exchange_proxy",
                    "coarse_f3": cvals["coarse"],
                    "medium_f2": cvals["medium"],
                    "fine_f1": cvals["fine"],
                    "r21": r21,
                    "r32": r32,
                    "all_windows_stationary": str(all_stationary),
                    "convergence_ratio_R": g["convergence_ratio_R"],
                    "verdict": g["verdict"],
                    "observed_order_p": g["observed_order_p"],
                    "gci_fine_pct": g["gci_fine_pct"],
                    "gci_coarse_pct": g["gci_coarse_pct"],
                    "asymptotic_range_ratio": g["asymptotic_range_ratio"],
                    "gci_trustworthy": str(g["gci_trustworthy"]),
                    "mesh_uq_admitted": str(mesh_uq_admitted),
                    "gci_note": g["gci_note"],
                }
            )

    # --- per-QOI admission rollup ---
    admission_rows: list[dict] = []
    for qoi in QOIS:
        qrows = [r for r in gci_rows if r["qoi_label"] == qoi]
        admitted = [r for r in qrows if r["mesh_uq_admitted"] == "True"]
        admission_rows.append(
            {
                "qoi_label": qoi,
                "qoi_class": "steady_integral" if qoi in STEADY_INTEGRAL_QOIS else "recirc_exchange_proxy",
                "cases_evaluated": len(qrows),
                "cases_mesh_uq_admitted": len(admitted),
                "max_gci_fine_pct": max((r["gci_fine_pct"] for r in qrows if r["gci_fine_pct"] is not None), default=None),
                "mesh_uq_status": (
                    "admitted_mesh_converged"
                    if len(admitted) == len(qrows) and qrows
                    else ("partial" if admitted else "fail_closed_mesh_unconverged")
                ),
                "source_property_release": "False",
                "candidate_freeze": "False",
            }
        )

    qwall_admitted = sum(
        1 for r in gci_rows if r["qoi_label"] == "Q_wall_W" and r["mesh_uq_admitted"] == "True"
    )
    exchange_admitted = sum(
        1 for r in gci_rows
        if r["qoi_label"] != "Q_wall_W" and r["mesh_uq_admitted"] == "True"
    )

    decision = {
        "method": "stationary_terminal_window_mesh_gci_removes_same_absolute_time_blocker_for_steady_qois",
        "r21": r21,
        "r32": r32,
        "qwall_cases_mesh_uq_admitted": qwall_admitted,
        "exchange_proxy_cases_mesh_uq_admitted": exchange_admitted,
        "overall": (
            "qwall_mesh_uq_admitted_exchange_proxies_fail_closed_mesh_unconverged"
            if qwall_admitted and not exchange_admitted
            else "see_gci_table"
        ),
        "same_qoi_mesh_gci_gate": (
            "pass_for_Q_wall_only" if qwall_admitted else "fail_closed"
        ),
        "source_property_release": False,
        "candidate_freeze": False,
        "final_score_values": 0,
        "scope_note": (
            "Q_wall is the seeded exchange-CV trusted-wall wallHeatFlux integral; its mesh-UQ "
            "admission is a mesh_gci_gate component, not a PASSIVE-H2 qambient release and not a freeze."
        ),
    }

    guardrails = [
        ("native_output_mutation", False),
        ("registry_or_admission_mutation", False),
        ("scheduler_action", False),
        ("solver_sampler_or_harvest_launch", False),
        ("fluid_or_external_edit", False),
        ("thesis_current_or_latex_edit", False),
        ("source_property_or_qwall_release", False),
        ("coefficient_admission", False),
        ("candidate_freeze", False),
        ("protected_or_final_scoring", False),
        ("fitting_or_model_selection", False),
        ("hidden_multiplier", False),
        ("borrowed_gci_or_fabricated_monotonicity", False),
        ("mesh_gci_admission_beyond_asymptotic_range_check", False),
        ("s11_s15_s6_trigger_fired", False),
        ("deletion_staging_commit_push", False),
    ]

    source_manifest = [
        ("coarse_sampled_rows", COARSE_ROWS),
        ("medium_fine_exact_label_rows", MEDIUM_FINE_ROWS),
        ("mesh_cell_count_inventory", MESH_INVENTORY),
        ("gci_engine", REPO / "tools" / "analyze" / "compute_gci.py"),
    ]

    summary = {
        "task_id": "TODO-S13-STATIONARY-WINDOW-QWALL-MESH-GCI-2026-07-23",
        "owner": "claude",
        "date": "2026-07-23",
        "n_coarse_cells": n_coarse,
        "n_medium_cells": n_medium,
        "n_fine_cells": n_fine,
        "r21": r21,
        "r32": r32,
        "gci_rows": len(gci_rows),
        "qwall_cases_mesh_uq_admitted": qwall_admitted,
        "exchange_proxy_cases_mesh_uq_admitted": exchange_admitted,
        "decision": decision["overall"],
        "same_qoi_mesh_gci_gate": decision["same_qoi_mesh_gci_gate"],
        "source_property_release": False,
        "candidate_freeze": False,
        "final_score_values": 0,
        **{f"guardrail_{k}": v for k, v in guardrails},
    }

    return {
        "stationarity": stationarity_rows,
        "gci": gci_rows,
        "admission": admission_rows,
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
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    res = build()
    OUT.mkdir(parents=True, exist_ok=True)
    _write_csv(OUT / "stationarity_evidence.csv", res["stationarity"])
    _write_csv(OUT / "mesh_gci_results.csv", res["gci"])
    _write_csv(OUT / "gci_admission_by_qoi.csv", res["admission"])
    _write_csv(
        OUT / "gci_decision.csv",
        [{"key": k, "value": v} for k, v in res["decision"].items()],
    )
    _write_csv(
        OUT / "no_mutation_guardrails.csv",
        [{"guardrail": k, "value": str(v)} for k, v in res["guardrails"]],
    )
    _write_csv(
        OUT / "source_manifest.csv",
        [
            {"role": role, "path": str(p.relative_to(REPO)), "exists": str(p.exists())}
            for role, p in res["source_manifest"]
        ],
    )
    (OUT / "summary.json").write_text(json.dumps(res["summary"], indent=2) + "\n")
    print(json.dumps(res["summary"], indent=2))


if __name__ == "__main__":
    main()
