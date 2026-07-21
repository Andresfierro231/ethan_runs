#!/usr/bin/env bash
# of12_env.sh — reproducible OpenFOAM environment for reading Ethan's TAMU loop cases.
#
# WHY THIS FILE EXISTS
# --------------------
# The 2026-06-30 inspection flagged reproducibility (action item #6): the cases
# were produced with OpenFOAM Foundation v13 plus a private custom boundary
# condition (`libRCWallBC.so`) that is NOT installed on LS6, and no OF runtime
# was on PATH. This script pins the ONE toolchain combination on LS6 that can
# actually open these cases, so post-processing is reproducible from a single
# `source`.
#
# DECISION + JUSTIFICATION
# ------------------------
# - The cases are Foundation v13 collated (`decomposedBlockData`, binary,
#   `processors64/`). LS6 offers `openfoam/12` (Foundation) and
#   `openfoam/v2406` (ESI). We choose Foundation **v12** because:
#     * It is the same fork (Foundation), so dictionary/IO conventions match;
#       ESI v2406 uses different field/utility conventions and would not read a
#       Foundation case cleanly.
#     * Foundation keeps the collated `decomposedBlockData` binary layout stable
#       across v12/v13, so v12 utilities read v13 field files for standard
#       boundary conditions (verified: reconstructPar succeeds on p/p_rgh/U/rho).
#   This is a documented *approximation*: v12 ≠ v13. It is valid ONLY for
#   reading/sampling already-converged fields with standard BCs. It must NOT be
#   used to re-run the solver or to reconstruct the temperature field `T`,
#   because `T` carries the custom `rcExternalTemperature` BC whose library is
#   absent (reconstructing `T` would fail to instantiate the patch type).
#
# CONFIDENCE BOUNDARY
# -------------------
# Reconstruct/sample ONLY these standard-BC fields with this env: p, p_rgh, U,
# phi, rho (and derived volume fields Re/Pr/Nu/Gr/Ra/Ri the solver already
# wrote). For anything needing `T` boundary values, recover the real v13 tree +
# libRCWallBC.so first (see operational_notes/06-26/30/2026-06-30_cfd_1d_closure_workflow.md).
#
# USAGE
#   source tools/ofenv/of12_env.sh        # sets up modules + PATH
#   of12_assert_ready                     # optional: verify tools resolve
#
# This script is intentionally idempotent and safe to source repeatedly.

# --- locate and initialise Lmod (non-login shells need this explicitly) -------
if ! command -v module >/dev/null 2>&1; then
  for _init in /etc/profile.d/z01_lmod.sh /opt/apps/lmod/lmod/init/bash; do
    # shellcheck disable=SC1090
    [ -f "${_init}" ] && source "${_init}" && break
  done
fi

# --- pinned toolchain (see DECISION above) ------------------------------------
# Reload silently; the OF module requires the intel/24.1 + impi/21.12 toolchain.
module load intel/24.1 impi/21.12 openfoam/12 >/dev/null 2>&1

# The LS6 openfoam/12 modulefile only prepends PATH/LD_LIBRARY_PATH; it does not
# export WM_* vars. Export the install root explicitly so downstream scripts can
# find utilities without re-parsing the modulefile.
export OF12_PROJECT_DIR="/home1/apps/intel24/impi21/OpenFOAM/OpenFOAM-12"
export OF12_APPBIN="${OF12_PROJECT_DIR}/platforms/linux64IcxDPInt32Opt/bin"

# Fields safe to reconstruct/sample with this env (standard BCs only).
export OF12_SAFE_FIELDS="p p_rgh U phi rho"

of12_assert_ready() {
  local ok=1
  for _bin in reconstructPar foamPostProcess foamDictionary; do
    if ! command -v "${_bin}" >/dev/null 2>&1; then
      echo "of12_env: MISSING ${_bin} on PATH" >&2
      ok=0
    fi
  done
  if [ "${ok}" -eq 1 ]; then
    echo "of12_env: ready (OpenFOAM Foundation 12; reading v13 cases, standard-BC fields only: ${OF12_SAFE_FIELDS})"
    return 0
  fi
  return 1
}
