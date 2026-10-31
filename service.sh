#!/system/bin/sh
MODDIR=${0%/*}

# Wait for boot completion
while [ "$(getprop sys.boot_completed)" != "1" ]; do
    sleep 2
done

# Enable Aux Camera access for MiuiCamera
resetprop vendor.camera.aux.packagelist "com.android.camera,org.lineageos.aperture"
resetprop persist.vendor.camera.privapp.list "com.android.camera"
resetprop ro.com.google.lens.oem_camera_package "com.android.camera"
resetprop persist.sys.cam.skip_detach_image "true"
resetprop ro.miui.notch "1"
resetprop ro.miui.customized.region "india"
resetprop ro.product.mod_device "breeze_in"
