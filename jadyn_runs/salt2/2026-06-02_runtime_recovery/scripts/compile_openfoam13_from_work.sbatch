#!/bin/bash
#SBATCH -J of13_build
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
#SBATCH -N 1
#SBATCH -n 16
#SBATCH -t 08:00:00
#SBATCH -o /work/09748/andresfierro231/ls6/OpenFOAM-13/build_logs/of13_build_%j.out
#SBATCH -e /work/09748/andresfierro231/ls6/OpenFOAM-13/build_logs/of13_build_%j.err

set -euo pipefail

INSTALL_ROOT="${INSTALL_ROOT:-/work/09748/andresfierro231/ls6/OpenFOAM-13}"
SOURCE_ROOT="$INSTALL_ROOT/source"
OF_DIR="$SOURCE_ROOT/OpenFOAM-13"
THIRD_DIR="$SOURCE_ROOT/ThirdParty-13"
LOG_DIR="$INSTALL_ROOT/build_logs"

mkdir -p "$LOG_DIR"
if [[ ! -d "$OF_DIR" || ! -d "$THIRD_DIR" ]]; then
    echo "Expected source directories are missing under $SOURCE_ROOT" >&2
    exit 1
fi

export WM_NCOMPPROCS="${SLURM_NTASKS:-16}"
module load intel/24.1 impi/21.12
export MPI_ROOT="${MPI_ROOT:-${TACC_IMPI_DIR:-}}"
if [[ -z "$MPI_ROOT" || ! -d "$MPI_ROOT" ]]; then
    echo "MPI_ROOT is not set to a readable Intel MPI install" >&2
    exit 1
fi
cd "$SOURCE_ROOT"
set +eu
source "$OF_DIR/etc/bashrc" WM_MPLIB=INTELMPI
source_status=$?
set -eu
if [[ $source_status -ne 0 ]]; then
    echo "Failed to source $OF_DIR/etc/bashrc with WM_MPLIB=INTELMPI" >&2
    exit "$source_status"
fi
./OpenFOAM-13/Allwmake -j "$WM_NCOMPPROCS" 2>&1 | tee "$LOG_DIR/allwmake_$(date +%Y%m%dT%H%M%S).log"
