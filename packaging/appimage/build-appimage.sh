#!/bin/bash
# Build Compa.AppImage inside an Ubuntu 22.04 container via podman.
#
# Why a container?
#   1. glibc compatibility — AppImages must be built on the oldest glibc
#      you want to support. Ubuntu 22.04 has a much older glibc than
#      Fedora, giving the widest portability.
#   2. Python is *copied* (not symlinked) so the AppImage carries its own
#      interpreter, avoiding path/ABI mismatches on the target machine.
#   3. The linuxdeploy GTK plugin ships its own strip binary that chokes
#      on Fedora's .relr.dyn ELF sections — Ubuntu's toolchain avoids this.
#
# Requirements: podman

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
CONTAINER_TAG="compa-builder:ubuntu-2204"

podman rm -f compa-builder 2>/dev/null || true

# Containerfile for the build environment
cat > /tmp/Containerfile.compa << 'DOCKERFILE'
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install -y -qq \
    python3 python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-pil \
    wget file pkg-config librsvg2-dev libgirepository1.0-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /build
ENTRYPOINT ["/build/_build-inside.sh"]
DOCKERFILE

# Build the container image if not cached
if ! podman image exists "${CONTAINER_TAG}" 2>/dev/null; then
    echo "Building container image (one-time)..."
    podman build -t "${CONTAINER_TAG}" -f /tmp/Containerfile.compa
fi

# Write the in-container build script
cat > "${BUILD_DIR}/_build-inside.sh" << 'INSIDE'
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
INSIDE
chmod +x "${BUILD_DIR}/_build-inside.sh"

echo "Starting container build..."
podman run --rm --name compa-builder \
    -v "${PROJECT_ROOT}:/src:ro,z" \
    -v "${BUILD_DIR}:/build:z" \
    "${CONTAINER_TAG}"

echo ""
echo "AppImage produced at: ${BUILD_DIR}/Compa-x86_64.AppImage"
ls -lh "${BUILD_DIR}/Compa-x86_64.AppImage"

cat <<'EOF'

TODO before this is production-ready:
  1. Test the resulting Compa*.AppImage on a *different* machine/distro
     than the one it was built on — that's the real portability test.
  2. Replace the placeholder icon (idle.png) with a proper square app icon.
EOF