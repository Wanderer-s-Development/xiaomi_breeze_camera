# HyperOS Camera (breeze) - Deep Technical Handover & Analysis for Cursor

> **Target Device**: Redmi 13 5G / POCO M6 Plus 5G (`breeze_in` / `breeze`)  
> **Chipset**: Qualcomm Snapdragon 4 Gen 2 (SM4450)  
> **Camera Sensor**: Samsung HM6 108MP (12000x9000, 3x3 nona-binning -> 4000x3000 12MP)  
> **Operating System**: Project Infinity-X (Android 17 / SDK 37, Linux Kernel 5.10.266)  
> **Environment**: Project Infinity-X (Android 17 / SDK 37), SELinux strictly **Enforcing**  
> **ADB Device Serial**: `be900bb`  
> **Git Repository**: `/home/wtf/Projects/hyperos_camera_breeze` (branch `main`, tag `v1.4-photo-stable`)  

---

## 1. Executive Summary & Objective

The objective of this project is to provide a 100% stable, fully native Xiaomi HyperOS Camera (`com.android.camera`) port for Redmi 13 5G / POCO M6 Plus 5G running Android 17 (Project Infinity-X) via native AOSP Soong ROM compilation (`Android.bp` & `breeze-camera.mk`).

### Current Status:
- **Offline Shutter Lag**: **100% Solved** and verified. Patched native libraries (`libcamera_algoup_jni.xiaomi.so`, `libcamera_mianode_jni.xiaomi.so`) for Android 17 vtable shift (`Surface::connect` offset `0xAD` -> `0xA9`). Bypassed MIVI offline daemon queue in `service.sh`. Normal Photo mode captures instantaneous photos with zero shutter lag.
- **Normal Photo Mode (Mode 163)**: **100% Functional**. Stream configuration: `picture size (YUV): 4000x3000`, `preview size: 1440x1080`.
- **Remaining Task**: **Ultra HD Mode (Mode 175, 108MP / 12000x9000)** crashes upon mode switch / viewfinder initialization due to an invalid stream configuration (`2000x1500`) passed to the Qualcomm CamX HAL.

---

## 2. The Ultra HD Mode (Mode 175) Failure Analysis

### 2.1 The Exact HAL Error
When switching to Ultra HD mode (Mode 175), the following fatal crash occurs in Qualcomm's CamX HAL:

```text
11-01 20:08:47.404 18177 18193 D MCAM_Camera2Module: updateSize: picture size (YUV): 2000x1500, preview size: 1440x1080, sensor raw image size: null
11-01 20:08:47.410 18177 18193 I MCAM_Camera2Module: [K_PROCESS]: startPreview: set PictureSize with 2000x1500
11-01 20:08:47.410 18177 18193 D MCAM_Camera2Module: startPreview: set PictureFormat to JPEG
11-01 20:08:47.410 18177 18193 D MCAM_Camera2Module: [QCFA]startPreview: set qcfa enable false
11-01 20:08:47.426  1390  2556 E CamX    : [ERROR][HAL    ] camxhaldevice.cpp:1860 CheckValidStreamConfig() Invalid streamStype: 0, format: 35 (2000 x 1500)
11-01 20:08:47.440 18177 18177 I MCAM_BaseModule: [K_PROCESS]: enableCameraControls: enable = false, caller: com.android.camera.module.BaseModule.onCameraException(SourceFile:169), com.android.camera.module.BaseModule.onCameraOpenedFail(SourceFile:34), com.android.camera.module.Camera2Module.handleMessage(SourceFile:338)
```

### 2.2 Why CamX Hal Rejects `2000x1500`
The SM4450 sensor driver in `/vendor/lib64/hw/camera.qcom.so` (Qualcomm CamX HAL) defines a strict static table of supported stream configurations for Format 35 (`YUV_420_888`):
- **Supported Format 35 resolutions**:
  - `4000 x 3000` (12MP 4:3 native binned)
  - `3280 x 2460`
  - `3264 x 2448`
  - `3200 x 2400`
  - `2592 x 1944`
  - `2048 x 1536`
  - `1920 x 1080` (16:9 1080p)
  - `1440 x 1080`
  - `1280 x 720`
- **Notice**: **`2000 x 1500` DOES NOT EXIST** in the CamX HAL valid stream table!
- When `MiuiCamera.apk` passes format `35` with `2000 x 1500`, CamX HAL fails `CheckValidStreamConfig()`, terminates the session, and triggers `onCameraOpenedFail()`.

### 2.3 Why `MiuiCamera.apk` Selects `2000x1500`
In `MiuiCamera.apk`:
1. `com.android.camera.features.mode.pixel.PixelModule` handles Mode 175 and inherits from `Camera2Module`.
2. During initialization, `Camera2Module.updateSize()` calls `updatePictureAndPreviewSize()`.
3. It retrieves the picture size from `mLoadStreamSizeBase.H.get(PICTURE_SIZE)`.
4. In Mode 175, `mLoadStreamSizeBase` (`Lv3/o;`) runs `Lv3/l;->q` (`code_off = 0x6a653c` in `classes2.dex`).
5. Inside `Lv3/l;->q`:
   - Xiaomi's downscale routine calls `LA/v3;->c` (calls at `0x6a670c` and `0x6a6824`).
   - For 4:3 aspect ratio, it computes a downscaled intermediate stream: `4000 / 2 = 2000`, `3000 / 2 = 1500`.
   - At `0x6a68a4`: it puts `Size(2000, 1500)` into `HashMap H` under key `PICTURE_SIZE`.
6. Then `Camera2Module.startPreview()` calls:
   ```java
   mCameraManager.setPictureSize(size); // receives 2000x1500
   ```
   and requests a YUV stream of `2000x1500` from Qualcomm HAL.

---

## 3. Reverse Engineering Blueprint (DEX Offsets & Bytecode)

All changes are focused on `classes2.dex` inside `MiuiCamera.apk`:
- **APK path**: `proprietary/product/priv-app/MiuiCamera/MiuiCamera.apk`
- **`classes2.dex` ZIP local header offset**: `23153120` (`0x01614940`)
- **`classes2.dex` uncompressed data offset**: `23153168` (`0x01614970`)
- **`classes2.dex` file size**: `10348448` bytes (`0x9DEAB0`)
- **Central Directory entry CRC offset**: `184984143`

### Key Method 1: `Ls3/e;->F0` (`mCameraManager.setPictureSize(Size size)`)
- **Method Index**: `63604`
- **Code Offset**: `0x68f28c`
- **Bytecode Inspection**:
  ```text
  0x68f28c: 02 00 02 00 00 00 00 00 00 00 00 00 03 00 00 00
  0x68f29c: 5b 01 05 f1   # iput-object v1, v0, Ls3/e;->K:Landroid/util/Size; (field 0xf105)
  0x68f2a0: 0e 00         # return-void
  0x68f2a2: 00 00         # padding
  ```
  - `v0` = `this` (`Ls3/e;`)
  - `v1` = `size` (`Landroid/util/Size;`)
  - `K` = `mPictureSize` (field `0xf105`)

### Key Method 2: `Ls3/e;->K0` (`mCameraManager.getPictureSize()`)
- **Code Offset**: `0x68cec4`
- **Bytecode Inspection**:
  ```text
  0x68cec4: 54 00 05 f1   # iget-object v0, v0, Ls3/e;->K:Landroid/util/Size;
  0x68cec8: 11 00         # return-object v0
  ```

### Key Method 3: `Camera2Module.updatePictureAndPreviewSize`
- **Code Offset Range**: `0x471070 - 0x471200`
- **Bytecode Inspection**:
  ```text
  0x471088: 54 14 b2 f3   # iget-object v4, v1, PICTURE_SIZE key
  0x47108c: 6e 20 d5 e9 b4 00 # invoke-virtual {v4, vb}, Map;->get(key)
  0x471092: 0c 04         # move-result-object v4 (Size object)
  0x471094: 1f 04 aa 10   # check-cast v4, Landroid/util/Size;
  0x471098: 54 18 b1 f3   # iget-object
  0x47109c: 55 88 81 f3   # iget-boolean
  0x4710a0: 38 08 8e 00   # if-eqz v8, +0x8e
  0x4710a4: 6e 10 7d 42 04 00 # invoke-virtual {v4}, Size;->getWidth()
  0x4710aa: 0a 04         # move-result v4
  0x4710ac: 13 08 04 10   # const/16 v8, 4100
  0x4710b0: 37 84 86 00   # if-le v4, v8, +0x86
  ...
  0x4710f4: 71 20 7f 01 84 00 # invoke-static {v4, v8}, LA/v3;->c (downscale)
  ```

---

## 4. Proposed Fix Strategies for Cursor

### Strategy A: Clamping/Replacing `mPictureSize` in `setPictureSize` (`Ls3/e;->F0`)
Whenever `setPictureSize` is called:
If `v1.getWidth() == 2000`, replace `v1` with a `4000x3000` `Size` object!
Or, if `CameraManager` receives `2000x1500`, clamp it to `4000x3000`.

### Strategy B: Fix `updatePictureAndPreviewSize` (Directly in `Camera2Module`)
In `Camera2Module.updatePictureAndPreviewSize` at `0x471092`:
Right after `v4` (`Size`) is retrieved from `Map.get(PICTURE_SIZE)`:
If `v4.getWidth() == 2000`, override `v4` with `4000x3000` (or instantiate `new Size(4000, 3000)`).
*Note*: `new Size(4000, 3000)` opcode in Dalvik:
```text
new-instance vX, Landroid/util/Size; (type 0x10aa)
const/16 vY, 4000 (0x0fa0)
const/16 vZ, 3000 (0x0bb8)
invoke-direct {vX, vY, vZ}, Landroid/util/Size;-><init>(II)V (method 0x427b)
```

### Strategy C: Re-evaluating `device_features/breeze.xml` vs Smali Patch
In commit `b8a83d2`, `<item>com.android.camera:0, add, 2000, 1500, 35, false</item>` was removed because Qualcomm's CamX HAL rejected it. **CamX HAL enforces its own sensor table.** The app MUST request a stream size that CamX HAL supports (`4000x3000`).

---

## 5. Development & Verification Workflow

### 5.1 In-Place DEX Patching Pipeline
The script `/home/wtf/Projects/hyperos_camera_breeze/patch_camera.py` directly patches uncompressed `classes2.dex` inside `MiuiCamera.apk`, recalculates SHA1, Adler32, and CRC32 in the ZIP Local Header & Central Directory without re-signing or repackaging:

```bash
cd /home/wtf/Projects/hyperos_camera_breeze
python3 patch_camera.py
```

### 5.2 Live Deployment to Device (No Reboot Required)
Run these commands to instantly update and test on the connected phone (`be900bb`):

```bash
# 1. Package recovery zip
./package.sh

# 2. Sideload via AOSP Recovery
adb reboot sideload
adb sideload /home/wtf/Downloads/HyperOS_Camera_breeze_Recovery_Flashable.zip
```

### 5.3 Automated Ultra HD Live Testing
Simulate mode switch and capture using ADB:

```bash
# Clear logcat
adb shell su -c "logcat -c"

# Launch camera app
adb shell "am start -n com.android.camera/.Camera"
sleep 2

# Tap Ultra HD Mode tab (coordinates for 1080x2400 screen: x=107, y=1934)
adb shell "input tap 107 1934"
sleep 2

# Check logcat output
adb shell su -c "logcat -d | grep -E 'MCAM_Camera2Module|CamX|CheckValidStreamConfig' | tail -n 30"

# If viewfinder is live, capture photo (Shutter button: x=540, y=2147)
adb shell "input tap 540 2147"
sleep 3

# Verify captured photo resolution in DCIM
adb shell "ls -la /sdcard/DCIM/Camera/"
```

### 5.4 Final Flashable ZIP Packaging
Once verified:
```bash
./package.sh
```
This produces `HyperOS_Camera_breeze_Recovery_Flashable.zip` ready for flashing via AOSP Recovery (`adb sideload`).

---

## 6. Critical Files & Repo Directory Layout

```text
/home/wtf/Projects/xiaomi_breeze_camera/
├── package.sh                    # Master AOSP Recovery ZIP packaging script
├── HyperOS_Camera_breeze_Recovery_Flashable.zip # Generated flashable module ZIP
├── Android.bp                    # Soong build system blueprint
├── breeze-camera.mk              # Product makefile for ROM compilation
├── addon.d/70-miuicamera.sh      # OTA survival script
├── sepolicy/                     # SELinux rules for Enforcing mode
├── META-INF/                     # AOSP Recovery installer
├── proprietary/
│   ├── product/
│   │   ├── priv-app/MiuiCamera/
│   │   │   └── MiuiCamera.apk    # Stock HyperOS camera app
│   │   └── etc/device_features/
│   │       ├── breeze.xml        # Device feature configurations
│   │       └── breeze_in.xml
│   └── system_ext/
│       ├── lib64/
│       │   ├── libcamera_algoup_jni.xiaomi.so # Surface::connect patched
│       │   └── libcamera_mianode_jni.xiaomi.so # Surface::connect patched
│       └── framework/
│           ├── miui-framework.jar
│           └── miui-cameraopt.jar
```

---

## 7. Next Action for Cursor
1. Inspect `patch_camera.py`.
2. Apply the `Size(4000, 3000)` clamp in `classes2.dex` at `Camera2Module.updatePictureAndPreviewSize` or `Ls3/e;->F0`.
3. Deploy to `be900bb`, switch to Ultra HD mode, and verify that CamX HAL accepts the stream config and saves a full-resolution 108MP shot!
