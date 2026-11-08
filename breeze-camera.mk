#
# Copyright (C) 2024 The LineageOS Project
# Copyright (C) 2024 Wanderer's Development
# SPDX-License-Identifier: Apache-2.0
#

CAMERA_PATH := vendor/xiaomi/breeze-camera

PRODUCT_SOONG_NAMESPACES += $(CAMERA_PATH)

# Inherit Soong packages
PRODUCT_PACKAGES += \
    MiuiCamera \
    MiuiCameraOverlay \
    libcamera_algoup_jni.xiaomi \
    libcamera_mianode_jni.xiaomi \
    libcameraimpl \
    libcameramind \
    libopencl-camera \
    libcameradngimpl \
    libcameraopt \
    libcameraopt_jni \
    libhidltransport.xiaomi \
    libmicampostproc_client \
    libmodemenhance_aidl_client \
    libmqsas \
    vendor.xiaomi.hardware.campostproc@1.0-system_ext \
    com.qti.feature2.gs.netrani \
    com.xiaomi.plugin.morphohdr \
    com.xiaomi.plugin.skinbeautifier \
    com.xiaomi.plugin.mibokeh \
    com.xiaomi.plugin.superlowlight \
    com.xiaomi.plugin.swflip \
    libanc_single_bokeh \
    libanc_single_bokeh_rear \
    libanc_single_rt_bokeh

# Device Features (breeze 108MP HM6 support)
PRODUCT_COPY_FILES += \
    $(CAMERA_PATH)/proprietary/product/etc/device_features/breeze.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/device_features/breeze.xml \
    $(CAMERA_PATH)/proprietary/product/etc/device_features/breeze.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/device_features/breeze_in.xml \
    $(CAMERA_PATH)/proprietary/product/etc/device_features/breeze.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/device_features/breeze_p_in.xml \
    $(CAMERA_PATH)/proprietary/product/etc/device_features/breeze.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/device_features/breeze_in_pa.xml \
    $(CAMERA_PATH)/proprietary/product/etc/device_features/breeze.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/device_features/breeze_in_global.xml \
    $(CAMERA_PATH)/proprietary/product/etc/device_features/breeze.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/device_features/breeze.xml \
    $(CAMERA_PATH)/proprietary/product/etc/device_features/breeze.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/device_features/breeze_in.xml \
    $(CAMERA_PATH)/proprietary/product/etc/device_features/breeze.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/device_features/breeze_p_in.xml \
    $(CAMERA_PATH)/proprietary/product/etc/device_features/breeze.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/device_features/breeze_in_pa.xml \
    $(CAMERA_PATH)/proprietary/product/etc/device_features/breeze.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/device_features/breeze_in_global.xml

# Permissions & Sysconfig
PRODUCT_COPY_FILES += \
    $(CAMERA_PATH)/proprietary/product/etc/permissions/privapp-permissions-com.android.camera.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/permissions/privapp-permissions-com.android.camera.xml \
    $(CAMERA_PATH)/proprietary/product/etc/permissions/privapp-permissions-com.android.camera.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/permissions/privapp-permissions-com.android.camera.xml \
    $(CAMERA_PATH)/proprietary/system_ext/etc/permissions/com.xiaomi.hardware.camera.companion.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/permissions/com.xiaomi.hardware.camera.companion.xml \
    $(CAMERA_PATH)/proprietary/system_ext/etc/permissions/miui-cameraopt.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/permissions/miui-cameraopt.xml \
    $(CAMERA_PATH)/proprietary/system_ext/etc/permissions/miui-framework.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/permissions/miui-framework.xml \
    $(CAMERA_PATH)/proprietary/product/etc/sysconfig/miuicamera-hiddenapi-package-allowlist.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/sysconfig/miuicamera-hiddenapi-package-allowlist.xml \
    $(CAMERA_PATH)/proprietary/product/etc/sysconfig/miuicamera-hiddenapi-package-allowlist.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/sysconfig/miuicamera-hiddenapi-package-allowlist.xml \
    $(CAMERA_PATH)/proprietary/product/etc/sysconfig/miuicamera-hiddenapi-package-allowlist.xml:$(TARGET_COPY_OUT_SYSTEM)/etc/sysconfig/miuicamera-hiddenapi-package-allowlist.xml

# Framework JARs
PRODUCT_COPY_FILES += \
    $(CAMERA_PATH)/proprietary/system_ext/framework/miui-framework.jar:$(TARGET_COPY_OUT_SYSTEM_EXT)/framework/miui-framework.jar \
    $(CAMERA_PATH)/proprietary/system_ext/framework/miui-cameraopt.jar:$(TARGET_COPY_OUT_SYSTEM_EXT)/framework/miui-cameraopt.jar \
    $(CAMERA_PATH)/proprietary/system_ext/framework/com.xiaomi.hardware.camera.companion-V1.jar:$(TARGET_COPY_OUT_SYSTEM_EXT)/framework/com.xiaomi.hardware.camera.companion-V1.jar

# Linker Namespace Public Libraries
PRODUCT_COPY_FILES := $(filter-out system/core/rootdir/etc/public.libraries.android.txt:system/etc/public.libraries.txt,$(PRODUCT_COPY_FILES))
PRODUCT_COPY_FILES += \
    $(CAMERA_PATH)/proprietary/product/etc/public.libraries.txt:$(TARGET_COPY_OUT_SYSTEM)/etc/public.libraries.txt \
    $(CAMERA_PATH)/proprietary/product/etc/public.libraries.txt:$(TARGET_COPY_OUT_PRODUCT)/etc/public.libraries.txt \
    $(CAMERA_PATH)/proprietary/product/etc/public.libraries.txt:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/public.libraries.txt \
    $(CAMERA_PATH)/proprietary/product/etc/public.libraries-xiaomi.txt:$(TARGET_COPY_OUT_PRODUCT)/etc/public.libraries-xiaomi.txt \
    $(CAMERA_PATH)/proprietary/product/etc/public.libraries-xiaomi.txt:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/public.libraries-xiaomi.txt

# Media Profiles
PRODUCT_COPY_FILES += \
    $(CAMERA_PATH)/proprietary/system/etc/media_profiles.xml:$(TARGET_COPY_OUT_SYSTEM)/etc/media_profiles.xml \
    $(CAMERA_PATH)/proprietary/vendor/etc/media_profiles.xml:$(TARGET_COPY_OUT_VENDOR)/etc/media_profiles.xml \
    $(CAMERA_PATH)/proprietary/vendor/etc/media_profiles_V1_0.xml:$(TARGET_COPY_OUT_VENDOR)/etc/media_profiles_V1_0.xml

# JNI Libraries for MiuiCamera App (system_ext, matching app partition)
PRODUCT_COPY_FILES += \
    $(CAMERA_PATH)/proprietary/system_ext/lib64/libcamera_algoup_jni.xiaomi.so:$(TARGET_COPY_OUT_SYSTEM_EXT)/priv-app/MiuiCamera/lib/arm64/libcamera_algoup_jni.xiaomi.so \
    $(CAMERA_PATH)/proprietary/system_ext/lib64/libcamera_mianode_jni.xiaomi.so:$(TARGET_COPY_OUT_SYSTEM_EXT)/priv-app/MiuiCamera/lib/arm64/libcamera_mianode_jni.xiaomi.so \
    $(CAMERA_PATH)/proprietary/system_ext/lib64/libcameraimpl.so:$(TARGET_COPY_OUT_SYSTEM_EXT)/priv-app/MiuiCamera/lib/arm64/libcameraimpl.so \
    $(CAMERA_PATH)/proprietary/system_ext/lib64/libcameramind.so:$(TARGET_COPY_OUT_SYSTEM_EXT)/priv-app/MiuiCamera/lib/arm64/libcameramind.so \
    $(CAMERA_PATH)/proprietary/system_ext/lib64/libopencl-camera.so:$(TARGET_COPY_OUT_SYSTEM_EXT)/priv-app/MiuiCamera/lib/arm64/libopencl-camera.so \
    $(CAMERA_PATH)/proprietary/system_ext/lib64/libcameraopt.so:$(TARGET_COPY_OUT_SYSTEM_EXT)/priv-app/MiuiCamera/lib/arm64/libcameraopt.so \
    $(CAMERA_PATH)/proprietary/system_ext/lib64/libcameraopt_jni.so:$(TARGET_COPY_OUT_SYSTEM_EXT)/priv-app/MiuiCamera/lib/arm64/libcameraopt_jni.so

# ODM & System_ext camera tuning configs
PRODUCT_COPY_FILES += \
    $(call find-copy-subdir-files,*,$(CAMERA_PATH)/proprietary/odm/etc/camera,$(TARGET_COPY_OUT_ODM)/etc/camera) \
    $(CAMERA_PATH)/proprietary/system_ext/etc/cameracustomize.json:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/cameracustomize.json \
    $(CAMERA_PATH)/proprietary/system_ext/etc/cameraopt.json:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/cameraopt.json \
    $(CAMERA_PATH)/proprietary/system_ext/etc/cameraopt_perf.json:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/cameraopt_perf.json \
    $(CAMERA_PATH)/proprietary/system_ext/etc/cameraopt_reclaim.json:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/cameraopt_reclaim.json \
    $(CAMERA_PATH)/proprietary/system_ext/etc/cameraopt_thirdParty.json:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/cameraopt_thirdParty.json \
    $(CAMERA_PATH)/proprietary/system_ext/etc/camerascene.json:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/camerascene.json

# Vendor Properties
PRODUCT_VENDOR_PROPERTIES += \
    vendor.camera.aux.packagelist=com.android.camera,org.lineageos.aperture \
    persist.vendor.camera.privapp.list=com.android.camera \
    persist.vendor.camera.mivi.version=1 \
    vendor.camera.support.mivi=false

# System Properties
PRODUCT_SYSTEM_PROPERTIES += \
    ro.product.mod_device=breeze_in \
    ro.miui.customized.region=india \
    ro.miui.notch=1 \
    persist.sys.miui.camera.protect_prev_ext=true \
    camera.debug.mivi2=false \
    hypercamera.disable_app_default_config=true \
    ro.com.google.lens.oem_camera_package=com.android.camera

# SEPolicy — NOTE: BOARD_VENDOR_SEPOLICY_DIRS must be set in device BoardConfig.mk
# See device/xiaomi/breeze/BoardConfig.mk for the camera sepolicy dir inclusion
