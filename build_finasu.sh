#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${DIR}/finasu_build"
OUT_ZIP="${DIR}/HyperOS_Camera_breeze_FinaSU.zip"

echo "==> Preparing FinaSU / KernelSU build environment..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/META-INF/com/google/android"
mkdir -p "$BUILD_DIR/system/product/priv-app/MiuiCamera/lib/arm64"
mkdir -p "$BUILD_DIR/system/product/lib64"
mkdir -p "$BUILD_DIR/system/product/etc/device_features"
mkdir -p "$BUILD_DIR/system/product/etc/permissions"
mkdir -p "$BUILD_DIR/system/etc"
mkdir -p "$BUILD_DIR/system/vendor/lib64"
mkdir -p "$BUILD_DIR/system/vendor/etc"
mkdir -p "$BUILD_DIR/system/system_ext/framework"
mkdir -p "$BUILD_DIR/system/system_ext/lib64"
mkdir -p "$BUILD_DIR/system/system_ext/etc/permissions"
mkdir -p "$BUILD_DIR/system/odm/etc/camera"

echo "==> Creating module metadata..."
cat << 'EOF' > "$BUILD_DIR/module.prop"
id=hyperos_camera_breeze
name=HyperOS Camera (breeze)
version=v1.3
versionCode=130
author=Wanderer-s-Development
description=Stock Xiaomi HyperOS Camera (108MP) with native algorithms, camcorder media profiles, and device features for Redmi 13 5G / POCO M6 Plus 5G (breeze). Built for FinaSU / KernelSU / APatch / Magisk.
EOF

cat << 'EOF' > "$BUILD_DIR/META-INF/com/google/android/updater-script"
#MAGISK
EOF

cat << 'EOF' > "$BUILD_DIR/META-INF/com/google/android/update-binary"
#!/sbin/sh
#################
# Magisk / KernelSU / FinaSU Module Installer Script
#################
OUTFD=$2
ZIPFILE=$3

mount /data 2>/dev/null

if [ -f /data/adb/magisk/util_functions.sh ]; then
  . /data/adb/magisk/util_functions.sh
elif [ -f /data/adb/ksu/util_functions.sh ]; then
  . /data/adb/ksu/util_functions.sh
elif [ -f /data/adb/ap/util_functions.sh ]; then
  . /data/adb/ap/util_functions.sh
fi

install_module
exit 0
EOF
chmod 755 "$BUILD_DIR/META-INF/com/google/android/update-binary"

cat << 'EOF' > "$BUILD_DIR/customize.sh"
ui_print "****************************************"
ui_print "*   HyperOS Camera for breeze (SM4450) *"
ui_print "* Redmi 13 5G / POCO M6 Plus 5G (108MP) *"
ui_print "*        FinaSU / KernelSU Edition     *"
ui_print "****************************************"

if [ "$ARCH" != "arm64" ]; then
  abort "! Unsupported architecture: $ARCH (requires arm64)"
fi

ui_print "- Disabling KernelSU mount isolation for apps..."
if [ -x /data/adb/ksud ]; then
  /data/adb/ksud feature set 1 0 2>/dev/null || true
  /data/adb/ksud feature save 2>/dev/null || true
fi

ui_print "- Linking partition overlays..."
ln -sfn ./system/product "$MODPATH/product" 2>/dev/null || true
ln -sfn ./system/system_ext "$MODPATH/system_ext" 2>/dev/null || true
ln -sfn ./system/vendor "$MODPATH/vendor" 2>/dev/null || true
ln -sfn ./system/odm "$MODPATH/odm" 2>/dev/null || true

ui_print "- Setting file permissions..."
set_perm_recursive "$MODPATH/system" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/product/priv-app/MiuiCamera" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/product/priv-app/MiuiCamera/lib" 0 0 0755 0755
set_perm_recursive "$MODPATH/system/product/priv-app/MiuiCamera/lib/arm64" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/product/lib64" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/system_ext/lib64" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/system_ext/framework" 0 0 0755 0644
[ -d "$MODPATH/system/vendor/lib64" ] && set_perm_recursive "$MODPATH/system/vendor/lib64" 0 0 0755 0644
[ -d "$MODPATH/system/vendor/etc" ] && set_perm_recursive "$MODPATH/system/vendor/etc" 0 0 0755 0644
[ -d "$MODPATH/system/etc" ] && set_perm_recursive "$MODPATH/system/etc" 0 0 0755 0644
[ -f "$MODPATH/sepolicy.rule" ] && set_perm "$MODPATH/sepolicy.rule" 0 0 0644

ui_print "- HyperOS Camera module installed successfully!"
ui_print "- Reboot your device to activate."
EOF

cat << 'EOF' > "$BUILD_DIR/service.sh"
#!/system/bin/sh
MODDIR=${0%/*}

while [ "$(getprop sys.boot_completed)" != "1" ]; do
  sleep 1
done

# Cleanup any stale buffer starving properties
resetprop -p --delete persist.sys.cam.skip_detach_image 2>/dev/null || true

# Camera & Device configuration
resetprop -n vendor.camera.aux.packagelist "com.android.camera,org.lineageos.aperture"
resetprop -n persist.vendor.camera.privapp.list "com.android.camera"
resetprop -n ro.product.mod_device "breeze_in_global"
resetprop -n ro.miui.customized.region "india"
resetprop -n ro.miui.notch "1"
resetprop -n persist.sys.miui.camera.protect_prev_ext "true"
resetprop -n vendor.camera.support.mivi "false"
resetprop -n camera.debug.mivi2 "false"
resetprop -n persist.vendor.camera.mivi.version "1"
resetprop -n hypercamera.disable_app_default_config "true"
resetprop -n ro.com.google.lens.oem_camera_package "com.android.camera"
EOF
chmod 755 "$BUILD_DIR/service.sh"

cat << 'EOF' > "$BUILD_DIR/post-fs-data.sh"
#!/system/bin/sh
MODDIR=${0%/*}

# Early property overrides to disable MIVI2 offline queue
resetprop -n camera.debug.mivi2 "false"
resetprop -n persist.vendor.camera.mivi.version "1"
resetprop -n vendor.camera.support.mivi "false"

# Disable KernelSU mount namespace isolation
if [ -x /data/adb/ksud ]; then
  /data/adb/ksud feature set 1 0 2>/dev/null || true
fi

# Ensure correct app permissions
chmod 755 "$MODDIR"/system/product/priv-app/MiuiCamera 2>/dev/null || true
chmod 644 "$MODDIR"/system/product/priv-app/MiuiCamera/* 2>/dev/null || true
chmod 755 "$MODDIR"/system/product/priv-app/MiuiCamera/lib 2>/dev/null || true
chmod 755 "$MODDIR"/system/product/priv-app/MiuiCamera/lib/arm64 2>/dev/null || true
chmod 644 "$MODDIR"/system/product/priv-app/MiuiCamera/lib/arm64/* 2>/dev/null || true
EOF
chmod 755 "$BUILD_DIR/post-fs-data.sh"

# Copy sepolicy.rule
cp -af "${DIR}/sepolicy.rule" "$BUILD_DIR/sepolicy.rule"

echo "==> Populating proprietary blobs into module overlay..."
SRC="${DIR}/proprietary"

# 1. Camera APK
cp -af "$SRC/product/priv-app/MiuiCamera/MiuiCamera.apk" "$BUILD_DIR/system/product/priv-app/MiuiCamera/"

# 2. Native JNI & Algorithm Libraries
for so in "$SRC/system_ext/lib64/"*.so; do
  cp -af "$so" "$BUILD_DIR/system/product/priv-app/MiuiCamera/lib/arm64/"
  cp -af "$so" "$BUILD_DIR/system/product/lib64/"
  cp -af "$so" "$BUILD_DIR/system/system_ext/lib64/"
done

# 3. Framework JARs
for jar in "$SRC/system_ext/framework/"*.jar; do
  cp -af "$jar" "$BUILD_DIR/system/system_ext/framework/"
done

# 4. Device Features
for xml in "$SRC/product/etc/device_features/"*.xml; do
  cp -af "$xml" "$BUILD_DIR/system/product/etc/device_features/"
done

# 5. Permissions
cp -af "$SRC/product/etc/permissions/"* "$BUILD_DIR/system/product/etc/permissions/"
cp -af "$SRC/system_ext/etc/permissions/"* "$BUILD_DIR/system/system_ext/etc/permissions/"

# 6. Tuning JSONs
cp -af "$SRC/odm/etc/camera/"*.json "$BUILD_DIR/system/odm/etc/camera/"
cp -af "$SRC/system_ext/etc/"*.json "$BUILD_DIR/system/system_ext/etc/"

# 7. Media Profiles & Linker config
if [ -d "$SRC/system/etc" ]; then
  cp -af "$SRC/system/etc/"* "$BUILD_DIR/system/etc/"
fi
if [ -d "$SRC/vendor/etc" ]; then
  cp -af "$SRC/vendor/etc/"* "$BUILD_DIR/system/vendor/etc/"
fi

if [ -f "$SRC/product/etc/public.libraries.txt" ]; then
  cp -af "$SRC/product/etc/public.libraries.txt" "$BUILD_DIR/system/product/etc/public.libraries.txt"
  cp -af "$SRC/product/etc/public.libraries.txt" "$BUILD_DIR/system/etc/public.libraries.txt"
fi

# 8. Vendor HAL fixes
if [ -d "$SRC/vendor/lib64" ]; then
  mkdir -p "$BUILD_DIR/system/vendor/lib64"
  cp -af "$SRC/vendor/lib64/"* "$BUILD_DIR/system/vendor/lib64/"
fi

# 9. Create Root Partition Overlay Symlinks for KernelSU / FinaSU
(cd "$BUILD_DIR" && ln -sfn ./system/product product)
(cd "$BUILD_DIR" && ln -sfn ./system/system_ext system_ext)
(cd "$BUILD_DIR" && ln -sfn ./system/vendor vendor)
(cd "$BUILD_DIR" && ln -sfn ./system/odm odm)

echo "==> Packaging FinaSU ZIP module..."
rm -f "$OUT_ZIP"
(cd "$BUILD_DIR" && zip -r9y "$OUT_ZIP" META-INF module.prop customize.sh service.sh post-fs-data.sh sepolicy.rule system product system_ext vendor odm)

rm -rf "$BUILD_DIR"
cp -f "$OUT_ZIP" /home/wtf/Downloads/HyperOS_Camera_breeze_FinaSU.zip

echo "==> Successfully created:"
echo "    $OUT_ZIP"
echo "    /home/wtf/Downloads/HyperOS_Camera_breeze_FinaSU.zip"
