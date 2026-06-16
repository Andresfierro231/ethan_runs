#!/bin/bash
set -euo pipefail

INSTALL_ROOT="${INSTALL_ROOT:-/work/09748/andresfierro231/ls6/openfoam_runtime_recovery/2026-06-02_openfoam13}"
SOURCE_ROOT="$INSTALL_ROOT/source"
MANIFEST_PATH="$INSTALL_ROOT/SOURCE_MANIFEST.json"
OF_SOURCE_URL="http://dl.openfoam.org/source/13"
THIRD_PARTY_URL="http://dl.openfoam.org/third-party/13"

mkdir -p "$SOURCE_ROOT"
cd "$SOURCE_ROOT"

if [[ ! -d OpenFOAM-13 ]]; then
    wget -O - "$OF_SOURCE_URL" | tar xvz
    mv OpenFOAM-13-version-13 OpenFOAM-13
fi

if [[ ! -d ThirdParty-13 ]]; then
    wget -O - "$THIRD_PARTY_URL" | tar xvz
    mv ThirdParty-13-version-13 ThirdParty-13
fi

cat > "$MANIFEST_PATH" <<EOF
{
  "downloaded_at": "$(date --iso-8601=seconds)",
  "install_root": "$INSTALL_ROOT",
  "source_root": "$SOURCE_ROOT",
  "openfoam_source_url": "$OF_SOURCE_URL",
  "third_party_source_url": "$THIRD_PARTY_URL",
  "openfoam_dir": "$SOURCE_ROOT/OpenFOAM-13",
  "third_party_dir": "$SOURCE_ROOT/ThirdParty-13"
}
EOF

echo "Downloaded OpenFOAM 13 source pack under: $SOURCE_ROOT"
echo "Wrote manifest: $MANIFEST_PATH"
