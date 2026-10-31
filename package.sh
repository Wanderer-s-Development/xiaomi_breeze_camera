#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_ZIP="$DIR/HyperOS_Camera_breeze_Recovery_Flashable.zip"
TMP_DIR=$(mktemp -d /tmp/breeze_aosp_cam_zip.XXXXXX)

echo "==> Packaging AOSP Recovery Flashable ZIP..."
trap "rm -rf $TMP_DIR" EXIT

# Copy META-INF (with AOSP certs & update-binary)
cp -rf "$DIR/META-INF" "$TMP_DIR/"

# Copy toybox-arm64 (for standalone POSIX environment in AOSP Recovery)
cp -f "$DIR/toybox-arm64" "$TMP_DIR/"

# Copy addon.d survival script
mkdir -p "$TMP_DIR/addon.d"
cp -rf "$DIR/addon.d/"* "$TMP_DIR/addon.d/"

# Copy proprietary camera components
mkdir -p "$TMP_DIR/proprietary"
cp -rf "$DIR/proprietary/"* "$TMP_DIR/proprietary/"

# Create the ZIP
cd "$TMP_DIR"
rm -f "$OUT_ZIP"
zip -r9 "$OUT_ZIP" .

echo "==> Done! AOSP Recovery Flashable ZIP generated at:"
echo "    $OUT_ZIP"
