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
    miui-framework \
    miui-cameraopt \
    com.xiaomi.hardware.camera.companion-V1 \
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
    com.xiaomi.plugin.morphohdr

# Device Features (breeze 108MP HM6 support)
PRODUCT_COPY_FILES += \
    $(CAMERA_PATH)/proprietary/product/etc/device_features/breeze.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/device_features/breeze.xml \
    $(CAMERA_PATH)/proprietary/product/etc/device_features/breeze.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/device_features/breeze_in.xml \
    $(CAMERA_PATH)/proprietary/product/etc/device_features/breeze.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/device_features/breeze_p_in.xml \
    $(CAMERA_PATH)/proprietary/product/etc/device_features/breeze.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/device_features/breeze_in_pa.xml \
    $(CAMERA_PATH)/proprietary/product/etc/device_features/breeze.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/device_features/breeze_in_global.xml

# Permissions
PRODUCT_COPY_FILES += \
    $(CAMERA_PATH)/proprietary/product/etc/permissions/privapp-permissions-com.android.camera.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/permissions/privapp-permissions-com.android.camera.xml \
    $(CAMERA_PATH)/proprietary/system_ext/etc/permissions/com.xiaomi.hardware.camera.companion.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/permissions/com.xiaomi.hardware.camera.companion.xml \
    $(CAMERA_PATH)/proprietary/system_ext/etc/permissions/miui-cameraopt.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/permissions/miui-cameraopt.xml

# Linker Namespace Public Libraries
PRODUCT_COPY_FILES += \
    $(CAMERA_PATH)/proprietary/product/etc/public.libraries-xiaomi.txt:$(TARGET_COPY_OUT_PRODUCT)/etc/public.libraries-xiaomi.txt \
    $(CAMERA_PATH)/proprietary/product/etc/public.libraries-xiaomi.txt:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/public.libraries-xiaomi.txt

# Media Profiles
PRODUCT_COPY_FILES += \
    $(CAMERA_PATH)/proprietary/system/etc/media_profiles.xml:$(TARGET_COPY_OUT_SYSTEM)/etc/media_profiles.xml \
    $(CAMERA_PATH)/proprietary/vendor/etc/media_profiles.xml:$(TARGET_COPY_OUT_VENDOR)/etc/media_profiles.xml \
    $(CAMERA_PATH)/proprietary/vendor/etc/media_profiles_V1_0.xml:$(TARGET_COPY_OUT_VENDOR)/etc/media_profiles_V1_0.xml

# JNI Libraries for MiuiCamera App
PRODUCT_COPY_FILES += \
    $(CAMERA_PATH)/proprietary/system_ext/lib64/libcamera_algoup_jni.xiaomi.so:$(TARGET_COPY_OUT_PRODUCT)/priv-app/MiuiCamera/lib/arm64/libcamera_algoup_jni.xiaomi.so \
    $(CAMERA_PATH)/proprietary/system_ext/lib64/libcamera_mianode_jni.xiaomi.so:$(TARGET_COPY_OUT_PRODUCT)/priv-app/MiuiCamera/lib/arm64/libcamera_mianode_jni.xiaomi.so \
    $(CAMERA_PATH)/proprietary/system_ext/lib64/libcameraimpl.so:$(TARGET_COPY_OUT_PRODUCT)/priv-app/MiuiCamera/lib/arm64/libcameraimpl.so \
    $(CAMERA_PATH)/proprietary/system_ext/lib64/libcameramind.so:$(TARGET_COPY_OUT_PRODUCT)/priv-app/MiuiCamera/lib/arm64/libcameramind.so \
    $(CAMERA_PATH)/proprietary/system_ext/lib64/libopencl-camera.so:$(TARGET_COPY_OUT_PRODUCT)/priv-app/MiuiCamera/lib/arm64/libopencl-camera.so

# ODM & System_ext camera tuning configs
PRODUCT_COPY_FILES += \
    $(call find-copy-subdir-files,*,$(CAMERA_PATH)/proprietary/odm/etc/camera,$(TARGET_COPY_OUT_ODM)/etc/camera) \
    $(CAMERA_PATH)/proprietary/system_ext/etc/cameracustomize.json:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/cameracustomize.json \
    $(CAMERA_PATH)/proprietary/system_ext/etc/cameraopt.json:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/cameraopt.json \
    $(CAMERA_PATH)/proprietary/system_ext/etc/cameraopt_perf.json:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/cameraopt_perf.json \
    $(CAMERA_PATH)/proprietary/system_ext/etc/cameraopt_reclaim.json:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/cameraopt_reclaim.json \
    $(CAMERA_PATH)/proprietary/system_ext/etc/cameraopt_thirdParty.json:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/cameraopt_thirdParty.json \
    $(CAMERA_PATH)/proprietary/system_ext/etc/camerascene.json:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/camerascene.json

# Properties
PRODUCT_SYSTEM_PROPERTIES += \
    vendor.camera.aux.packagelist=com.android.camera,org.lineageos.aperture \
    persist.vendor.camera.privapp.list=com.android.camera \
    ro.product.mod_device=breeze_in \
    ro.miui.customized.region=india \
    ro.miui.notch=1 \
    persist.sys.miui.camera.protect_prev_ext=true \
    camera.debug.mivi2=false \
    persist.vendor.camera.mivi.version=1 \
    vendor.camera.support.mivi=false \
    hypercamera.disable_app_default_config=true \
    ro.com.google.lens.oem_camera_package=com.android.camera

# SEPolicy
BOARD_VENDOR_SEPOLICY_DIRS += $(CAMERA_PATH)/sepolicy/vendor
SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS += $(CAMERA_PATH)/sepolicy/private
