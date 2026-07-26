#!/bin/bash
set -euo pipefail
ARCH="$(uname -m)"
APPDIR="/build/Compa.AppDir"
TOOLS_DIR="/build/.tools"
PYTHON_LIBS="${APPDIR}/usr/lib/python3-libs"

mkdir -p "${TOOLS_DIR}" "${APPDIR}/usr/bin" "${APPDIR}/usr/share/compa" \
         "${APPDIR}/usr/share/applications" \
         "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

echo "Copying application files..."
cp /src/companion.py        "${APPDIR}/usr/share/compa/"
cp -r /src/assets            "${APPDIR}/usr/share/compa/"
cp /src/packaging/appimage/AppRun "${APPDIR}/AppRun"
chmod +x "${APPDIR}/AppRun"
cp /src/packaging/appimage/compa.desktop "${APPDIR}/usr/share/applications/"
cp /src/packaging/appimage/compa.desktop "${APPDIR}/compa.desktop"

echo "Bundling Python interpreter..."
cp "$(command -v python3)" "${APPDIR}/usr/bin/python3"

echo "Bundling Python packages (gi, cairo, PIL)..."
mkdir -p "${PYTHON_LIBS}"
SYS_DIRS=$(python3 -c "import site; print('\n'.join(site.getsitepackages()))")
for mod in gi cairo PIL; do
    found=0
    for d in $SYS_DIRS; do
        if [ -d "$d/$mod" ]; then
            cp -r "$d/$mod" "$PYTHON_LIBS/"
            found=1
            break
        fi
    done
    if [ "$found" = "0" ]; then
        echo "WARNING: could not find $mod in site-packages" >&2
    fi
done

cp /src/assets/tux/poses/idle.png "${APPDIR}/compa.png"

fetch_tool() {
    local url="$1" out="$2"
    if [ ! -x "${out}" ]; then
        echo "Downloading $(basename "${out}")..."
        wget -q -O "${out}" "${url}"
        chmod +x "${out}"
    fi
}

fetch_tool \
    "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-${ARCH}.AppImage" \
    "${TOOLS_DIR}/linuxdeploy-${ARCH}.AppImage"

fetch_tool \
    "https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/master/linuxdeploy-plugin-gtk.sh" \
    "${TOOLS_DIR}/linuxdeploy-plugin-gtk.sh"

fetch_tool \
    "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${ARCH}.AppImage" \
    "${TOOLS_DIR}/appimagetool-${ARCH}.AppImage"

# FUSE is not available in the container, extract AppImages instead
echo "Extracting linuxdeploy..."
"${TOOLS_DIR}/linuxdeploy-${ARCH}.AppImage" --appimage-extract
mv squashfs-root "${TOOLS_DIR}/linuxdeploy-extracted"

echo "Running linuxdeploy with the GTK plugin..."
export DEPLOY_GTK_VERSION=3
"${TOOLS_DIR}/linuxdeploy-extracted/AppRun" \
    --appdir "${APPDIR}" \
    --plugin gtk \
    --icon-file /src/assets/tux/poses/idle.png \
    --desktop-file /src/packaging/appimage/compa.desktop || true

echo "Running appimagetool..."
"${TOOLS_DIR}/appimagetool-${ARCH}.AppImage" --appimage-extract
mv squashfs-root "${TOOLS_DIR}/appimagetool-extracted"
"${TOOLS_DIR}/appimagetool-extracted/AppRun" \
    "${APPDIR}" \
    "/build/Compa-x86_64.AppImage"

echo "Build finished successfully."
