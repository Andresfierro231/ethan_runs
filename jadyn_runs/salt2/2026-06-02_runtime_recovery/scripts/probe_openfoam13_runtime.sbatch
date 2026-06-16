#!/bin/bash
#SBATCH -J of13_probe
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 00:15:00
#SBATCH -o /work/09748/andresfierro231/ls6/OpenFOAM-13/build_logs/of13_probe_%j.out
#SBATCH -e /work/09748/andresfierro231/ls6/OpenFOAM-13/build_logs/of13_probe_%j.err

set -euo pipefail

INSTALL_ROOT="${INSTALL_ROOT:-/work/09748/andresfierro231/ls6/OpenFOAM-13}"
OF_DIR="${OF_DIR:-$INSTALL_ROOT/source/OpenFOAM-13}"
RCWALLBC_LIBDIR="${RCWALLBC_LIBDIR:-/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data}"

if [[ ! -r "$OF_DIR/etc/bashrc" ]]; then
    echo "OpenFOAM bashrc not readable: $OF_DIR/etc/bashrc" >&2
    exit 1
fi
if [[ ! -r "$RCWALLBC_LIBDIR/libRCWallBC.so" ]]; then
    echo "Missing libRCWallBC.so under: $RCWALLBC_LIBDIR" >&2
    exit 1
fi

module load intel/24.1 impi/21.12
export MPI_ROOT="${MPI_ROOT:-${TACC_IMPI_DIR:-}}"
if [[ -z "$MPI_ROOT" || ! -d "$MPI_ROOT" ]]; then
    echo "MPI_ROOT is not set to a readable Intel MPI install" >&2
    exit 1
fi
set +eu
source "$OF_DIR/etc/bashrc" WM_MPLIB=INTELMPI
source_status=$?
set -eu
if [[ $source_status -ne 0 ]]; then
    echo "Failed to source $OF_DIR/etc/bashrc with WM_MPLIB=INTELMPI" >&2
    exit "$source_status"
fi
export LD_LIBRARY_PATH="$RCWALLBC_LIBDIR:${LD_LIBRARY_PATH:-}"

echo "BASHRC_OK"
which foamRun
echo "FOAM_RUN_HELP_START"
foamRun -help | head -20
echo "FOAM_RUN_HELP_END"
ls -l "$RCWALLBC_LIBDIR/libRCWallBC.so"
