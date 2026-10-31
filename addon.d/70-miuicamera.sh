#!/sbin/sh
#
# ADDOND_VERSION=3
# /system/addon.d/70-miuicamera.sh
#

. /tmp/backuptool.functions

list_files() {
cat << 'LIST_EOF'
product/priv-app/MiuiCamera/MiuiCamera.apk
product/etc/device_features/breeze.xml
product/etc/device_features/breeze_in.xml
product/etc/device_features/breeze_p_in.xml
product/etc/permissions/privapp-permissions-com.android.camera.xml
system_ext/framework/miui-framework.jar
system_ext/framework/miui-cameraopt.jar
system_ext/framework/com.xiaomi.hardware.camera.companion-V1.jar
system_ext/lib64/libcamera_algoup_jni.xiaomi.so
system_ext/lib64/libcamera_mianode_jni.xiaomi.so
system_ext/lib64/libcameraimpl.so
system_ext/lib64/libcameramind.so
system_ext/lib64/libopencl-camera.so
system_ext/etc/permissions/com.xiaomi.hardware.camera.companion.xml
system_ext/etc/permissions/miui-cameraopt.xml
system_ext/etc/cameracustomize.json
system_ext/etc/cameraopt.json
system_ext/etc/cameraopt_perf.json
system_ext/etc/cameraopt_reclaim.json
system_ext/etc/cameraopt_thirdParty.json
system_ext/etc/camerascene.json
odm/etc/camera/camerabooster.json
odm/etc/camera/cameracustomize.json
odm/etc/camera/cameraopt.json
odm/etc/camera/cameraopt_perf.json
odm/etc/camera/cameraopt_reclaim.json
addon.d/70-miuicamera.sh
LIST_EOF
}

case "$1" in
  backup)
    list_files | while read FILE DUMMY; do
      backup_file "$S/$FILE"
    done
  ;;
  restore)
    list_files | while read FILE REPLACEMENT; do
      R=""
      [ -n "$REPLACEMENT" ] && R="$S/$REPLACEMENT"
      [ -f "$C/$S/$FILE" ] && restore_file "$S/$FILE" "$R"
    done
  ;;
  pre-backup|post-backup|pre-restore)
    # Stub
  ;;
  post-restore)
    for i in $(list_files); do
      if type get_output_path >/dev/null 2>&1; then
        f=$(get_output_path "$S/$i")
      else
        f="$S/$i"
      fi
      [ -f "$f" ] || continue
      chown root:root "$f" 2>/dev/null || true
      chmod 644 "$f" 2>/dev/null || true
      chmod 755 "$(dirname "$f")" 2>/dev/null || true
      chcon -h u:object_r:system_file:s0 "$f" 2>/dev/null || true
    done
    if type get_output_path >/dev/null 2>&1; then
      f=$(get_output_path "$S/addon.d/70-miuicamera.sh")
    else
      f="$S/addon.d/70-miuicamera.sh"
    fi
    chmod 755 "$f" 2>/dev/null || true
  ;;
esac
