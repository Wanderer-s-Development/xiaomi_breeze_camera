# HyperOS Stock Camera for Redmi 13 5G / POCO M6 Plus 5G (`breeze`)

Stock Xiaomi HyperOS Camera port and Recovery Flashable / Magisk package for **Redmi 13 5G / POCO M6 Plus 5G** (codename: `breeze` / `breeze_in`), powered by Qualcomm Snapdragon 4 Gen 2 (SM4450).

Extracted directly from official stock HyperOS India firmware (`OS3.0.303.0.WNUINXM`).

---

## Features

- **108 MP Ultra-HD Mode** (Samsung ISOCELL HM6 sensor fully enabled via `device_features/breeze.xml`).
- **Full Auxiliary Lens Switching** (Main + Macro + Front).
- **Portrait & Night Modes** with native Xiaomi AI algorithms (`libcamera_algoup`, `libcamera_mianode`, `libopencl-camera`).
- **Leica / HyperOS Watermarks & Filters**.
- **ODM Optimizations** (`camerabooster.json`, `cameraopt.json`).
- **Dynamic AUX Whitelisting** (`vendor.camera.aux.packagelist` & `persist.vendor.camera.privapp.list` set automatically on boot via `service.sh` and `post-fs-data.sh`).
- **SELinux Rules Included** (`sepolicy.rule` prevents `priv_app` denials).
- **Universal Flashable Installer** (Works in OrangeFox Recovery, TWRP, Magisk, KernelSU, and APatch).

---

## Directory Structure

```
.
├── META-INF/com/google/android/
│   ├── update-binary                # Universal Recovery & Magisk installer
│   └── updater-script               # Android recovery updater script
├── customize.sh                     # Installation permission script
├── module.prop                      # Module metadata
├── post-fs-data.sh                  # Early-boot camera provider properties
├── service.sh                       # Boot-completed property initialization
├── sepolicy.rule                    # SELinux permissions for camera services
└── system/
    ├── odm/etc/camera/              # Stock ODM camera booster JSONs
    ├── product/
    │   ├── etc/device_features/     # Hardware sensor features (breeze.xml)
    │   ├── etc/permissions/         # Camera privapp permissions
    │   └── priv-app/MiuiCamera/     # Stock 64-bit MiuiCamera.apk
    └── system_ext/
        ├── etc/                     # Camera scene & optimizer configurations
        ├── framework/               # Framework dependencies (miui-framework, etc.)
        └── lib64/                   # Proprietary Xiaomi camera algo libraries
```

---

## Installation

### Method 1: Recovery (OrangeFox / TWRP)
1. Download the flashable ZIP or zip this directory:
   ```bash
   zip -r9 HyperOS_Camera_breeze_Recovery_Flashable.zip .
   ```
2. Reboot into **OrangeFox Recovery** or **TWRP**.
3. Flash `HyperOS_Camera_breeze_Recovery_Flashable.zip`.
4. Reboot system.

### Method 2: Magisk / KernelSU / APatch
1. Open the Magisk / KernelSU / APatch Manager app.
2. Go to **Modules** $\rightarrow$ **Install from storage**.
3. Select the zip package and reboot.

---

## Credits
- Xiaomi for official HyperOS firmware
- [Wanderer's Development](https://github.com/Wanderer-s-Development)
