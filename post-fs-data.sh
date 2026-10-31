#!/system/bin/sh
MODDIR=${0%/*}

# Set Aux Camera packages early before camera provider binds
resetprop -n vendor.camera.aux.packagelist "com.android.camera,org.lineageos.aperture"
resetprop -n persist.vendor.camera.privapp.list "com.android.camera"
resetprop -n persist.sys.cam.skip_detach_image "true"
