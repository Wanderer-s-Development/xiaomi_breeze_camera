#!/usr/bin/env bash
#
# Build script for HyperOS Camera Magisk / KernelSU / APatch Module
# Redmi 13 5G / POCO M6 Plus 5G (codename: breeze / breeze_in)
#

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${DIR}/out_magisk"
OUT_ZIP="${DIR}/HyperOS_Camera_breeze_Magisk.zip"

echo "==> Preparing Magisk module build workspace..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/META-INF/com/google/android"
mkdir -p "$BUILD_DIR/system/priv-app/MiuiCamera/lib/arm64"
mkdir -p "$BUILD_DIR/system/product/priv-app/MiuiCamera/lib/arm64"
mkdir -p "$BUILD_DIR/system/lib64"
mkdir -p "$BUILD_DIR/system/product/lib64"
mkdir -p "$BUILD_DIR/system/system_ext/lib64"
mkdir -p "$BUILD_DIR/system/framework"
mkdir -p "$BUILD_DIR/system/system_ext/framework"
mkdir -p "$BUILD_DIR/system/etc/device_features"
mkdir -p "$BUILD_DIR/system/product/etc/device_features"
mkdir -p "$BUILD_DIR/system/etc/permissions"
mkdir -p "$BUILD_DIR/system/product/etc/permissions"
mkdir -p "$BUILD_DIR/system/system_ext/etc/permissions"
mkdir -p "$BUILD_DIR/system/etc/camera"
mkdir -p "$BUILD_DIR/system/odm/etc/camera"
mkdir -p "$BUILD_DIR/system/system_ext/etc"

echo "==> Creating module.prop..."
cat << 'EOF' > "$BUILD_DIR/module.prop"
id=hyperos_camera_breeze
name=HyperOS Camera (Redmi 13 5G / POCO M6 Plus 5G)
version=v1.0
versionCode=100
author=Wanderer's Development
description=Stock Xiaomi HyperOS Camera (MiuiCamera) port for breeze/breeze_in on AOSP ROMs with 108MP HM6 support and linker namespace integration.
EOF

echo "==> Creating META-INF updater scripts..."
cat << 'EOF' > "$BUILD_DIR/META-INF/com/google/android/updater-script"
#MAGISK
EOF

cat << 'EOF' > "$BUILD_DIR/META-INF/com/google/android/update-binary"
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
chmod 755 "$BUILD_DIR/META-INF/com/google/android/update-binary"

echo "==> Creating customize.sh..."
cat << 'EOF' > "$BUILD_DIR/customize.sh"
ui_print "****************************************"
ui_print "* HyperOS Camera for Redmi 13 5G       *"
ui_print "* Codename: breeze / breeze_in         *"
ui_print "* Wanderer's Development               *"
ui_print "****************************************"

DEVICE=$(getprop ro.product.device)
MODEL=$(getprop ro.product.model)
ui_print "- Detected device: $DEVICE ($MODEL)"

ui_print "- Configuring dynamic linker public libraries..."

patch_public_libraries() {
  local target="$1"
  local mod_target="$MODPATH$target"
  
  if [ -f "$target" ]; then
    mkdir -p "$(dirname "$mod_target")"
    cp -af "$target" "$mod_target"
    
    for lib in \
      libbinder.so \
      libcamera_client.so \
      libcamera_metadata.so \
      libcutils.so \
      libgui.so \
      libutils.so \
      libvndksupport.so \
      libandroid_runtime.so \
      libbase.so \
      libmedia_jni_utils.so \
      libui.so \
      android.hidl.token@1.0-utils.so \
      libc++.so \
      libcrypto.so \
      libxml2.so \
      libopencl-camera.so \
      libcamera_algoup_jni.xiaomi.so \
      libcamera_mianode_jni.xiaomi.so \
      libcameraimpl.so \
      libcameramind.so; do
      if ! grep -q "^$lib" "$mod_target"; then
        echo "$lib" >> "$mod_target"
      fi
    done
    set_perm 0 0 0644 "$mod_target"
    ui_print "  - Patched $target"
  fi
}

patch_public_libraries "/system/etc/public.libraries.txt"
patch_public_libraries "/product/etc/public.libraries.txt"
patch_public_libraries "/system_ext/etc/public.libraries.txt"

ui_print "- Setting permissions..."
set_perm_recursive "$MODPATH/system" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/priv-app/MiuiCamera" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/priv-app/MiuiCamera/lib" 0 0 0755 0755
set_perm_recursive "$MODPATH/system/priv-app/MiuiCamera/lib/arm64" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/lib64" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/product/priv-app/MiuiCamera" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/product/priv-app/MiuiCamera/lib" 0 0 0755 0755
set_perm_recursive "$MODPATH/system/product/priv-app/MiuiCamera/lib/arm64" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/product/lib64" 0 0 0755 0644

ui_print "- HyperOS Camera module installed successfully!"
ui_print "- Please reboot to activate."
EOF

echo "==> Creating service.sh..."
cat << 'EOF' > "$BUILD_DIR/service.sh"
#!/system/bin/sh
MODDIR=${0%/*}

# Wait for boot completion
while [ "$(getprop sys.boot_completed)" != "1" ]; do
  sleep 1
done

# Xiaomi Camera System Properties
resetprop -n vendor.camera.aux.packagelist "com.android.camera,org.lineageos.aperture"
resetprop -n persist.vendor.camera.privapp.list "com.android.camera"
resetprop -n ro.product.mod_device "breeze_in"
resetprop -n ro.miui.customized.region "india"
resetprop -n ro.miui.notch "1"
resetprop -n persist.sys.cam.skip_detach_image "true"
resetprop -n ro.com.google.lens.oem_camera_package "com.android.camera"
EOF
chmod 755 "$BUILD_DIR/service.sh"

echo "==> Creating post-fs-data.sh..."
cat << 'EOF' > "$BUILD_DIR/post-fs-data.sh"
#!/system/bin/sh
MODDIR=${0%/*}

# Ensure permissions at early boot
chmod 755 "$MODDIR"/system/priv-app/MiuiCamera 2>/dev/null || true
chmod 644 "$MODDIR"/system/priv-app/MiuiCamera/* 2>/dev/null || true
chmod 755 "$MODDIR"/system/priv-app/MiuiCamera/lib 2>/dev/null || true
chmod 755 "$MODDIR"/system/priv-app/MiuiCamera/lib/arm64 2>/dev/null || true
chmod 644 "$MODDIR"/system/priv-app/MiuiCamera/lib/arm64/* 2>/dev/null || true
EOF
chmod 755 "$BUILD_DIR/post-fs-data.sh"

echo "==> Populating proprietary components..."
SRC="${DIR}/proprietary"

# 1. Camera APK
cp -af "$SRC/product/priv-app/MiuiCamera/MiuiCamera.apk" "$BUILD_DIR/system/priv-app/MiuiCamera/"
cp -af "$SRC/product/priv-app/MiuiCamera/MiuiCamera.apk" "$BUILD_DIR/system/product/priv-app/MiuiCamera/"

# 2. Native JNI Libraries
for so in "$SRC/system_ext/lib64/"*.so; do
  cp -af "$so" "$BUILD_DIR/system/priv-app/MiuiCamera/lib/arm64/"
  cp -af "$so" "$BUILD_DIR/system/product/priv-app/MiuiCamera/lib/arm64/"
  cp -af "$so" "$BUILD_DIR/system/lib64/"
  cp -af "$so" "$BUILD_DIR/system/product/lib64/"
  cp -af "$so" "$BUILD_DIR/system/system_ext/lib64/"
done

# 3. Framework JARs
for jar in "$SRC/system_ext/framework/"*.jar; do
  cp -af "$jar" "$BUILD_DIR/system/framework/"
  cp -af "$jar" "$BUILD_DIR/system/system_ext/framework/"
done

# 4. Device Features (breeze.xml)
for xml in "$SRC/product/etc/device_features/"*.xml; do
  cp -af "$xml" "$BUILD_DIR/system/etc/device_features/"
  cp -af "$xml" "$BUILD_DIR/system/product/etc/device_features/"
done

# 5. Permissions
cp -af "$SRC/product/etc/permissions/"* "$BUILD_DIR/system/etc/permissions/"
cp -af "$SRC/product/etc/permissions/"* "$BUILD_DIR/system/product/etc/permissions/"
cp -af "$SRC/system_ext/etc/permissions/"* "$BUILD_DIR/system/etc/permissions/"
cp -af "$SRC/system_ext/etc/permissions/"* "$BUILD_DIR/system/system_ext/etc/permissions/"

# 6. ODM & System_ext Tuning configs
cp -af "$SRC/odm/etc/camera/"*.json "$BUILD_DIR/system/etc/camera/"
cp -af "$SRC/odm/etc/camera/"*.json "$BUILD_DIR/system/odm/etc/camera/"
cp -af "$SRC/system_ext/etc/"*.json "$BUILD_DIR/system/etc/"
cp -af "$SRC/system_ext/etc/"*.json "$BUILD_DIR/system/system_ext/etc/"

echo "==> Packaging Magisk module ZIP..."
rm -f "$OUT_ZIP"
(cd "$BUILD_DIR" && zip -r9 "$OUT_ZIP" META-INF module.prop customize.sh service.sh post-fs-data.sh system)

rm -rf "$BUILD_DIR"
echo "==> Magisk module successfully generated at:"
echo "    $OUT_ZIP"
