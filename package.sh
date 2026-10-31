#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_ZIP="$DIR/HyperOS_Camera_breeze_Recovery_Flashable.zip"
TMP_DIR=$(mktemp -d /tmp/breeze_cam_zip.XXXXXX)

echo "==> Packaging Recovery Flashable ZIP..."
trap "rm -rf $TMP_DIR" EXIT

# Copy META-INF and scripts
cp -rf "$DIR/META-INF" "$TMP_DIR/"
cp -f "$DIR/customize.sh" "$TMP_DIR/"
cp -f "$DIR/module.prop" "$TMP_DIR/"
cp -f "$DIR/service.sh" "$TMP_DIR/"
cp -f "$DIR/post-fs-data.sh" "$TMP_DIR/"
cp -f "$DIR/sepolicy.rule" "$TMP_DIR/"

# Copy proprietary files as system partition layout
mkdir -p "$TMP_DIR/system"
cp -rf "$DIR/proprietary/"* "$TMP_DIR/system/"

# Create the ZIP
cd "$TMP_DIR"
zip -r9 "$OUT_ZIP" .

echo "==> Done! Flashable ZIP generated at:"
echo "    $OUT_ZIP"
