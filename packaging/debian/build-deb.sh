#!/bin/bash
# Build a .deb for Compa.
#
# dpkg-buildpackage expects a `debian/` folder at the project root, but we
# keep packaging scaffolding under packaging/ to avoid cluttering the repo
# root. This script symlinks packaging/debian -> debian temporarily, builds,
# then removes the symlink again.
#
# Requirements: sudo apt install build-essential debhelper devscripts

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cleanup() {
    if [ -L "${PROJECT_ROOT}/debian" ]; then
        rm "${PROJECT_ROOT}/debian"
    fi
}
trap cleanup EXIT

if [ -e "${PROJECT_ROOT}/debian" ] && [ ! -L "${PROJECT_ROOT}/debian" ]; then
    echo "A real (non-symlink) debian/ folder already exists at project root — aborting." >&2
    exit 1
fi

ln -sf "${SCRIPT_DIR}" "${PROJECT_ROOT}/debian"

cd "${PROJECT_ROOT}"
dpkg-buildpackage -us -uc -b

echo
echo "Done — the .deb should have been written one directory above the project root."
