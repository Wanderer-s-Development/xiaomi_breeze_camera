#!/usr/bin/env python3
"""
patch_breeze_native.py:
Applies targeted Smali fixes to OUR native MiuiCamera.apk for breeze:
1. Fix Fatal Launch Crash (Crash 1 - VerifyError in Z5.e.V1):
   - Replaces corrupted method Z5.e.V1 with clean, valid Dalvik bytecode returning true.
   - Eliminates 'wide register index out of range (87+1 >= 6)' which caused class Z5.e rejection.
2. Fix Photo Save Crash (Crash 3 - NullPointerException in l4.a.g / File.<init>):
   - Adds null-safety check on savePath (Laa/p;->q) before calling new File(path).
   - Falls back cleanly to standard timestamp filename generation if path is null.
3. Fix Secondary Crash (Crash 2 - UnsatisfiedLinkError in MiCameraAlgo.init):
   - Catches Throwable during MiCamAlgoInterfaceJNI.init() to prevent unhandled RxJava fatal crash.
4. Photo Mode (4-take freeze & queue hang fix):
   - Camera2Module.isParallel() -> false for normal Photo mode (0xa3)
   - Camera2Module.enablePreviewAsThumbnail() -> false
   - Camera2Module.isParallelSessionEnable() -> false
   - Camera2Module.isShot2GalleryOrEnableParallel() -> false for normal Photo mode
5. Ultra HD Mode (108MP image saving fix):
   - Restores isParallel() and isShot2GalleryOrEnableParallel() to return true for
     moduleIndex == 0xaf (Ultra HD) or instanceof PixelModule.
   - Allows 108MP frames to be processed and saved without dropping!
6. Watermark Fix (Shutter lockup fix & _global offline watermark):
   - Camera2Module.isCloudWatermarkProcessing() -> false.
   - Prevents cloud watermark synchronization from permanently blocking shutter (isBlockSnap).
   - W2/c.smali: forces _global branch to bypass China online font sync.
   - Skia native watermark rendering preserved without shutter freeze.
7. Portrait Mode:
   - Camera2Module.updatePortraitBokehRole() -> role 0x3f (role 63, Single Sensor Bokeh).
     Qualcomm CamX opens only the main 108MP camera, completely eliminating "couldn't connect to camera".
   - H3/f.smali (Portrait ShotTypeHandler) -> shotType 0 (normal still capture) to save photos immediately without hanging.
   - Z5/Z.smali & Z5/L0.smali are kept 100% UNTOUCHED to prevent any launch crashes!
8. Night Mode:
   - NightModule.getRawCallbackType() -> 0 (prevents unsupported RAW burst stream crash).
   - NightModule.getGraphDescriptorBean() -> standard session operating mode (super.getGraphDescriptorBean()).
   - NightModule.isParallelSessionEnable() -> false.
   - H3/i.smali (Night ShotTypeHandler) -> shotType 0 (clean night capture without HAL error 4 crash).
9. Watermark NPE Safety:
   - Null-safety checks in D5/c.smali for CaptureResult and ICustomCaptureResult.
10. Documents:
   - DocModuleEntry.support() -> false (keeps Document mode disabled).
11. Watermark Green Bar & Corruption Fix (GPU Sync):
   - Inserts GLES20.glFinish() before CameraNativeTool.compressHardwareBuffer() in V0/f.smali and J9/f.smali.
   - Inserts GLES20.glFinish() before V0/f.d(Rect) in I/a.smali.
   - Guarantees Adreno GPU flushes tile cache and chroma (UV) plane to AHardwareBuffer before CPU lock.
12. Watermark Device Model Fix ("Redmi 13 5G"):
   - G7/b.w() -> false.
   - G7/b.m() -> unconditionally selects index 1 ("13 5G") instead of index 0 ("Note 13R").
   - G7/c.<clinit>() -> unconditionally sets m (isGlobal) to true.
"""

import os
import sys
import shutil
import subprocess
import zipfile
import tempfile
import re

APK_IN = "/serverhive5/wandererdev/MiuiCamera_pre_sapphire_v13_640003207.apk"
KEY_PK8 = "/serverhive5/wandererdev/infinityx/vendor/infinity-priv/keys/platform.pk8"
CERT_PEM = "/serverhive5/wandererdev/infinityx/vendor/infinity-priv/keys/platform.x509.pem"
ZIPALIGN = "/serverhive5/wandererdev/infinityx/prebuilts/build-tools/linux-x86/bin/zipalign"

REPO_APK = "/serverhive5/wandererdev/infinityx/vendor/xiaomi/breeze-camera/proprietary/product/priv-app/MiuiCamera/MiuiCamera.apk"
OUT_APK_V20 = "/serverhive5/wandererdev/MiuiCamera_breeze_fixed_v20_640003214.apk"

def patch_file(path, old_pattern, new_pattern, label):
    with open(path, "r") as f:
        content = f.read()
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern, 1)
        with open(path, "w") as f:
            f.write(content)
        print(f"[+] Successfully patched {label}")
        return True
    elif new_pattern in content:
        print(f"[*] Already patched: {label}")
        return True
    else:
        raise ValueError(f"[-] Failed to match pattern for {label} in {path}")

def patch_method(path, method_regex, replacement_body, label):
    with open(path, "r") as f:
        content = f.read()
    if re.search(method_regex, content, re.DOTALL):
        content = re.sub(method_regex, replacement_body, content, count=1, flags=re.DOTALL)
        with open(path, "w") as f:
            f.write(content)
        print(f"[+] Successfully replaced method {label}")
        return True
    else:
        raise ValueError(f"[-] Failed to find method regex for {label} in {path}")

def main():
    print(f"[*] Base input APK: {APK_IN}")
    assert os.path.exists(APK_IN), f"APK_IN not found: {APK_IN}"

    with tempfile.TemporaryDirectory() as td:
        dex1_path = os.path.join(td, "classes.dex")
        smali1_dir = os.path.join(td, "smali1")
        dex2_path = os.path.join(td, "classes2.dex")
        smali2_dir = os.path.join(td, "smali2")
        dex4_path = os.path.join(td, "classes4.dex")
        smali4_dir = os.path.join(td, "smali4")

        with zipfile.ZipFile(APK_IN, "r") as z:
            z.extract("classes.dex", td)
            z.extract("classes2.dex", td)
            z.extract("classes4.dex", td)

        print("[*] Disassembling classes.dex...")
        subprocess.run(["baksmali", "d", dex1_path, "-o", smali1_dir], check=True)

        print("[*] Disassembling classes2.dex...")
        subprocess.run(["baksmali", "d", dex2_path, "-o", smali2_dir], check=True)

        print("[*] Disassembling classes4.dex...")
        subprocess.run(["baksmali", "d", dex4_path, "-o", smali4_dir], check=True)

        # =====================================================================
        # 1. FIX FATAL LAUNCH CRASH (Crash 1): Z5/e.smali V1 VerifyError
        # =====================================================================
        z5e_smali = os.path.join(smali2_dir, "Z5/e.smali")
        patch_method(
            z5e_smali,
            r"\.method public static V1\(LZ5/d;\)Z.*?\n\.end method",
            """.method public static V1(LZ5/d;)Z
    .registers 2

    const/4 v0, 0x1

    return v0
.end method""",
            "Z5/e.V1 (CameraCapabilitiesUtil quick snapshot) -> clean return true (Fix VerifyError)"
        )

        # =====================================================================
        # 2. FIX PHOTO SAVE CRASH (Crash 3): l4/a.smali NullPointerException
        # =====================================================================
        l4a_smali = os.path.join(smali2_dir, "l4/a.smali")

        # Location 1: around line 1771
        old_l4a_loc1 = """:cond_156
    :goto_156
    new-instance v5, Ljava/io/File;

    iget-object v6, v13, Laa/p;->q:Ljava/lang/String;

    invoke-direct {v5, v6}, Ljava/io/File;-><init>(Ljava/lang/String;)V

    invoke-static {v5}, Ljc/x;->h(Ljava/io/File;)Ljava/lang/String;

    move-result-object v5

    goto :goto_154"""

        new_l4a_loc1 = """:cond_156
    :goto_156
    iget-object v6, v13, Laa/p;->q:Ljava/lang/String;

    if-nez v6, :cond_file_ok_1

    goto :cond_13b

    :cond_file_ok_1
    new-instance v5, Ljava/io/File;

    invoke-direct {v5, v6}, Ljava/io/File;-><init>(Ljava/lang/String;)V

    invoke-static {v5}, Ljc/x;->h(Ljava/io/File;)Ljava/lang/String;

    move-result-object v5

    goto :goto_154"""
        patch_file(l4a_smali, old_l4a_loc1, new_l4a_loc1, "l4/a.smali location 1 null check for Laa/p;->q")

        # Location 2: around line 2803
        old_l4a_loc2 = """:cond_502
    :goto_502
    new-instance v5, Ljava/io/File;

    iget-object v6, v14, Laa/p;->q:Ljava/lang/String;

    invoke-direct {v5, v6}, Ljava/io/File;-><init>(Ljava/lang/String;)V

    invoke-static {v5}, Ljc/x;->h(Ljava/io/File;)Ljava/lang/String;

    move-result-object v5

    goto :goto_500"""

        new_l4a_loc2 = """:cond_502
    :goto_502
    iget-object v6, v14, Laa/p;->q:Ljava/lang/String;

    if-nez v6, :cond_file_ok_2

    goto :cond_4e7

    :cond_file_ok_2
    new-instance v5, Ljava/io/File;

    invoke-direct {v5, v6}, Ljava/io/File;-><init>(Ljava/lang/String;)V

    invoke-static {v5}, Ljc/x;->h(Ljava/io/File;)Ljava/lang/String;

    move-result-object v5

    goto :goto_500"""
        patch_file(l4a_smali, old_l4a_loc2, new_l4a_loc2, "l4/a.smali location 2 null check for Laa/p;->q")

        # =====================================================================
        # 3. FIX SECONDARY JNI CRASH (Crash 2): MiCameraAlgo.smali init try-catch
        # =====================================================================
        algo_smali = os.path.join(smali4_dir, "com/xiaomi/engine/MiCameraAlgo.smali")
        old_algo_init = r"\.method public static init\(Landroid/content/Context;\)V.*?\n\.end method"
        new_algo_init = """.method public static init(Landroid/content/Context;)V
    .registers 4

    sget-object v0, Lcom/xiaomi/engine/MiCameraAlgo;->TAG:Ljava/lang/String;

    const-string v1, "init: E"

    invoke-static {v0, v1}, Lcom/xiaomi/engine/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    if-eqz p0, :cond_31

    invoke-virtual {p0}, Landroid/content/Context;->getFilesDir()Ljava/io/File;

    move-result-object p0

    invoke-virtual {p0}, Ljava/io/File;->getAbsolutePath()Ljava/lang/String;

    move-result-object p0

    new-instance v1, Ljava/lang/StringBuilder;

    const-string v2, "init: application file path to algorithm lib: "

    invoke-direct {v1, v2}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    invoke-virtual {v1, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-static {v0, v1}, Lcom/xiaomi/engine/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    :try_start_jni
    invoke-static {p0}, Lcom/xiaomi/engine/MiCamAlgoInterfaceJNI;->init(Ljava/lang/String;)I

    move-result p0

    const-string v1, "init"

    invoke-static {p0, v0, v1}, Lcom/xiaomi/engine/Util;->assertOrNot(ILjava/lang/String;Ljava/lang/String;)V
    :try_end_jni
    .catchall {:try_start_jni .. :try_end_jni} :catch_jni

    goto :goto_jni_done

    :catch_jni
    move-exception p0

    const-string v1, "MiCamAlgoInterfaceJNI.init failed, ignored"

    invoke-static {v0, v1, p0}, Lcom/xiaomi/engine/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    :goto_jni_done
    const-string p0, "init: X"

    invoke-static {v0, p0}, Lcom/xiaomi/engine/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    return-void

    :cond_31
    new-instance p0, Ljava/lang/IllegalArgumentException;

    const-string v0, "context is null!"

    invoke-direct {p0, v0}, Ljava/lang/IllegalArgumentException;-><init>(Ljava/lang/String;)V

    throw p0
.end method"""
        patch_method(algo_smali, old_algo_init, new_algo_init, "MiCameraAlgo.init try-catch Throwable")

        # =====================================================================
        # 4. Camera2Module: Photo mode parallel bypass & Ultra HD (108MP) parallel routing
        # =====================================================================
        c2m_smali = os.path.join(smali2_dir, "com/android/camera/module/Camera2Module.smali")
        patch_method(
            c2m_smali,
            r"\.method private isParallel\(\)Z.*?\n\.end method",
            """.method private isParallel()Z
    .registers 3

    invoke-virtual {p0}, Lcom/android/camera/module/BaseModule;->getModuleIndex()I

    move-result v0

    const/16 v1, 0xaf

    if-ne v0, v1, :cond_a

    const/4 v0, 0x1

    return v0

    :cond_a
    instance-of v0, p0, Lcom/android/camera/features/mode/pixel/PixelModule;

    if-eqz v0, :cond_10

    const/4 v0, 0x1

    return v0

    :cond_10
    const/4 v0, 0x0

    return v0
.end method""",
            "Camera2Module.isParallel -> true for UltraHD/PixelModule (0xaf), false for Photo"
        )

        patch_method(
            c2m_smali,
            r"\.method public enablePreviewAsThumbnail\(\)Z.*?\n\.end method",
            """.method public enablePreviewAsThumbnail()Z
    .registers 2
    .annotation build Lcom/android/camera/jacoco/JacocoForceIgnore;
    .end annotation

    const/4 v0, 0x0

    return v0
.end method""",
            "Camera2Module.enablePreviewAsThumbnail -> false"
        )

        patch_method(
            c2m_smali,
            r"\.method public isParallelSessionEnable\(\)Z.*?\n\.end method",
            """.method public isParallelSessionEnable()Z
    .registers 2
    .annotation build Lcom/android/camera/jacoco/JacocoIgnore;
        ignore = false
        key = "!isSupportMIVI2"
        type = 0x0
    .end annotation

    const/4 v0, 0x0

    return v0
.end method""",
            "Camera2Module.isParallelSessionEnable -> false"
        )

        patch_method(
            c2m_smali,
            r"\.method public isShot2GalleryOrEnableParallel\(\)Z.*?\n\.end method",
            """.method public isShot2GalleryOrEnableParallel()Z
    .registers 3
    .annotation build Lcom/android/camera/jacoco/JacocoForceIgnore;
    .end annotation

    invoke-virtual {p0}, Lcom/android/camera/module/BaseModule;->getModuleIndex()I

    move-result v0

    const/16 v1, 0xaf

    if-ne v0, v1, :cond_a

    const/4 v0, 0x1

    return v0

    :cond_a
    instance-of v0, p0, Lcom/android/camera/features/mode/pixel/PixelModule;

    if-eqz v0, :cond_10

    const/4 v0, 0x1

    return v0

    :cond_10
    const/4 v0, 0x0

    return v0
.end method""",
            "Camera2Module.isShot2GalleryOrEnableParallel -> true for UltraHD/PixelModule (0xaf), false for Photo"
        )

        # =====================================================================
        # 5. Camera2Module: Fix Watermark shutter lockup (isCloudWatermarkProcessing -> false)
        # =====================================================================
        patch_method(
            c2m_smali,
            r"\.method private isCloudWatermarkProcessing\(LZ5/a;I\)Z.*?\n\.end method",
            """.method private isCloudWatermarkProcessing(LZ5/a;I)Z
    .registers 4

    const/4 v0, 0x0

    return v0
.end method""",
            "Camera2Module.isCloudWatermarkProcessing -> false (eliminates watermark shutter lockup)"
        )

        # =====================================================================
        # 6. Watermark _global fix: W2/c.smali (force _global to bypass online font sync)
        # =====================================================================
        w2c_smali = os.path.join(smali2_dir, "W2/c.smali")
        old_w2c = """:cond_31
    const-string v0, "ro.product.mod_device"

    const-string v1, ""

    invoke-static {v0, v1}, Lic/f;->b(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    if-eqz v0, :cond_44

    const-string v1, "_global"

    invoke-virtual {v0, v1}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v0

    if-eqz v0, :cond_44

    goto :goto_52"""

        new_w2c = """:cond_31
    goto :goto_52"""
        patch_file(w2c_smali, old_w2c, new_w2c, "W2/c.smali force _global for watermark signature font")

        old_bokeh_role = """    :cond_69
    const/16 v1, 0x3d

    :goto_6b"""
        new_bokeh_role = """    :cond_69
    const/16 v1, 0x3f

    :goto_6b"""
        patch_file(c2m_smali, old_bokeh_role, new_bokeh_role, "Camera2Module.updatePortraitBokehRole -> role 0x3f (63)")

        # =====================================================================
        # 7. H3/f.smali: Portrait ShotTypeHandler -> shotType 0
        # =====================================================================
        h3f_smali = os.path.join(smali2_dir, "H3/f.smali")
        patch_method(
            h3f_smali,
            r"\.method public final c\(\)Ljava/lang/Object;.*?\n\.end method",
            """.method public final c()Ljava/lang/Object;
    .registers 2

    const/4 v0, 0x0

    invoke-static {v0}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;

    move-result-object v0

    return-object v0
.end method""",
            "H3/f.c() (Portrait ShotTypeHandler) -> shotType 0"
        )

        # =====================================================================
        # 8. NightModule.smali: raw callback, graph descriptor, parallel bypass
        # =====================================================================
        nm_smali = os.path.join(smali2_dir, "com/android/camera/features/mode/night/photo/NightModule.smali")
        patch_method(
            nm_smali,
            r"\.method public getRawCallbackType\(\)I.*?\n\.end method",
            """.method public getRawCallbackType()I
    .registers 2

    const/4 v0, 0x0

    return v0
.end method""",
            "NightModule.getRawCallbackType -> 0"
        )

        patch_method(
            nm_smali,
            r"\.method public getGraphDescriptorBean\(\)Lcom/xiaomi/engine/GraphDescriptorBean;.*?\n\.end method",
            """.method public getGraphDescriptorBean()Lcom/xiaomi/engine/GraphDescriptorBean;
    .registers 2

    invoke-super {p0}, Lcom/android/camera/module/Camera2Module;->getGraphDescriptorBean()Lcom/xiaomi/engine/GraphDescriptorBean;

    move-result-object v0

    return-object v0
.end method""",
            "NightModule.getGraphDescriptorBean -> super.getGraphDescriptorBean()"
        )

        patch_method(
            nm_smali,
            r"\.method public isParallelSessionEnable\(\)Z.*?\n\.end method",
            """.method public isParallelSessionEnable()Z
    .registers 2
    .annotation build Lcom/android/camera/jacoco/JacocoIgnore;
        ignore = false
        key = "!isSupportMIVI2"
        type = 0x0
    .end annotation

    const/4 v0, 0x0

    return v0
.end method""",
            "NightModule.isParallelSessionEnable -> false"
        )

        # =====================================================================
        # 9. H3/i.smali: Night ShotTypeHandler -> shotType 0
        # =====================================================================
        h3i_smali = os.path.join(smali2_dir, "H3/i.smali")
        patch_method(
            h3i_smali,
            r"\.method public final c\(\)Ljava/lang/Object;.*?\n\.end method",
            """.method public final c()Ljava/lang/Object;
    .registers 2

    const/4 v0, 0x0

    invoke-static {v0}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;

    move-result-object v0

    return-object v0
.end method""",
            "H3/i.c() (Night ShotTypeHandler) -> shotType 0"
        )

        # =====================================================================
        # 10. D5/c.smali: Watermark NPE Fix
        # =====================================================================
        d5c_smali = os.path.join(smali2_dir, "D5/c.smali")
        old_d5c_b = """.method public static b(Landroid/hardware/camera2/CaptureResult;)Lua/b;
    .registers 7

    sget-object v0, Landroid/hardware/camera2/CaptureResult;->SENSOR_EXPOSURE_TIME:Landroid/hardware/camera2/CaptureResult$Key;"""
        new_d5c_b = """.method public static b(Landroid/hardware/camera2/CaptureResult;)Lua/b;
    .registers 7

    if-nez p0, :cond_b_not_null

    new-instance v0, Lua/b;

    invoke-direct {v0}, Lua/b;-><init>()V

    return-object v0

    :cond_b_not_null
    sget-object v0, Landroid/hardware/camera2/CaptureResult;->SENSOR_EXPOSURE_TIME:Landroid/hardware/camera2/CaptureResult$Key;"""
        patch_file(d5c_smali, old_d5c_b, new_d5c_b, "D5/c.b(CaptureResult) null-check")

        old_d5c_call = """    iget-object v1, v7, Laa/p;->h:Landroid/hardware/camera2/TotalCaptureResult;

    if-nez v1, :cond_b6

    iget-object v1, v7, Laa/p;->g:Lcom/xiaomi/protocol/ICustomCaptureResult;

    invoke-static {v1, v9}, Lcom/xiaomi/protocol/ICustomCaptureResult;->toTotalCaptureResult(Lcom/xiaomi/protocol/ICustomCaptureResult;I)Landroid/hardware/camera2/TotalCaptureResult;

    move-result-object v1

    :cond_b6"""
        new_d5c_call = """    iget-object v1, v7, Laa/p;->h:Landroid/hardware/camera2/TotalCaptureResult;

    if-nez v1, :cond_b6

    iget-object v1, v7, Laa/p;->g:Lcom/xiaomi/protocol/ICustomCaptureResult;

    if-eqz v1, :cond_b5_no_ccr

    invoke-static {v1, v9}, Lcom/xiaomi/protocol/ICustomCaptureResult;->toTotalCaptureResult(Lcom/xiaomi/protocol/ICustomCaptureResult;I)Landroid/hardware/camera2/TotalCaptureResult;

    move-result-object v1

    goto :cond_b6

    :cond_b5_no_ccr
    const/4 v1, 0x0

    :cond_b6"""
        patch_file(d5c_smali, old_d5c_call, new_d5c_call, "D5/c caller null-check on ICustomCaptureResult")

        # =====================================================================
        # 11. DocModuleEntry.smali: Disable Document mode
        # =====================================================================
        doc_smali = os.path.join(smali2_dir, "com/android/camera/features/mode/doc/DocModuleEntry.smali")
        patch_method(
            doc_smali,
            r"\.method public support\(\)Z.*?\n\.end method",
            """.method public support()Z
    .registers 2

    const/4 v0, 0x0

    return v0
.end method""",
            "DocModuleEntry.support() -> false"
        )

        # =====================================================================
        # 12. GPU SYNC FIX: classes.dex (Eliminate Neon Green Watermark Band)
        # =====================================================================
        v0f_smali = os.path.join(smali1_dir, "V0/f.smali")
        old_v0f_compress = """    iget-boolean v7, p0, LV0/d;->d:Z

    invoke-static {v4, v6, v7, v5, v3}, Lcom/xiaomi/gl/texture/CameraNativeTool;->compressHardwareBuffer(Landroid/hardware/HardwareBuffer;[IZIZ)[B"""

        new_v0f_compress = """    iget-boolean v7, p0, LV0/d;->d:Z

    invoke-static {}, Landroid/opengl/GLES20;->glFinish()V

    invoke-static {v4, v6, v7, v5, v3}, Lcom/xiaomi/gl/texture/CameraNativeTool;->compressHardwareBuffer(Landroid/hardware/HardwareBuffer;[IZIZ)[B"""
        patch_file(v0f_smali, old_v0f_compress, new_v0f_compress, "V0/f.smali glFinish before compressHardwareBuffer")

        old_v0f_candy = """    invoke-virtual {v4, p0, v5}, Lcom/xiaomi/milab/filtersdk/CandySDK;->c(Ljava/lang/Object;[F)V

    invoke-virtual {v4}, Lcom/xiaomi/milab/filtersdk/CandySDK;->e()V"""

        new_v0f_candy = """    invoke-virtual {v4, p0, v5}, Lcom/xiaomi/milab/filtersdk/CandySDK;->c(Ljava/lang/Object;[F)V

    invoke-virtual {v4}, Lcom/xiaomi/milab/filtersdk/CandySDK;->e()V

    invoke-static {}, Landroid/opengl/GLES20;->glFinish()V"""
        patch_file(v0f_smali, old_v0f_candy, new_v0f_candy, "V0/f.smali glFinish after CandySDK.e()")

        ia_smali = os.path.join(smali1_dir, "I/a.smali")
        old_ia_1 = """    :goto_455
    invoke-virtual {v2, v1}, LV0/f;->d(Landroid/graphics/Rect;)V"""

        new_ia_1 = """    :goto_455
    invoke-static {}, Landroid/opengl/GLES20;->glFinish()V

    invoke-virtual {v2, v1}, LV0/f;->d(Landroid/graphics/Rect;)V"""
        patch_file(ia_smali, old_ia_1, new_ia_1, "I/a.smali location 1 glFinish before V0/f.d(Rect)")

        old_ia_2 = """    move-object/from16 v3, v27

    invoke-virtual {v3, v2}, LV0/f;->d(Landroid/graphics/Rect;)V"""

        new_ia_2 = """    move-object/from16 v3, v27

    invoke-static {}, Landroid/opengl/GLES20;->glFinish()V

    invoke-virtual {v3, v2}, LV0/f;->d(Landroid/graphics/Rect;)V"""
        patch_file(ia_smali, old_ia_2, new_ia_2, "I/a.smali location 2 glFinish before V0/f.d(Rect)")

        # =====================================================================
        # 13. GPU SYNC FIX: classes2.dex (J9/f.smali HardwareBufferToJpeg)
        # =====================================================================
        j9f_smali = os.path.join(smali2_dir, "J9/f.smali")
        old_j9f = """    const/4 v5, 0x1

    invoke-static {v0, v3, v2, v4, v5}, Lcom/xiaomi/gl/texture/CameraNativeTool;->compressHardwareBuffer(Landroid/hardware/HardwareBuffer;[IZIZ)[B"""

        new_j9f = """    const/4 v5, 0x1

    invoke-static {}, Landroid/opengl/GLES20;->glFinish()V

    invoke-static {v0, v3, v2, v4, v5}, Lcom/xiaomi/gl/texture/CameraNativeTool;->compressHardwareBuffer(Landroid/hardware/HardwareBuffer;[IZIZ)[B"""
        patch_file(j9f_smali, old_j9f, new_j9f, "J9/f.smali glFinish before compressHardwareBuffer")

        # =====================================================================
        # 14. WATERMARK DEVICE NAME FIX: classes4.dex (Force "Redmi 13 5G")
        # =====================================================================
        g7b_smali = os.path.join(smali4_dir, "G7/b.smali")
        patch_method(
            g7b_smali,
            r"\.method public final w\(\)Z.*?\n\.end method",
            """.method public final w()Z
    .registers 2

    const/4 v0, 0x0

    return v0
.end method""",
            "G7/b.w() -> false (force non-China model)"
        )

        old_g7b_m = """:cond_1e4
    invoke-virtual {v6, v2}, Landroid/util/SparseArray;->get(I)Ljava/lang/Object;

    move-result-object p0

    if-eqz p0, :cond_1f1

    invoke-virtual {v6, v2}, Landroid/util/SparseArray;->get(I)Ljava/lang/Object;

    move-result-object p0

    check-cast p0, [Ljava/lang/String;

    return-object p0"""

        new_g7b_m = """:cond_1e4
    invoke-virtual {v6, v1}, Landroid/util/SparseArray;->get(I)Ljava/lang/Object;

    move-result-object p0

    if-eqz p0, :cond_1f1

    invoke-virtual {v6, v1}, Landroid/util/SparseArray;->get(I)Ljava/lang/Object;

    move-result-object p0

    check-cast p0, [Ljava/lang/String;

    return-object p0"""
        patch_file(g7b_smali, old_g7b_m, new_g7b_m, "G7/b.m() force index 1 ('13 5G') at cond_1e4")

        g7c_smali = os.path.join(smali4_dir, "G7/c.smali")
        old_g7c = """    const-string v0, "ro.product.mod_device"

    invoke-static {v0, v3}, Lic/f;->b(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    const-string v3, "_global"

    invoke-virtual {v0, v3}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v0

    sput-boolean v0, LG7/c;->m:Z"""

        new_g7c = """    const/4 v0, 0x1

    sput-boolean v0, LG7/c;->m:Z"""
        patch_file(g7c_smali, old_g7c, new_g7c, "G7/c.<clinit> force isGlobal m = true")

        # =====================================================================
        # 15. Reassemble classes.dex, classes2.dex, and classes4.dex
        # =====================================================================
        new_dex1 = os.path.join(td, "classes_new.dex")
        print("[*] Reassembling classes.dex with smali...")
        subprocess.run(["smali", "a", smali1_dir, "-o", new_dex1], check=True)

        new_dex2 = os.path.join(td, "classes2_new.dex")
        print("[*] Reassembling classes2.dex with smali...")
        subprocess.run(["smali", "a", smali2_dir, "-o", new_dex2], check=True)

        new_dex4 = os.path.join(td, "classes4_new.dex")
        print("[*] Reassembling classes4.dex with smali...")
        subprocess.run(["smali", "a", smali4_dir, "-o", new_dex4], check=True)

        # =====================================================================
        # 16. Pack into APK, bump versionCode 640003207 -> 640003214
        # =====================================================================
        raw_apk = os.path.join(td, "repacked.apk")
        aligned_apk = os.path.join(td, "aligned.apk")

        print("[*] Updating APK contents...")
        with zipfile.ZipFile(APK_IN, "r") as zin:
            with zipfile.ZipFile(raw_apk, "w") as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    if item.filename == "classes.dex":
                        with open(new_dex1, "rb") as df:
                            data = df.read()
                        print(f"[+] Replaced classes.dex in APK ({len(data)} bytes)")
                    elif item.filename == "classes2.dex":
                        with open(new_dex2, "rb") as df:
                            data = df.read()
                        print(f"[+] Replaced classes2.dex in APK ({len(data)} bytes)")
                    elif item.filename == "classes4.dex":
                        with open(new_dex4, "rb") as df:
                            data = df.read()
                        print(f"[+] Replaced classes4.dex in APK ({len(data)} bytes)")
                    elif item.filename == "AndroidManifest.xml":
                        # Bump 640003207 (87ac2526) -> 640003214 (8eac2526)
                        if b"\x87\xac\x25\x26" in data:
                            data = data.replace(b"\x87\xac\x25\x26", b"\x8e\xac\x25\x26", 1)
                            print("[+] Bumped versionCode to 640003214 in AndroidManifest.xml")
                    zout.writestr(item, data)

        print("[*] Aligning APK with zipalign...")
        subprocess.run([ZIPALIGN, "-p", "-f", "4", raw_apk, aligned_apk], check=True)

        print("[*] Signing APK with Project Infinity-X platform key...")
        subprocess.run([
            "apksigner", "sign",
            "--v1-signing-enabled", "true",
            "--v2-signing-enabled", "true",
            "--v3-signing-enabled", "true",
            "--key", KEY_PK8,
            "--cert", CERT_PEM,
            "--out", OUT_APK_V20,
            aligned_apk
        ], check=True)

        print("[*] Verifying output APK...")
        subprocess.run(["apksigner", "verify", "-v", OUT_APK_V20], check=True)
        print(f"[+] SUCCESS! Created {OUT_APK_V20}")

        # Also copy to repo proprietary location
        print(f"[*] Updating repo vendor APK: {REPO_APK}")
        shutil.copy2(OUT_APK_V20, REPO_APK)
        print(f"[+] Successfully copied to {REPO_APK}")

if __name__ == "__main__":
    main()
