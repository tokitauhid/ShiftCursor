#!/bin/bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────────────
# ShiftCursor — Local AppImage Builder (for testing)
# ──────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="ShiftCursor"
VERSION="test"
VENV_DIR=".venv"

echo "══════════════════════════════════════════════════════"
echo "  ShiftCursor AppImage Builder (local testing)"
echo "══════════════════════════════════════════════════════"

# ── Step 1: Activate venv ──
echo ""
echo "▶ [1/7] Activating virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    echo "ERROR: No .venv found. Create one first."
    exit 1
fi
source "$VENV_DIR/bin/activate"

# Verify required packages
python3 -c "import PySide6, win2xcur, wand" 2>/dev/null || {
    echo "ERROR: Missing Python packages. Run: pip install PySide6 win2xcur wand"
    exit 1
}
command -v pyinstaller >/dev/null 2>&1 || {
    echo "ERROR: PyInstaller not found. Run: pip install pyinstaller"
    exit 1
}

echo "  ✓ venv OK ($(python3 --version))"

# ── Step 2: Locate ImageMagick shared libraries ──
echo ""
echo "▶ [2/7] Locating ImageMagick shared libraries..."

MAGICK_LIB_DIR=$(mktemp -d "${SCRIPT_DIR}/magick_libs_XXXXXX")
trap "rm -rf '$MAGICK_LIB_DIR'" EXIT

# Find and copy the real .so files + create the symlinks that wand expects
for lib_base in libMagickWand libMagickCore; do
    # Get all registered paths from ldconfig
    while IFS= read -r so_path; do
        if [ -f "$so_path" ]; then
            real_path=$(readlink -f "$so_path")
            base_name=$(basename "$so_path")
            real_name=$(basename "$real_path")

            # Copy the real file if not already copied
            if [ ! -f "$MAGICK_LIB_DIR/$real_name" ]; then
                cp "$real_path" "$MAGICK_LIB_DIR/$real_name"
                echo "  Copied: $real_name"
            fi

            # Create symlink if the registered name differs from the real name
            if [ "$base_name" != "$real_name" ] && [ ! -e "$MAGICK_LIB_DIR/$base_name" ]; then
                ln -s "$real_name" "$MAGICK_LIB_DIR/$base_name"
                echo "  Symlink: $base_name -> $real_name"
            fi
        fi
    done < <(ldconfig -p | grep "$lib_base" | awk '{print $NF}' | sort -u)

    # Also create the unversioned .so symlink that wand looks for via MAGICK_HOME
    # wand searches for e.g. libMagickWand-7.Q16HDRI.so (no version suffix)
    for f in "$MAGICK_LIB_DIR"/${lib_base}-*.so.*; do
        [ -f "$f" ] || continue
        fname=$(basename "$f")
        # Extract the base pattern (e.g., libMagickWand-7.Q16HDRI) and create .so symlink
        # Pattern: libMagickWand-7.Q16HDRI.so.10.0.2 -> libMagickWand-7.Q16HDRI.so
        unversioned=$(echo "$fname" | sed 's/\.so\..*/\.so/')
        if [ ! -e "$MAGICK_LIB_DIR/$unversioned" ]; then
            ln -s "$fname" "$MAGICK_LIB_DIR/$unversioned"
            echo "  Symlink: $unversioned -> $fname"
        fi
    done
done

echo ""
echo "  Libraries staged in: $MAGICK_LIB_DIR"
ls -la "$MAGICK_LIB_DIR/"

# ── Step 3: Build with PyInstaller ──
echo ""
echo "▶ [3/7] Building with PyInstaller..."

# Clean previous builds
rm -rf build/ dist/ "${APP_NAME}.spec"

# Build the --add-binary flags for each file in our magick lib dir
MAGICK_ADD_BINARIES=""
for f in "$MAGICK_LIB_DIR"/*; do
    # Only add real files and symlinks
    if [ -f "$f" ] || [ -L "$f" ]; then
        MAGICK_ADD_BINARIES="$MAGICK_ADD_BINARIES --add-binary $f:_magick_libs"
    fi
done

pyinstaller \
    --name "$APP_NAME" \
    --windowed \
    --onedir \
    --noconfirm \
    --clean \
    --hidden-import PySide6.QtSvg \
    --hidden-import win2xcur \
    --collect-all wand \
    $MAGICK_ADD_BINARIES \
    shiftcursor_app.py

echo "  ✓ PyInstaller build complete"

# ── Step 4: Verify the .so files are in the bundle ──
echo ""
echo "▶ [4/7] Verifying bundled libraries..."
BUNDLE_DIR="dist/${APP_NAME}"

# Check where the magick libs ended up
if [ -d "$BUNDLE_DIR/_magick_libs" ]; then
    echo "  ✓ _magick_libs directory found in bundle:"
    ls -la "$BUNDLE_DIR/_magick_libs/" | grep -i magick
elif [ -d "$BUNDLE_DIR/_internal/_magick_libs" ]; then
    echo "  ✓ _magick_libs found in _internal:"
    ls -la "$BUNDLE_DIR/_internal/_magick_libs/" | grep -i magick
    BUNDLE_DIR="$BUNDLE_DIR"  # keep as-is, we'll handle in AppRun
else
    echo "  ⚠ Looking for magick libs in bundle..."
    find "dist/${APP_NAME}" -name "libMagick*" -type f -o -name "libMagick*" -type l 2>/dev/null
fi

# ── Step 5: Assemble AppDir ──
echo ""
echo "▶ [5/7] Assembling AppDir..."

APPDIR="${APP_NAME}.AppDir"
rm -rf "$APPDIR"

mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copy PyInstaller output
cp -r "dist/${APP_NAME}/"* "$APPDIR/usr/bin/"

# Create the magick lib/ directory where wand's MAGICK_HOME search expects it
# wand looks in ${MAGICK_HOME}/lib/libMagickWand*.so
MAGICK_DEST="$APPDIR/usr/bin/magick_home/lib"
mkdir -p "$MAGICK_DEST"

# Move the _magick_libs content to the proper location
if [ -d "$APPDIR/usr/bin/_magick_libs" ]; then
    cp -a "$APPDIR/usr/bin/_magick_libs/"* "$MAGICK_DEST/"
    rm -rf "$APPDIR/usr/bin/_magick_libs"
elif [ -d "$APPDIR/usr/bin/_internal/_magick_libs" ]; then
    cp -a "$APPDIR/usr/bin/_internal/_magick_libs/"* "$MAGICK_DEST/"
    rm -rf "$APPDIR/usr/bin/_internal/_magick_libs"
fi

echo "  Magick libs in final location:"
ls -la "$MAGICK_DEST/"

# Copy desktop file
cp shiftcursor.desktop "$APPDIR/usr/share/applications/shiftcursor.desktop"

# Generate icon
QT_QPA_PLATFORM=offscreen python3 -c "
import sys
from PySide6.QtWidgets import QApplication
app = QApplication(sys.argv)
from ui.resources import svg_to_pixmap
pm = svg_to_pixmap('mouse_pointer', color='#00BFA5', size=256)
pm.save('${APPDIR}/usr/share/icons/hicolor/256x256/apps/shiftcursor.png')
app.quit()
" 2>/dev/null || {
    echo "  ⚠ Icon generation failed (non-fatal), using placeholder"
    # Create a minimal 1x1 PNG as placeholder
    python3 -c "
from PySide6.QtGui import QImage, QColor
img = QImage(256, 256, QImage.Format.Format_ARGB32)
img.fill(QColor('#00BFA5'))
img.save('${APPDIR}/usr/share/icons/hicolor/256x256/apps/shiftcursor.png')
"
}

# Root-level copies required by AppImage
cp "$APPDIR/usr/share/applications/shiftcursor.desktop" "$APPDIR/shiftcursor.desktop"
cp "$APPDIR/usr/share/icons/hicolor/256x256/apps/shiftcursor.png" "$APPDIR/shiftcursor.png"

# Create AppRun
cat > "$APPDIR/AppRun" << 'APPRUN'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/bin/magick_home/lib:${HERE}/usr/bin:${LD_LIBRARY_PATH}"
export MAGICK_HOME="${HERE}/usr/bin/magick_home"
exec "${HERE}/usr/bin/ShiftCursor" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

echo "  ✓ AppDir assembled"

# ── Step 6: Quick smoke test (run the binary directly) ──
echo ""
echo "▶ [6/7] Smoke test — running binary directly..."

# Test that the binary can at least import successfully
export LD_LIBRARY_PATH="$SCRIPT_DIR/$APPDIR/usr/bin/magick_home/lib:$SCRIPT_DIR/$APPDIR/usr/bin:${LD_LIBRARY_PATH:-}"
export MAGICK_HOME="$SCRIPT_DIR/$APPDIR/usr/bin/magick_home"
export QT_QPA_PLATFORM=offscreen

timeout 5 "$SCRIPT_DIR/$APPDIR/usr/bin/${APP_NAME}" --help 2>&1 && echo "  ✓ Binary runs!" || {
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        echo "  ✓ Binary started (timed out after 5s — that's normal for a GUI app)"
    else
        echo "  ⚠ Binary exited with code $EXIT_CODE (check output above)"
    fi
}

unset LD_LIBRARY_PATH MAGICK_HOME QT_QPA_PLATFORM

# ── Step 7: Package as AppImage ──
echo ""
echo "▶ [7/7] Packaging AppImage..."

# Download appimagetool if not present
if [ ! -f appimagetool-x86_64.AppImage ]; then
    echo "  Downloading appimagetool..."
    wget -q https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x appimagetool-x86_64.AppImage
fi

OUTPUT_FILE="${APP_NAME}-${VERSION}-x86_64.AppImage"

ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 \
    ./appimagetool-x86_64.AppImage "$APPDIR" "$OUTPUT_FILE"

echo ""
echo "══════════════════════════════════════════════════════"
echo "  ✅ Done! Output: $OUTPUT_FILE"
echo "  Size: $(du -h "$OUTPUT_FILE" | cut -f1)"
echo ""
echo "  Test it:  ./$OUTPUT_FILE"
echo "══════════════════════════════════════════════════════"
