# HyperOS Stock Camera for Redmi 13 5G / POCO M6 Plus 5G (`breeze`)

Dual-purpose camera repository for **Redmi 13 5G / POCO M6 Plus 5G** (codename: `breeze` / `breeze_in`, Qualcomm Snapdragon 4 Gen 2 - SM4450):
1. **Soong Build System Integration (`Android.bp`)**: Compile directly into AOSP custom ROMs (Project Infinity-X, LineageOS, etc.).
2. **AOSP Recovery Flashable Package**: Sideloadable via AOSP / Lineage / Project Infinity-X / TWRP Recovery with OTA survival (`addon.d`).

Extracted directly from official stock HyperOS India firmware (`OS3.0.303.0.WNUINXM`).

---

## Features

- **108 MP Ultra-HD Mode** (Samsung ISOCELL HM6 sensor fully enabled via `device_features/breeze.xml`).
- **Full Auxiliary Lens Switching** (Main + Macro + Front).
- **Portrait & Night Modes** with native Xiaomi AI algorithms (`libcamera_algoup`, `libcamera_mianode`, `libopencl-camera`).
- **Leica / HyperOS Watermarks & Filters**.
- **ODM Optimizations** (`camerabooster.json`, `cameraopt.json`).
- **Dynamic AUX Whitelisting** (`vendor.camera.aux.packagelist` & `persist.vendor.camera.privapp.list` set automatically on boot).
- **SELinux Policies Included** (Allows `priv_app` access to camera provider and postproc services).

---

## 1. Soong Build Integration (Custom ROM Compilers)

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
- Link Xiaomi camera JNI libraries (`libcamera_algoup_jni.xiaomi.so`, `libcamera_mianode_jni.xiaomi.so`, etc.).
- Copy `breeze.xml` device features to `/product/etc/device_features/breeze.xml`.
- Apply camera SEPolicy rules from `sepolicy/`.

---

## 2. AOSP Recovery Flashable Package

If you want a standalone flashable package without rebuilding the ROM:

### Package Generation
Run the build script in this repo:
```bash
./package.sh
```
This generates `HyperOS_Camera_breeze_Recovery_Flashable.zip`.

### Flashing via AOSP Recovery (or Lineage / Infinity-X / TWRP / OrangeFox)
1. Reboot your device into Recovery mode.
2. Select **Apply update** -> **Apply from ADB** (or install directly in TWRP/OrangeFox).
3. From your computer, run:
```bash
adb sideload HyperOS_Camera_breeze_Recovery_Flashable.zip
```
4. Reboot system.

### OTA Survival (addon.d v3)
The installer deploys `addon.d/70-miuicamera.sh` into `/system/addon.d/`. This ensures all camera components, proprietary libraries, and configuration files automatically survive future AOSP / LineageOS / Project Infinity-X OTA ROM updates without needing to reflash.

---

## Repository Structure

```
.
├── addon.d/                         # OTA backup/restore script
│   └── 70-miuicamera.sh             # Addon.d v3 OTA survival script
├── Android.bp                       # Soong blueprint (android_app_import, java_import, cc_prebuilt)
├── breeze-camera.mk                 # Product makefile to inherit in device.mk
├── package.sh                       # Packaging script for AOSP Recovery Flashable ZIP
├── toybox-arm64                     # Static POSIX binary bundled for AOSP recovery shell
├── sepolicy/                        # SELinux policies for ROM compilation
│   ├── vendor/camera.te
│   └── private/priv_app.te
├── META-INF/com/google/android/     # AOSP recovery installer
│   ├── update-binary                # Dynamic partition mapper & installer script
│   └── updater-script               # Binary launcher stub
└── proprietary/                     # Raw proprietary files used by both Soong and Recovery
    ├── odm/etc/camera/              # Stock ODM booster JSONs
    ├── product/etc/device_features/ # Hardware sensor features (breeze.xml)
    ├── product/etc/permissions/     # Privapp permissions
    ├── product/priv-app/MiuiCamera/ # Stock 64-bit MiuiCamera.apk
    └── system_ext/                  # Framework jars & algo libraries
```

---

## Credits
- Xiaomi for official HyperOS firmware
- [Wanderer's Development](https://github.com/Wanderer-s-Development)
