from __future__ import annotations

import copy
import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.common import WORKSPACE_ROOT, get_registry_row, load_case_metadata


DEFAULT_SOURCE_ID = "val_salt_test_2_coarse_mesh_laminar"
DEFAULT_TARGET_DS_M = 0.01
DEFAULT_WALL_FIELDS = ("wallShearStress", "yPlus")
DEFAULT_PRESSURE_FIELDS = ("p", "p_rgh")
DEFAULT_THERMAL_FIELDS = ("T", "U", "wallHeatFlux")
DEFAULT_ANALYSIS_REQUIRED_FIELDS = DEFAULT_WALL_FIELDS + DEFAULT_PRESSURE_FIELDS + DEFAULT_THERMAL_FIELDS
DEFAULT_HEAT_WINDOW_COUNT = 50
FLOW_DIRECTION_HINT_STATUS = "manual_profile_assumption_not_auto_validated"
FLOW_DIRECTION_HINT_MEANING = (
    "Positive aligned mass flux follows the local streamwise coordinate as declared in the case profile; "
    "the current pipeline does not infer or validate flow direction automatically."
)
REQUIRED_MAJOR_SPAN_KEYS = (
    "kind",
    "centerline_labels",
    "flow_direction_sign_hint",
    "wall_patches",
    "start_patch",
    "end_patch",
)
REQUIRED_FEATURE_BUDGET_KEYS = (
    "kind",
    "start_patch",
    "end_patch",
    "adjacent_major_spans",
)

TP_TW_LOCATIONS = (
    WORKSPACE_ROOT
    / "jadyn_runs"
    / "salt2"
    / "2026-06-01_continuation_candidate"
    / "tp_tw_probe_locations.csv"
)
METADATA_CSV = (
    WORKSPACE_ROOT
    / "reports"
    / "2026-06-04_ethan_case_metadata_index"
    / "ethan_case_metadata_index.csv"
)
SALT1_JIN_SOURCE_ID = "viscosity_screening_salt_test_1_jin_coarse_mesh"
SALT1_KIRST_SOURCE_ID = "viscosity_screening_salt_test_1_kirst_coarse_mesh"
SALT2_JIN_SOURCE_ID = "viscosity_screening_salt_test_2_jin_coarse_mesh"
SALT2_KIRST_SOURCE_ID = "viscosity_screening_salt_test_2_kirst_coarse_mesh"
SALT3_JIN_SOURCE_ID = "viscosity_screening_salt_test_3_jin_coarse_mesh"
SALT3_KIRST_SOURCE_ID = "viscosity_screening_salt_test_3_kirst_coarse_mesh"
SALT4_JIN_SOURCE_ID = "viscosity_screening_salt_test_4_jin_coarse_mesh"
SALT4_KIRST_SOURCE_ID = "viscosity_screening_salt_test_4_kirst_coarse_mesh"
WATER1_VAL_SOURCE_ID = "val_water_test_1_coarse_mesh_laminar"
WATER2_VAL_SOURCE_ID = "val_water_test_2_coarse_mesh_laminar"
WATER3_VAL_SOURCE_ID = "val_water_test_3_coarse_mesh_laminar"
WATER4_VAL_SOURCE_ID = "val_water_test_4_coarse_mesh_laminar"


@dataclass(frozen=True)
class CaseAnalysisProfile:
    profile_name: str
    source_id: str
    tp_tw_locations: Path
    major_spans: dict[str, dict[str, Any]]
    feature_budgets: dict[str, dict[str, Any]]
    thermal_patch_roles: dict[str, str]
    thermal_role_groups: dict[str, tuple[str, ...]]
    major_span_order: list[str]
    main_loop_span_order: list[str]
    loop_span_order: list[str]
    target_ds_m: float = DEFAULT_TARGET_DS_M
    heat_window_count: int = DEFAULT_HEAT_WINDOW_COUNT
    wall_fields: tuple[str, ...] = DEFAULT_WALL_FIELDS
    pressure_fields: tuple[str, ...] = DEFAULT_PRESSURE_FIELDS
    thermal_fields: tuple[str, ...] = DEFAULT_THERMAL_FIELDS
    analysis_required_fields: tuple[str, ...] = DEFAULT_ANALYSIS_REQUIRED_FIELDS
    tp_density_intercept: float = 2293.6
    tp_density_slope: float = 0.7497


class CaseAnalysisProfileContractError(ValueError):
    """Raised when a registered case-analysis profile is incomplete or inconsistent."""


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_station_centers_from_rows(rows: list[dict[str, str]]) -> dict[str, tuple[float, float, float]]:
    grouped: dict[str, list[tuple[float, float, float]]] = {}
    for row in rows:
        label = str(row["label"])
        x_value = float(row["x_m"])
        y_value = float(row["y_m"])
        z_value = float(row["z_m"])
        grouped.setdefault(label, []).append((x_value, y_value, z_value))
        if row["group"] == "TW":
            station = label.split("_", 1)[0]
            grouped.setdefault(station, []).append((x_value, y_value, z_value))
    centers: dict[str, tuple[float, float, float]] = {}
    for label, coords in grouped.items():
        xs, ys, zs = zip(*coords)
        centers[label] = (
            float(sum(xs) / len(xs)),
            float(sum(ys) / len(ys)),
            float(sum(zs) / len(zs)),
        )
    return centers


def load_station_centers_from_file(path: Path) -> dict[str, tuple[float, float, float]]:
    return load_station_centers_from_rows(load_csv_rows(path))


def require_profile_keys(
    scope: str,
    name: str,
    definition: dict[str, Any],
    required_keys: tuple[str, ...],
) -> None:
    missing = [key for key in required_keys if key not in definition]
    if missing:
        raise CaseAnalysisProfileContractError(
            f"{scope} `{name}` is missing required keys: {', '.join(missing)}"
        )


def require_nonempty_string_list(scope: str, name: str, values: Any) -> list[str]:
    if not isinstance(values, (list, tuple)) or not values:
        raise CaseAnalysisProfileContractError(f"{scope} `{name}` must be a non-empty list of strings")
    normalized = [str(value).strip() for value in values]
    if any(not value for value in normalized):
        raise CaseAnalysisProfileContractError(f"{scope} `{name}` contains an empty string entry")
    if len(set(normalized)) != len(normalized):
        raise CaseAnalysisProfileContractError(f"{scope} `{name}` contains duplicate entries")
    return normalized


def require_nonempty_string_mapping(scope: str, name: str, values: Any) -> dict[str, str]:
    if not isinstance(values, dict) or not values:
        raise CaseAnalysisProfileContractError(f"{scope} `{name}` must be a non-empty mapping of strings")
    normalized: dict[str, str] = {}
    for raw_key, raw_value in values.items():
        key = str(raw_key).strip()
        value = str(raw_value).strip()
        if not key or not value:
            raise CaseAnalysisProfileContractError(f"{scope} `{name}` contains an empty key or value")
        normalized[key] = value
    return normalized


def require_order(
    order_name: str,
    values: list[str],
    allowed_names: set[str],
    *,
    exact_set: bool,
) -> None:
    duplicates = [name for name in values if values.count(name) > 1]
    if duplicates:
        repeated = ", ".join(sorted(set(duplicates)))
        raise CaseAnalysisProfileContractError(f"`{order_name}` contains duplicate span names: {repeated}")
    unknown = [name for name in values if name not in allowed_names]
    if unknown:
        raise CaseAnalysisProfileContractError(
            f"`{order_name}` references unknown span names: {', '.join(sorted(set(unknown)))}"
        )
    if exact_set and set(values) != allowed_names:
        missing = sorted(allowed_names - set(values))
        extra = sorted(set(values) - allowed_names)
        details: list[str] = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if extra:
            details.append(f"extra {', '.join(extra)}")
        raise CaseAnalysisProfileContractError(f"`{order_name}` must cover every major span exactly once ({'; '.join(details)})")


def validate_case_analysis_profile(profile: CaseAnalysisProfile) -> None:
    if not profile.profile_name.strip():
        raise CaseAnalysisProfileContractError("`profile_name` must be non-empty")
    if not profile.source_id.strip():
        raise CaseAnalysisProfileContractError("`source_id` must be non-empty")
    if profile.target_ds_m <= 0.0:
        raise CaseAnalysisProfileContractError("`target_ds_m` must be positive")
    if profile.heat_window_count <= 0:
        raise CaseAnalysisProfileContractError("`heat_window_count` must be positive")
    if not math.isfinite(profile.tp_density_intercept):
        raise CaseAnalysisProfileContractError("`tp_density_intercept` must be finite")
    if not math.isfinite(profile.tp_density_slope):
        raise CaseAnalysisProfileContractError("`tp_density_slope` must be finite")
    if not profile.tp_tw_locations.exists():
        raise CaseAnalysisProfileContractError(
            f"`tp_tw_locations` does not exist for profile `{profile.profile_name}`: {profile.tp_tw_locations}"
        )

    required_fields = require_nonempty_string_list("profile field list", "analysis_required_fields", profile.analysis_required_fields)
    wall_fields = require_nonempty_string_list("profile field list", "wall_fields", profile.wall_fields)
    pressure_fields = require_nonempty_string_list("profile field list", "pressure_fields", profile.pressure_fields)
    thermal_fields = require_nonempty_string_list("profile field list", "thermal_fields", profile.thermal_fields)
    expected_required = set(wall_fields) | set(pressure_fields) | set(thermal_fields)
    missing_required = sorted(expected_required - set(required_fields))
    if missing_required:
        raise CaseAnalysisProfileContractError(
            "`analysis_required_fields` must include wall, pressure, and thermal fields; "
            f"missing {', '.join(missing_required)}"
        )

    station_centers = load_station_centers_from_file(profile.tp_tw_locations)
    if not station_centers:
        raise CaseAnalysisProfileContractError(
            f"`tp_tw_locations` produced no station centers for profile `{profile.profile_name}`"
        )

    major_span_names = list(profile.major_spans)
    if not major_span_names:
        raise CaseAnalysisProfileContractError("`major_spans` must be non-empty")
    major_span_name_set = set(major_span_names)

    require_order("major_span_order", profile.major_span_order, major_span_name_set, exact_set=True)
    require_order("loop_span_order", profile.loop_span_order, major_span_name_set, exact_set=True)
    require_order("main_loop_span_order", profile.main_loop_span_order, major_span_name_set, exact_set=False)

    for span_name, definition in profile.major_spans.items():
        require_profile_keys("major span", span_name, definition, REQUIRED_MAJOR_SPAN_KEYS)
        centerline_labels = require_nonempty_string_list("major span", f"{span_name}.centerline_labels", definition["centerline_labels"])
        if len(centerline_labels) < 2:
            raise CaseAnalysisProfileContractError(
                f"major span `{span_name}` must have at least two centerline labels"
            )
        missing_labels = [label for label in centerline_labels if label not in station_centers]
        if missing_labels:
            raise CaseAnalysisProfileContractError(
                f"major span `{span_name}` references missing TP/TW labels: {', '.join(missing_labels)}"
            )
        wall_patches = require_nonempty_string_list("major span", f"{span_name}.wall_patches", definition["wall_patches"])
        start_patch = str(definition["start_patch"]).strip()
        end_patch = str(definition["end_patch"]).strip()
        if not start_patch or not end_patch:
            raise CaseAnalysisProfileContractError(
                f"major span `{span_name}` must define non-empty `start_patch` and `end_patch`"
            )
        if start_patch == end_patch:
            raise CaseAnalysisProfileContractError(
                f"major span `{span_name}` has identical `start_patch` and `end_patch`"
            )
        try:
            flow_direction_sign_hint = float(definition["flow_direction_sign_hint"])
        except (TypeError, ValueError) as exc:
            raise CaseAnalysisProfileContractError(
                f"major span `{span_name}` has a non-numeric `flow_direction_sign_hint`"
            ) from exc
        if not math.isfinite(flow_direction_sign_hint) or abs(flow_direction_sign_hint) <= 0.0:
            raise CaseAnalysisProfileContractError(
                f"major span `{span_name}` must define a finite non-zero `flow_direction_sign_hint`"
            )
        if definition.get("streamwise_coordinate_method") is not None and not str(
            definition["streamwise_coordinate_method"]
        ).strip():
            raise CaseAnalysisProfileContractError(
                f"major span `{span_name}` defines an empty `streamwise_coordinate_method`"
            )
        if definition.get("mdot_face_zone") is not None and not str(definition["mdot_face_zone"]).strip():
            raise CaseAnalysisProfileContractError(
                f"major span `{span_name}` defines an empty `mdot_face_zone`"
            )
        definition["centerline_labels"] = centerline_labels
        definition["wall_patches"] = wall_patches
        definition["start_patch"] = start_patch
        definition["end_patch"] = end_patch

    thermal_patch_roles = require_nonempty_string_mapping(
        "profile thermal metadata",
        "thermal_patch_roles",
        profile.thermal_patch_roles,
    )
    known_wall_patches = flatten_profile_wall_patches(profile)
    missing_thermal_roles = [patch_name for patch_name in known_wall_patches if patch_name not in thermal_patch_roles]
    if missing_thermal_roles:
        raise CaseAnalysisProfileContractError(
            "`thermal_patch_roles` must cover every major-span wall patch; "
            f"missing {', '.join(sorted(missing_thermal_roles))}"
        )
    known_roles = set(thermal_patch_roles.values())
    thermal_role_groups = require_nonempty_string_mapping_group(
        "profile thermal metadata",
        "thermal_role_groups",
        profile.thermal_role_groups,
    )
    for group_name, roles in thermal_role_groups.items():
        unknown_roles = [role_name for role_name in roles if role_name not in known_roles]
        if unknown_roles:
            raise CaseAnalysisProfileContractError(
                f"`thermal_role_groups.{group_name}` references unknown thermal roles: "
                f"{', '.join(sorted(set(unknown_roles)))}"
            )

    if not profile.feature_budgets:
        raise CaseAnalysisProfileContractError("`feature_budgets` must be non-empty")
    for feature_name, definition in profile.feature_budgets.items():
        require_profile_keys("feature budget", feature_name, definition, REQUIRED_FEATURE_BUDGET_KEYS)
        start_patch = str(definition["start_patch"]).strip()
        end_patch = str(definition["end_patch"]).strip()
        if not start_patch or not end_patch:
            raise CaseAnalysisProfileContractError(
                f"feature budget `{feature_name}` must define non-empty `start_patch` and `end_patch`"
            )
        if start_patch == end_patch:
            raise CaseAnalysisProfileContractError(
                f"feature budget `{feature_name}` has identical `start_patch` and `end_patch`"
            )
        adjacent_spans = require_nonempty_string_list(
            "feature budget",
            f"{feature_name}.adjacent_major_spans",
            definition["adjacent_major_spans"],
        )
        unknown_adjacent = [span_name for span_name in adjacent_spans if span_name not in major_span_name_set]
        if unknown_adjacent:
            raise CaseAnalysisProfileContractError(
                f"feature budget `{feature_name}` references unknown adjacent spans: {', '.join(unknown_adjacent)}"
            )
        definition["start_patch"] = start_patch
        definition["end_patch"] = end_patch
        definition["adjacent_major_spans"] = adjacent_spans


def require_nonempty_string_mapping_group(
    scope: str,
    name: str,
    values: Any,
) -> dict[str, tuple[str, ...]]:
    if not isinstance(values, dict) or not values:
        raise CaseAnalysisProfileContractError(
            f"{scope} `{name}` must be a non-empty mapping of string lists"
        )
    normalized: dict[str, tuple[str, ...]] = {}
    for raw_key, raw_values in values.items():
        key = str(raw_key).strip()
        if not key:
            raise CaseAnalysisProfileContractError(f"{scope} `{name}` contains an empty group key")
        normalized[key] = tuple(require_nonempty_string_list(scope, f"{name}.{key}", raw_values))
    return normalized


def flatten_profile_wall_patches(profile: CaseAnalysisProfile) -> list[str]:
    patches: list[str] = []
    seen: set[str] = set()
    for span_name in profile.major_span_order:
        for patch_name in profile.major_spans[span_name]["wall_patches"]:
            normalized = str(patch_name)
            if normalized not in seen:
                seen.add(normalized)
                patches.append(normalized)
    return patches


def thermal_role_for_patch(profile: CaseAnalysisProfile, patch_name: str) -> str:
    return str(profile.thermal_patch_roles.get(str(patch_name), "other"))


def thermal_role_group_for_patch(profile: CaseAnalysisProfile, patch_name: str) -> str:
    role_name = thermal_role_for_patch(profile, patch_name)
    for group_name, role_names in profile.thermal_role_groups.items():
        if role_name in role_names:
            return str(group_name)
    return "unclassified"


def build_flow_direction_hint_metadata(profile: CaseAnalysisProfile) -> dict[str, Any]:
    return {
        "status": FLOW_DIRECTION_HINT_STATUS,
        "meaning": FLOW_DIRECTION_HINT_MEANING,
        "hints_by_span": {
            span_name: float(profile.major_spans[span_name]["flow_direction_sign_hint"])
            for span_name in profile.major_span_order
        },
    }


SALT_FAMILY_HEATER_PATCHES = {
    "pipeleg_lower_04_straight",
    "pipeleg_lower_05_straight",
    "pipeleg_lower_06_straight",
}
SALT_FAMILY_TEST_SECTION_PATCHES = {
    "pipeleg_left_04_test_section",
}
SALT_FAMILY_COOLING_BRANCH_PATCHES = {
    "pipeleg_upper_04_reducer",
    "pipeleg_upper_05_cooler",
    "pipeleg_upper_06_reducer",
}


def build_salt_family_thermal_patch_roles() -> dict[str, str]:
    roles: dict[str, str] = {}
    for definition in SALT2_MAJOR_SPANS.values():
        for patch_name in definition["wall_patches"]:
            normalized = str(patch_name)
            if normalized in SALT_FAMILY_HEATER_PATCHES:
                roles[normalized] = "heater"
            elif normalized in SALT_FAMILY_TEST_SECTION_PATCHES:
                roles[normalized] = "test_section"
            elif normalized in SALT_FAMILY_COOLING_BRANCH_PATCHES:
                roles[normalized] = "cooling_branch"
            else:
                roles[normalized] = "transport"
    return roles


SALT_FAMILY_THERMAL_ROLE_GROUPS: dict[str, tuple[str, ...]] = {
    "intended_transfer": ("heater", "cooling_branch", "test_section"),
    "parasitic_loss": ("transport",),
}


SALT2_MAJOR_SPANS: dict[str, dict[str, Any]] = {
    "lower_leg": {
        "kind": "main_loop_leg",
        "centerline_labels": ["TP1", "TW1", "TW2", "TW3", "TP2"],
        "streamwise_coordinate_method": "patch_centroid_polyline",
        "flow_direction_sign_hint": 1.0,
        "wall_patches": [
            "pipeleg_lower_01_fitting",
            "pipeleg_lower_02_straight",
            "pipeleg_lower_03_bend",
            "pipeleg_lower_04_straight",
            "pipeleg_lower_05_straight",
            "pipeleg_lower_06_straight",
            "pipeleg_lower_07_bend",
            "pipeleg_lower_08_straight",
            "pipeleg_lower_09_fitting",
        ],
        "mdot_face_zone": "mdot_pipeleg_lower_05_straight",
        "start_patch": "ncc_pipeleg_lower_01_fitting_start",
        "end_patch": "ncc_pipeleg_lower_09_fitting_end",
    },
    "right_leg": {
        "kind": "main_loop_leg",
        "centerline_labels": ["TP2", "TW4", "TW5", "TW6", "TP3"],
        "streamwise_coordinate_method": "patch_centroid_polyline",
        "flow_direction_sign_hint": 1.0,
        "wall_patches": [
            "pipeleg_right_01_lower",
            "pipeleg_right_02_middle",
            "pipeleg_right_03_upper",
        ],
        "mdot_face_zone": "mdot_pipeleg_right_02_middle",
        "start_patch": "ncc_pipeleg_right_01_lower_start",
        "end_patch": "ncc_pipeleg_right_03_upper_end",
    },
    "left_lower_leg": {
        "kind": "main_loop_leg",
        "centerline_labels": ["TP3", "TW7", "TP4"],
        "flow_direction_sign_hint": 1.0,
        "wall_patches": [
            "pipeleg_left_07_lower",
            "pipeleg_left_06_connector",
        ],
        "mdot_face_zone": None,
        "start_patch": "ncc_pipeleg_left_07_lower_end",
        "end_patch": "ncc_pipeleg_left_06_connector_start",
    },
    "test_section_span": {
        "kind": "test_section_leg",
        "centerline_labels": ["TP4", "TP5"],
        "flow_direction_sign_hint": 1.0,
        "wall_patches": [
            "pipeleg_left_05_fitting",
            "pipeleg_left_04_test_section",
            "pipeleg_left_03_fitting",
        ],
        "mdot_face_zone": "mdot_pipeleg_left_04_test_section",
        "start_patch": "ncc_pipeleg_left_05_fitting_end",
        "end_patch": "ncc_pipeleg_left_03_fitting_start",
    },
    "left_upper_leg": {
        "kind": "main_loop_leg",
        "centerline_labels": ["TP5", "TW8", "TP6"],
        "flow_direction_sign_hint": 1.0,
        "wall_patches": [
            "pipeleg_left_02_connector",
            "pipeleg_left_01_upper",
        ],
        "mdot_face_zone": None,
        "start_patch": "ncc_pipeleg_left_02_connector_end",
        "end_patch": "ncc_pipeleg_left_01_upper_start",
    },
    "upper_leg": {
        "kind": "main_loop_leg",
        "centerline_labels": ["TP6", "TW11", "TW10", "TW9", "TP1"],
        "flow_direction_sign_hint": 1.0,
        "wall_patches": [
            "pipeleg_upper_09_straight",
            "pipeleg_upper_08_bend",
            "pipeleg_upper_07_straight",
            "pipeleg_upper_06_reducer",
            "pipeleg_upper_05_cooler",
            "pipeleg_upper_04_reducer",
            "pipeleg_upper_03_straight",
            "pipeleg_upper_02_bend",
            "pipeleg_upper_01_straight",
        ],
        "mdot_face_zone": "mdot_pipeleg_upper_05_cooler",
        "start_patch": "ncc_pipeleg_upper_09_straight_end",
        "end_patch": "ncc_pipeleg_upper_01_straight_start",
    },
}

SALT2_FEATURE_BUDGETS: dict[str, dict[str, Any]] = {
    "corner_lower_left": {
        "kind": "corner",
        "start_patch": "ncc_pipeleg_left_07_lower_end",
        "end_patch": "ncc_pipeleg_lower_01_fitting_start",
        "adjacent_major_spans": ["left_lower_leg", "lower_leg"],
    },
    "corner_lower_right": {
        "kind": "corner",
        "start_patch": "ncc_pipeleg_lower_09_fitting_end",
        "end_patch": "ncc_pipeleg_right_01_lower_start",
        "adjacent_major_spans": ["lower_leg", "right_leg"],
    },
    "corner_upper_right": {
        "kind": "corner",
        "start_patch": "ncc_pipeleg_right_03_upper_end",
        "end_patch": "ncc_pipeleg_upper_01_straight_start",
        "adjacent_major_spans": ["right_leg", "upper_leg"],
    },
    "corner_upper_left": {
        "kind": "corner",
        "start_patch": "ncc_pipeleg_upper_09_straight_end",
        "end_patch": "ncc_pipeleg_left_01_upper_start",
        "adjacent_major_spans": ["upper_leg", "left_upper_leg"],
    },
    "test_section_complex": {
        "kind": "connector_expansion_contraction",
        "start_patch": "ncc_pipeleg_left_02_connector_end",
        "end_patch": "ncc_pipeleg_left_06_connector_start",
        "adjacent_major_spans": ["left_upper_leg", "test_section_span", "left_lower_leg"],
    },
}

SALT2_MAJOR_SPAN_ORDER = [
    "lower_leg",
    "right_leg",
    "left_lower_leg",
    "test_section_span",
    "left_upper_leg",
    "upper_leg",
]

SALT2_MAIN_LOOP_SPAN_ORDER = [
    "lower_leg",
    "right_leg",
    "left_lower_leg",
    "left_upper_leg",
    "upper_leg",
]

SALT2_LOOP_SPAN_ORDER = [
    "lower_leg",
    "right_leg",
    "upper_leg",
    "left_upper_leg",
    "test_section_span",
    "left_lower_leg",
]


def build_salt_family_case_profile(source_id: str, profile_name: str) -> CaseAnalysisProfile:
    return CaseAnalysisProfile(
        profile_name=profile_name,
        source_id=source_id,
        tp_tw_locations=TP_TW_LOCATIONS,
        major_spans=SALT2_MAJOR_SPANS,
        feature_budgets=SALT2_FEATURE_BUDGETS,
        thermal_patch_roles=build_salt_family_thermal_patch_roles(),
        thermal_role_groups=SALT_FAMILY_THERMAL_ROLE_GROUPS,
        major_span_order=SALT2_MAJOR_SPAN_ORDER,
        main_loop_span_order=SALT2_MAIN_LOOP_SPAN_ORDER,
        loop_span_order=SALT2_LOOP_SPAN_ORDER,
    )


def build_water_family_case_profile(source_id: str, profile_name: str) -> CaseAnalysisProfile:
    # The staged modern-run water validation cases share the same loop topology,
    # TP/TW registration, and wall/connector patch names as the Salt-family
    # screening cases. Reusing the same span and feature definitions keeps the
    # postprocessing path shared; if a water case later fails this contract, that
    # should be treated as a real cross-family geometry mismatch rather than
    # hidden behind a separate, silently diverging workflow.
    return CaseAnalysisProfile(
        profile_name=profile_name,
        source_id=source_id,
        tp_tw_locations=TP_TW_LOCATIONS,
        major_spans=SALT2_MAJOR_SPANS,
        feature_budgets=SALT2_FEATURE_BUDGETS,
        thermal_patch_roles=build_salt_family_thermal_patch_roles(),
        thermal_role_groups=SALT_FAMILY_THERMAL_ROLE_GROUPS,
        major_span_order=SALT2_MAJOR_SPAN_ORDER,
        main_loop_span_order=SALT2_MAIN_LOOP_SPAN_ORDER,
        loop_span_order=SALT2_LOOP_SPAN_ORDER,
    )


SUPPORTED_CASE_ANALYSIS_PROFILES = {
    DEFAULT_SOURCE_ID: build_salt_family_case_profile(DEFAULT_SOURCE_ID, "salt2_val_case_v1"),
    SALT1_JIN_SOURCE_ID: build_salt_family_case_profile(SALT1_JIN_SOURCE_ID, "salt1_jin_case_v1"),
    SALT1_KIRST_SOURCE_ID: build_salt_family_case_profile(SALT1_KIRST_SOURCE_ID, "salt1_kirst_case_v1"),
    SALT2_JIN_SOURCE_ID: build_salt_family_case_profile(SALT2_JIN_SOURCE_ID, "salt2_jin_case_v1"),
    SALT2_KIRST_SOURCE_ID: build_salt_family_case_profile(SALT2_KIRST_SOURCE_ID, "salt2_kirst_case_v1"),
    SALT3_JIN_SOURCE_ID: build_salt_family_case_profile(SALT3_JIN_SOURCE_ID, "salt3_jin_case_v1"),
    SALT3_KIRST_SOURCE_ID: build_salt_family_case_profile(SALT3_KIRST_SOURCE_ID, "salt3_kirst_case_v1"),
    SALT4_JIN_SOURCE_ID: build_salt_family_case_profile(SALT4_JIN_SOURCE_ID, "salt4_jin_case_v1"),
    # Salt 4 Kirst shares the same loop geometry, patch naming, and TP/TW
    # station layout as the rest of the Salt-family screening cases. Register
    # it on the same reusable profile path so any later incompatibility is
    # treated as a real shared-contract issue rather than hidden by omission.
    SALT4_KIRST_SOURCE_ID: build_salt_family_case_profile(SALT4_KIRST_SOURCE_ID, "salt4_kirst_case_v1"),
    WATER1_VAL_SOURCE_ID: build_water_family_case_profile(WATER1_VAL_SOURCE_ID, "water1_val_case_v1"),
    WATER2_VAL_SOURCE_ID: build_water_family_case_profile(WATER2_VAL_SOURCE_ID, "water2_val_case_v1"),
    WATER3_VAL_SOURCE_ID: build_water_family_case_profile(WATER3_VAL_SOURCE_ID, "water3_val_case_v1"),
    WATER4_VAL_SOURCE_ID: build_water_family_case_profile(WATER4_VAL_SOURCE_ID, "water4_val_case_v1"),
}


def get_case_analysis_profile(source_id: str) -> CaseAnalysisProfile:
    if source_id not in SUPPORTED_CASE_ANALYSIS_PROFILES:
        supported = ", ".join(sorted(SUPPORTED_CASE_ANALYSIS_PROFILES))
        raise KeyError(
            f"No case-analysis profile is registered for {source_id}. "
            f"Supported source_ids: {supported}"
        )
    profile = SUPPORTED_CASE_ANALYSIS_PROFILES[source_id]
    cloned_profile = CaseAnalysisProfile(
        profile_name=profile.profile_name,
        source_id=profile.source_id,
        tp_tw_locations=profile.tp_tw_locations,
        major_spans=copy.deepcopy(profile.major_spans),
        feature_budgets=copy.deepcopy(profile.feature_budgets),
        thermal_patch_roles=copy.deepcopy(profile.thermal_patch_roles),
        thermal_role_groups=copy.deepcopy(profile.thermal_role_groups),
        major_span_order=list(profile.major_span_order),
        main_loop_span_order=list(profile.main_loop_span_order),
        loop_span_order=list(profile.loop_span_order),
        target_ds_m=profile.target_ds_m,
        heat_window_count=profile.heat_window_count,
        wall_fields=tuple(profile.wall_fields),
        pressure_fields=tuple(profile.pressure_fields),
        thermal_fields=tuple(profile.thermal_fields),
        analysis_required_fields=tuple(profile.analysis_required_fields),
        tp_density_intercept=profile.tp_density_intercept,
        tp_density_slope=profile.tp_density_slope,
    )
    validate_case_analysis_profile(cloned_profile)
    return cloned_profile


def resolve_case_paths(source_id: str) -> tuple[Path, Path, dict[str, Any]]:
    metadata_rows = {row["source_id"]: row for row in load_csv_rows(METADATA_CSV) if row.get("source_id")}
    metadata_row = metadata_rows.get(source_id, {})
    registry_row = get_registry_row(WORKSPACE_ROOT / "registry" / "case_registry.csv", source_id)

    source_root = Path(metadata_row.get("source_root") or registry_row["source_root"]).resolve()
    runtime_root = Path(
        metadata_row.get("active_runtime_root")
        or metadata_row.get("source_root")
        or registry_row["source_root"]
    ).resolve()
    metadata = load_case_metadata(runtime_root) or load_case_metadata(source_root) or {}
    return source_root, runtime_root, metadata
