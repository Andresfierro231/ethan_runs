#!/bin/bash

# Canonical OpenFOAM 13 bootstrap for Ethan-derived LS6 runs.
# This mirrors Ethan's shared environment sequence as closely as possible
# while targeting the local canonical runtime alias under /work.

module purge
module load TACC
module load gcc/13.2.0
module load impi/21.12

export WM_MPLIB=INTELMPI
export MPI_ROOT="${I_MPI_ROOT:-}"

if [[ -z "$MPI_ROOT" || ! -d "$MPI_ROOT" ]]; then
    echo "MPI_ROOT is not set to a readable Intel MPI install" >&2
    return 1 2>/dev/null || exit 1
fi

OF13_ROOT="${OF13_ROOT:-/work/09748/andresfierro231/ls6/OpenFOAM-13/source/OpenFOAM-13}"
if [[ ! -r "$OF13_ROOT/etc/bashrc" ]]; then
    echo "OpenFOAM 13 bashrc not readable: $OF13_ROOT/etc/bashrc" >&2
    return 1 2>/dev/null || exit 1
fi

set +u
source "$OF13_ROOT/etc/bashrc" WM_MPLIB=INTELMPI
source_status=$?
set -u
if [[ $source_status -ne 0 ]]; then
    echo "Failed to source $OF13_ROOT/etc/bashrc" >&2
    return "$source_status" 2>/dev/null || exit "$source_status"
fi

# Ethan's original bootstrap loaded python3/3.9.7 afterwards. On this account
# the exact module may be incompatible with the active toolchain, so keep it
# optional and do not let it break solver startup.
if module load python3/3.9.7 >/dev/null 2>&1; then
    export OF13_OPTIONAL_PYTHON_LOADED=1
    export LD_LIBRARY_PATH="/opt/apps/gcc11_2/python3/3.9.7/lib:${LD_LIBRARY_PATH:-}"
else
    export OF13_OPTIONAL_PYTHON_LOADED=0
fi
