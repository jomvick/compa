#!/bin/bash
# Build Compa.AppImage.
#
# Must be run on a Linux machine with GTK3 already installed (build on an
# Ubuntu/Debian box for best compatibility with older glibc — AppImages
# generally only run on distros with a glibc >= the one they were built
# against).
#
# Requirements on the build machine:
#   sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-pil wget
#
# This script downloads linuxdeploy + its GTK plugin (which knows how to
# bundle GTK3, its typelibs, icon themes, etc.) the first time it runs, then
# reuses the cached copies on subsequent runs.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
APPDIR="${BUILD_DIR}/Compa.AppDir"
TOOLS_DIR="${SCRIPT_DIR}/.tools"

mkdir -p "${TOOLS_DIR}" "${BUILD_DIR}"

fetch_tool () {
    local url="$1" out="$2"
    if [ ! -x "${out}" ]; then
        echo "Downloading $(basename "${out}")..."
        wget -q -O "${out}" "${url}"
        chmod +x "${out}"
    fi
}

ARCH="$(uname -m)"

fetch_tool \
    "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-${ARCH}.AppImage" \
    "${TOOLS_DIR}/linuxdeploy-${ARCH}.AppImage"

fetch_tool \
    "https://github.com/linuxdeploy/linuxdeploy-plugin-gtk/releases/download/continuous/linuxdeploy-plugin-gtk.sh" \
    "${TOOLS_DIR}/linuxdeploy-plugin-gtk.sh"

fetch_tool \
    "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${ARCH}.AppImage" \
    "${TOOLS_DIR}/appimagetool-${ARCH}.AppImage"

echo "Cleaning previous AppDir..."
rm -rf "${APPDIR}"
mkdir -p "${APPDIR}/usr/bin" "${APPDIR}/usr/share/compa" "${APPDIR}/usr/share/applications" "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

echo "Copying application files..."
cp "${PROJECT_ROOT}/companion.py" "${APPDIR}/usr/share/compa/"
cp -r "${PROJECT_ROOT}/assets"     "${APPDIR}/usr/share/compa/"
cp "${SCRIPT_DIR}/AppRun"          "${APPDIR}/AppRun"
chmod +x "${APPDIR}/AppRun"
cp "${SCRIPT_DIR}/compa.desktop"   "${APPDIR}/usr/share/applications/"
cp "${SCRIPT_DIR}/compa.desktop"   "${APPDIR}/compa.desktop"

ln -sf "$(command -v python3)" "${APPDIR}/usr/bin/python3"

# Bundle PyGObject, pycairo, and Pillow into the AppDir. These are
# pure-Python + C-extension packages that linuxdeploy's GTK plugin
# does not pick up automatically, yet companion.py cannot start
# without them.
echo "Bundling PyGObject, pycairo, Pillow..."
"${APPDIR}/usr/bin/python3" -m pip install \
    --target="${APPDIR}/usr/lib/python3-libs" \
    --no-input --quiet \
    PyGObject pycairo Pillow 2>&1 | tail -3

if [ ! -f "${PROJECT_ROOT}/assets/tux/README.md" ] && [ ! -d "${PROJECT_ROOT}/assets/tux/poses" ]; then
    echo "WARNING: assets/tux/poses not found — the AppImage will run with no sprites." >&2
fi

echo "Running linuxdeploy with the GTK plugin..."
export DEPLOY_GTK_VERSION=3
"${TOOLS_DIR}/linuxdeploy-${ARCH}.AppImage" \
    --appdir "${APPDIR}" \
    --plugin gtk \
    --icon-file "${PROJECT_ROOT}/assets/tux/poses/idle.png" \
    --icon-filename compa \
    --desktop-file "${SCRIPT_DIR}/compa.desktop" \
    --output appimage

mv Compa*.AppImage "${BUILD_DIR}/" 2>/dev/null || true

cat <<'EOF'

Done (or check the log above for errors).

TODO before this is production-ready:
  1. Test the resulting Compa*.AppImage on a *different* machine/distro
     than the one it was built on — that's the real portability test.
  2. If the pip install step above picks up the wrong (system) PyGObject
     version, try replacing `--target` with `--root="${APPDIR}"` and
     adjust PYTHONPATH accordingly.
  3. Replace the icon-file above with a proper square app icon once one
     exists (currently reusing the idle sprite as a placeholder).
EOF
