#!/usr/bin/env bash
#
# Build script for HyperOS Camera Minimal Fix Magisk Module
# Codename: breeze / breeze_in (Redmi 13 5G / POCO M6 Plus 5G)
#

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="/tmp/magisk_breeze_fix"
OUT_ZIP="/serverhive5/wandererdev/HyperOS_Camera_breeze_Fix_Magisk.zip"

echo "==> Preparing clean workspace at $WORK_DIR..."
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR/META-INF/com/google/android"

# System, product, and system_ext paths (matching Infinity-X ROM partition layout)
mkdir -p "$WORK_DIR/system/etc/device_features"
mkdir -p "$WORK_DIR/system/product/etc/device_features"
mkdir -p "$WORK_DIR/system/system_ext/etc/device_features"
mkdir -p "$WORK_DIR/system/system_ext/priv-app/MiuiCamera/lib/arm64"
mkdir -p "$WORK_DIR/system/system_ext/lib64"
mkdir -p "$WORK_DIR/system/system_ext/etc/permissions"

echo "==> Creating module.prop..."
cat << 'EOF' > "$WORK_DIR/module.prop"
id=hyperos_camera_breeze_fix
name=HyperOS Camera Fix (breeze)
version=v2.8-fixed
versionCode=280
author=Wanderer's Development
description=Fix for HyperOS Camera on breeze. Platform-signed APK (v20/640003214). Fixes watermark green corrupted band via GPU glFinish tile cache flush, forces Redmi 13 5G device watermark naming, forces _global mod_device and device_features for offline watermark, fixes 108MP Ultra HD photo saving, fixes Watermark shutter freeze (isCloudWatermarkProcessing bypassed), fixes launch VerifyError in Z5.e.V1, fixes UnsatisfiedLinkError via public.libraries.txt, fixes photo save NPE in l4.a.g, Photo 4-take freeze bypassed, Portrait role 63 single bokeh, and Night CamX RAW fix.
EOF

echo "==> Creating META-INF updater scripts..."
cat << 'EOF' > "$WORK_DIR/META-INF/com/google/android/updater-script"
#MAGISK
EOF

cat << 'EOF' > "$WORK_DIR/META-INF/com/google/android/update-binary"
#!/sbin/sh
#################################
# Magisk Module Installer Script
#################################

umask 022

ui_print() {
  echo "$1"
}

require_new_magisk() {
  ui_print "*******************************"
  ui_print " Please install Magisk v20.4+! "
  ui_print "*******************************"
  exit 1
}

OUTFD=$2
ZIPFILE=$3

mount /data 2>/dev/null

[ -f /data/adb/magisk/util_functions.sh ] || require_new_magisk
. /data/adb/magisk/util_functions.sh

[ $MAGISK_VER_CODE -lt 20400 ] && require_new_magisk

install_module

exit 0
EOF
chmod 755 "$WORK_DIR/META-INF/com/google/android/update-binary"

echo "==> Creating customize.sh..."
cat << 'EOF' > "$WORK_DIR/customize.sh"
ui_print "****************************************"
ui_print "* HyperOS Camera Color & Freeze Fix    *"
ui_print "* Device: breeze / breeze_in           *"
ui_print "* Wanderer's Development               *"
ui_print "****************************************"

DEVICE=$(getprop ro.product.device)
MODEL=$(getprop ro.product.model)
ui_print "- Detected: $DEVICE ($MODEL)"

ui_print "- Configuring system_ext partition overlay..."

# Ensure proper SELinux permissions
set_perm_recursive "$MODPATH/system" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/system_ext/priv-app/MiuiCamera" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/system_ext/priv-app/MiuiCamera/lib" 0 0 0755 0755
set_perm_recursive "$MODPATH/system/system_ext/priv-app/MiuiCamera/lib/arm64" 0 0 0755 0644
set_perm "$MODPATH/system/etc/public.libraries.txt" 0 0 0644 2>/dev/null || true
set_perm "$MODPATH/system/system_ext/etc/public.libraries.txt" 0 0 0644 2>/dev/null || true
set_perm_recursive "$MODPATH/system/etc/device_features" 0 0 0755 0644 2>/dev/null || true
set_perm_recursive "$MODPATH/system/system_ext/etc/device_features" 0 0 0755 0644 2>/dev/null || true
set_perm_recursive "$MODPATH/system/product/etc/device_features" 0 0 0755 0644 2>/dev/null || true

# Grant camera and media storage permissions to prevent File NullPointerException
ui_print "- Granting camera and media storage permissions..."
pm grant com.android.camera android.permission.READ_MEDIA_IMAGES 2>/dev/null || true
pm grant com.android.camera android.permission.READ_MEDIA_VIDEO 2>/dev/null || true
pm grant com.android.camera android.permission.CAMERA 2>/dev/null || true
pm grant com.android.camera android.permission.RECORD_AUDIO 2>/dev/null || true
pm grant com.android.camera android.permission.ACCESS_FINE_LOCATION 2>/dev/null || true
pm grant com.android.camera android.permission.ACCESS_COARSE_LOCATION 2>/dev/null || true
appops set com.android.camera MANAGE_EXTERNAL_STORAGE allow 2>/dev/null || true

ui_print "- Module successfully installed!"
ui_print "- Please reboot your device to apply the fix."
EOF

echo "==> Creating service.sh..."
cat << 'EOF' > "$WORK_DIR/service.sh"
#!/system/bin/sh
MODDIR=${0%/*}

# Wait for boot completion
while [ "$(getprop sys.boot_completed)" != "1" ]; do
  sleep 1
done

# Force native Zero Shutter Lag mode (replaces camera.disable_zsl_mode=true)
# for continuous 3A Auto White Balance / Auto Exposure convergence
resetprop -n camera.disable_zsl_mode 0

# Force global region and mod_device for offline watermark & Live Photo support
resetprop -n ro.product.mod_device breeze_in_global
resetprop -n ro.miui.customized.region india
resetprop -n ro.miui.build.region in
resetprop -n ro.boot.hwc in

# Ensure full storage / media permissions are granted after boot
appops set com.android.camera MANAGE_EXTERNAL_STORAGE allow 2>/dev/null || true
pm grant com.android.camera android.permission.READ_MEDIA_IMAGES 2>/dev/null || true
pm grant com.android.camera android.permission.READ_MEDIA_VIDEO 2>/dev/null || true
EOF
chmod 755 "$WORK_DIR/service.sh"

echo "==> Creating post-fs-data.sh..."
cat << 'EOF' > "$WORK_DIR/post-fs-data.sh"
#!/system/bin/sh
MODDIR=${0%/*}

# Set native ZSL at early boot
resetprop -n camera.disable_zsl_mode 0

# Set global region and mod_device at early boot
resetprop -n ro.product.mod_device breeze_in_global
resetprop -n ro.miui.customized.region india
resetprop -n ro.miui.build.region in
resetprop -n ro.boot.hwc in
EOF
chmod 755 "$WORK_DIR/post-fs-data.sh"

echo "==> Copying platform-signed MiuiCamera.apk and proprietary libraries..."
APK_SRC="${DIR}/proprietary/product/priv-app/MiuiCamera/MiuiCamera.apk"
SYSTEM_EXT_LIB="${DIR}/proprietary/system_ext/lib64"
PERM_SRC="${DIR}/proprietary/product/etc/permissions/privapp-permissions-com.android.camera.xml"
PUBLIC_LIB_SRC="${DIR}/proprietary/product/etc/public.libraries.txt"
DEVICE_FEATURES_DIR="${DIR}/proprietary/product/etc/device_features"

# 1. Platform-signed MiuiCamera.apk
cp -af "$APK_SRC" "$WORK_DIR/system/system_ext/priv-app/MiuiCamera/MiuiCamera.apk"

# 2. Complete JNI libraries for MiuiCamera (prevent missing library crashes)
for lib in \
  libcamera_algoup_jni.xiaomi.so \
  libcamera_mianode_jni.xiaomi.so \
  libcameraimpl.so \
  libcameramind.so \
  libcameraopt_jni.so \
  libcameraopt.so \
  libopencl-camera.so; do
  if [ -f "$SYSTEM_EXT_LIB/$lib" ]; then
    cp -af "$SYSTEM_EXT_LIB/$lib" "$WORK_DIR/system/system_ext/priv-app/MiuiCamera/lib/arm64/"
    cp -af "$SYSTEM_EXT_LIB/$lib" "$WORK_DIR/system/system_ext/lib64/"
  fi
done

# 3. Privapp permissions
cp -af "$PERM_SRC" "$WORK_DIR/system/system_ext/etc/permissions/privapp-permissions-com.android.camera.xml"

# 4. Public libraries declarations (ensures dynamic linker allows apps to load private platform/HAL libs)
if [ -f "$PUBLIC_LIB_SRC" ]; then
  cp -af "$PUBLIC_LIB_SRC" "$WORK_DIR/system/etc/public.libraries.txt"
  cp -af "$PUBLIC_LIB_SRC" "$WORK_DIR/system/system_ext/etc/public.libraries.txt"
  echo "[+] Installed public.libraries.txt to system/etc and system_ext/etc"
fi

# 5. Device features XML configs (enforces device feature flags & global watermark)
if [ -d "$DEVICE_FEATURES_DIR" ]; then
  cp -af "$DEVICE_FEATURES_DIR"/* "$WORK_DIR/system/product/etc/device_features/"
  cp -af "$DEVICE_FEATURES_DIR"/* "$WORK_DIR/system/system_ext/etc/device_features/"
  cp -af "$DEVICE_FEATURES_DIR"/* "$WORK_DIR/system/etc/device_features/"
  echo "[+] Installed device_features to product, system_ext, and system"
fi

echo "==> Creating Magisk ZIP: $OUT_ZIP..."
rm -f "$OUT_ZIP"
(cd "$WORK_DIR" && zip -r9 "$OUT_ZIP" META-INF module.prop customize.sh service.sh post-fs-data.sh system)

# Mirror to repo dir
cp -af "$OUT_ZIP" "${DIR}/HyperOS_Camera_breeze_Fix_Magisk.zip"

rm -rf "$WORK_DIR"

echo "==> Successfully built Magisk module!"
ls -lh "$OUT_ZIP"
