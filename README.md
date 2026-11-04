# HyperOS Stock Camera for Redmi 13 5G / POCO M6 Plus 5G (`breeze`)

Native AOSP / Soong camera tree for **Redmi 13 5G / POCO M6 Plus 5G** (codename: `breeze` / `breeze_in`, Qualcomm Snapdragon 4 Gen 2 - SM4450):
- **Soong Build System Integration (`Android.bp` & `breeze-camera.mk`)**: Compile directly into AOSP custom ROMs (Project Infinity-X, LineageOS, PixelOS, EvolutionX, etc.).

Extracted directly from official stock HyperOS India firmware (`OS3.0.303.0.WNUINXM`).

---

## Features

- **108 MP Ultra-HD Mode** (Samsung ISOCELL HM6 sensor fully enabled via `device_features/breeze.xml`).
- **Full Auxiliary Lens Switching** (Main + Macro + Front).
- **Portrait & Night Modes** with native Xiaomi AI algorithms (`libcamera_algoup`, `libcamera_mianode`, `libopencl-camera`).
- **SELinux Policies Included** (Full Enforcing compatibility: `priv_app` binder & fd access to camera provider and postproc services).
- **Vendor Partition Isolation** (Qualcomm & Xiaomi HAL libs strictly located in vendor space).
- **MIVI 2.0 Capture Optimization** (Bypasses hung MIUI system services for instant capture).
- **ODM Optimizations** (`camerabooster.json`, `cameraopt.json`).

---

## Soong Build Integration (Custom ROM Compilers)

To include this camera natively in your custom ROM builds:

### Step 1: Clone into your ROM tree
In your ROM root directory:
```bash
git clone https://github.com/Wanderer-s-Development/hyperos_camera_breeze.git vendor/xiaomi/breeze-camera
```

### Step 2: Inherit from `device.mk`
Add the following line to `device/xiaomi/breeze/device.mk` (or `lineage_breeze.mk`):
```makefile
# HyperOS Stock Camera
$(call inherit-product-if-exists, vendor/xiaomi/breeze-camera/breeze-camera.mk)
```

### Step 3: Compile
Run your standard ROM build command:
```bash
mka bacon
# or
mka infinity
```
Soong will automatically:
- Import `MiuiCamera.apk` as a privileged app (`android_app_import`).
- Import `miui-framework.jar`, `miui-cameraopt.jar`, and `com.xiaomi.hardware.camera.companion-V1.jar`.
- Link Xiaomi camera JNI & post-processing libraries (`libcamera_algoup_jni.xiaomi.so`, `libcamera_mianode_jni.xiaomi.so`, `libmicampostproc_client.so`, etc.).
- Copy `breeze.xml` device features to `/product/etc/device_features/`.
- Apply camera SEPolicy rules from `sepolicy/`.

---

## Repository Structure

```
.
├── Android.bp                       # Soong blueprint (android_app_import, java_import, cc_prebuilt)
├── breeze-camera.mk                 # Product makefile to inherit in device.mk
├── sepolicy/                        # SELinux policies for ROM compilation
│   ├── vendor/
│   │   ├── camera.te
│   │   ├── hal_camera_default.te
│   │   └── hwservice.te
│   └── private/
│       └── priv_app.te
└── proprietary/                     # Raw proprietary files used by Soong build system
    ├── odm/etc/camera/              # Stock ODM booster JSONs
    ├── product/etc/device_features/ # Hardware sensor features (breeze.xml, breeze_in.xml, etc.)
    ├── product/etc/permissions/     # Privapp permissions
    ├── product/priv-app/MiuiCamera/ # Stock 64-bit MiuiCamera.apk & private JNI libs
    ├── system/etc/                  # System media profiles
    ├── system_ext/                  # Framework jars & algo libraries
    └── vendor/                      # CamX Chi netrani & morphohdr vendor plugins and media profiles
```

---

## Credits
- Xiaomi for official HyperOS firmware
- [Wanderer's Development](https://github.com/Wanderer-s-Development)
