#!/usr/bin/env bash
# of13_env.sh — OpenFOAM Foundation v13 runtime for the Ethan TAMU loop cases.
#
# WHY THIS FILE EXISTS  (resolves blocker B1)
# -------------------------------------------
# The cases were produced with OpenFOAM Foundation **v13** plus a private custom
# boundary condition `rcExternalTemperature` (library `libRCWallBC.so`). The v12
# toolchain (tools/ofenv/of12_env.sh) reads standard-BC fields (p, p_rgh, U, rho)
# but CANNOT reconstruct the temperature field `T`, because `T` carries that
# custom BC: under v12 the OF13-compiled library loads but SEGFAULTS in the BC
# constructor (ABI mismatch). That blocked all thermal extraction (HTC, UA', Nu).
#
# A locally-built OF13 runtime exists and, combined with the OF13-compiled
# `libRCWallBC.so` and a new-enough libstdc++, reconstructs `T` natively.
# Verified 2026-06-30: `reconstructPar -fields '(T p_rgh U rho)'` succeeds on the
# salt2_jin continuation (t=7915). This file pins that exact, reproducible recipe.
#
# THE THREE INGREDIENTS (all required)
# ------------------------------------
# 1. OF13 build:   $OF13_PROJECT_DIR (built from source 2026-06-02).
# 2. libstdc++ with GLIBCXX_3.4.32:  the OF13 binaries were built with gcc/15.2.0;
#    the default gcc/9.4.0 libstdc++ lacks GLIBCXX_3.4.32 -> "version not found".
#    We prepend gcc/15.2.0 lib64 to LD_LIBRARY_PATH.
# 3. libRCWallBC.so: the custom BC, prepended to LD_LIBRARY_PATH and passed via
#    `libs (...)` in controlDict (the helper of13_libs_entry prints the line).
#
# CONFIDENCE / SCOPE
# ------------------
# - This is the NATIVE toolchain for these v13 cases, so unlike of12_env.sh there
#   is NO zone-stripping workaround needed; reconstruct full meshes + all fields.
# - It is a from-source build (gcc), not the original private tree the runs used.
#   It reproduces field reconstruction faithfully (validated on T/p_rgh/U/rho);
#   if it is ever used to RE-RUN the solver, re-validate against a known run first.
#
# USAGE
#   source tools/ofenv/of13_env.sh
#   of13_assert_ready
#   echo "$(of13_libs_entry)"   # -> libs ("/abs/path/libRCWallBC.so");  for controlDict

export OF13_PROJECT_DIR="/work/09748/andresfierro231/ls6/openfoam_runtime_recovery/2026-06-02_openfoam13/source/OpenFOAM-13"
export OF13_RCWALL_LIB="/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/libRCWallBC.so"
export OF13_GCC_LIB64="/opt/apps/gcc/15.2.0/lib64"

# --- Lmod init (non-login shells) ---
if ! command -v module >/dev/null 2>&1; then
  for _init in /etc/profile.d/z01_lmod.sh /opt/apps/lmod/lmod/init/bash; do
    # shellcheck disable=SC1090
    [ -f "${_init}" ] && source "${_init}" && break
  done
fi
module load gcc/15.2.0 >/dev/null 2>&1

# --- OF13 environment ---
# shellcheck disable=SC1091
source "${OF13_PROJECT_DIR}/etc/bashrc" >/dev/null 2>&1

# Prepend the gcc-15 libstdc++ (GLIBCXX_3.4.32) and the custom BC dir.
export LD_LIBRARY_PATH="${OF13_GCC_LIB64}:$(dirname "${OF13_RCWALL_LIB}"):${LD_LIBRARY_PATH}"

of13_libs_entry() {
  # Print the controlDict `libs` line needed to load the custom wall BC.
  echo "libs (\"${OF13_RCWALL_LIB}\");"
}

of13_assert_ready() {
  local ok=1
  if [ "${WM_PROJECT_VERSION}" != "13" ]; then
    echo "of13_env: WM_PROJECT_VERSION='${WM_PROJECT_VERSION}' (expected 13)" >&2; ok=0
  fi
  for _bin in reconstructPar foamPostProcess foamRun; do
    command -v "${_bin}" >/dev/null 2>&1 || { echo "of13_env: MISSING ${_bin}" >&2; ok=0; }
  done
  [ -f "${OF13_RCWALL_LIB}" ] || { echo "of13_env: MISSING libRCWallBC.so at ${OF13_RCWALL_LIB}" >&2; ok=0; }
  if [ "${ok}" -eq 1 ]; then
    echo "of13_env: ready (OpenFOAM Foundation 13 native; T reconstructable via libRCWallBC.so + gcc/15.2.0 libstdc++)"
    return 0
  fi
  return 1
}
