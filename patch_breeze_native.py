#!/usr/bin/env python3
"""
patch_breeze_native.py:
Applies targeted Smali fixes to OUR native MiuiCamera.apk for breeze:
1. Photo Mode:
   - Full parallel bypass from Sapphire (commit f248d67):
     * Camera2Module.isParallel() -> false
     * Camera2Module.enablePreviewAsThumbnail() -> false
     * Camera2Module.isParallelSessionEnable() -> false
     * Camera2Module.isShot2GalleryOrEnableParallel() -> false
   - Completely eliminates offline MIVI daemon queue hang and 4-take freeze.
2. Portrait Mode:
   - Camera2Module.updatePortraitBokehRole() -> role 0x3f (role 63, Single Sensor Bokeh).
     Qualcomm CamX opens only the main 108MP camera, completely eliminating "couldn't connect to camera".
   - H3/f.smali (Portrait ShotTypeHandler) -> shotType 0 (normal still capture) to save photos immediately without hanging.
   - Z5/Z.smali & Z5/L0.smali are kept 100% UNTOUCHED to prevent any launch crashes!
3. Night Mode:
   - NightModule.getRawCallbackType() -> 0 (prevents unsupported RAW burst stream crash).
   - NightModule.getGraphDescriptorBean() -> standard session operating mode (super.getGraphDescriptorBean()).
   - NightModule.isParallelSessionEnable() -> false.
   - H3/i.smali (Night ShotTypeHandler) -> shotType 0 (clean night capture without HAL error 4 crash).
4. Watermark & Saving:
   - Null-safety checks in D5/c.smali for CaptureResult and ICustomCaptureResult.
   - Native Skia watermark rendering is fully preserved!
5. Documents:
   - DocModuleEntry.support() -> false (keeps Document mode disabled).
6. Ultra HD (108MP):
   - Tripartite downscale bypass and PixelModule parallel bypass fully preserved from base v13 APK.
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
OUT_APK_V16 = "/serverhive5/wandererdev/MiuiCamera_breeze_fixed_v16_640003210.apk"

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
        dex2_path = os.path.join(td, "classes2.dex")
        smali_dir = os.path.join(td, "smali")

        with zipfile.ZipFile(APK_IN, "r") as z:
            z.extract("classes2.dex", td)

        print("[*] Disassembling classes2.dex...")
        subprocess.run(["baksmali", "d", dex2_path, "-o", smali_dir], check=True)

        # ---------------------------------------------------------------------
        # 1. Camera2Module: Photo mode Sapphire parallel bypass & Portrait role 63
        # ---------------------------------------------------------------------
        c2m_smali = os.path.join(smali_dir, "com/android/camera/module/Camera2Module.smali")
        patch_method(
            c2m_smali,
            r"\.method private isParallel\(\)Z.*?\n\.end method",
            """.method private isParallel()Z
    .registers 2

    const/4 v0, 0x0

    return v0
.end method""",
            "Camera2Module.isParallel (private) -> false"
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
    .registers 2
    .annotation build Lcom/android/camera/jacoco/JacocoForceIgnore;
    .end annotation

    const/4 v0, 0x0

    return v0
.end method""",
            "Camera2Module.isShot2GalleryOrEnableParallel -> false"
        )

        old_bokeh_role = """    :cond_69
    const/16 v1, 0x3d

    :goto_6b"""
        new_bokeh_role = """    :cond_69
    const/16 v1, 0x3f

    :goto_6b"""
        patch_file(c2m_smali, old_bokeh_role, new_bokeh_role, "Camera2Module.updatePortraitBokehRole -> role 0x3f (63)")

        # ---------------------------------------------------------------------
        # 2. H3/f.smali: Portrait ShotTypeHandler -> shotType 0
        # ---------------------------------------------------------------------
        h3f_smali = os.path.join(smali_dir, "H3/f.smali")
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

        # ---------------------------------------------------------------------
        # 3. NightModule.smali: raw callback, graph descriptor, parallel bypass
        # ---------------------------------------------------------------------
        nm_smali = os.path.join(smali_dir, "com/android/camera/features/mode/night/photo/NightModule.smali")
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

        # ---------------------------------------------------------------------
        # 4. H3/i.smali: Night ShotTypeHandler -> shotType 0
        # ---------------------------------------------------------------------
        h3i_smali = os.path.join(smali_dir, "H3/i.smali")
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

        # ---------------------------------------------------------------------
        # 5. D5/c.smali: Watermark NPE Fix
        # ---------------------------------------------------------------------
        d5c_smali = os.path.join(smali_dir, "D5/c.smali")
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

        # ---------------------------------------------------------------------
        # 6. DocModuleEntry.smali: Disable Document mode
        # ---------------------------------------------------------------------
        doc_smali = os.path.join(smali_dir, "com/android/camera/features/mode/doc/DocModuleEntry.smali")
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

        # ---------------------------------------------------------------------
        # 7. Reassemble classes2.dex
        # ---------------------------------------------------------------------
        new_dex2 = os.path.join(td, "classes2_new.dex")
        print("[*] Reassembling classes2.dex with smali...")
        subprocess.run(["smali", "a", smali_dir, "-o", new_dex2], check=True)

        # ---------------------------------------------------------------------
        # 8. Pack into APK, bump versionCode 640003207 -> 640003210
        # ---------------------------------------------------------------------
        raw_apk = os.path.join(td, "repacked.apk")
        aligned_apk = os.path.join(td, "aligned.apk")

        print("[*] Updating APK contents...")
        with zipfile.ZipFile(APK_IN, "r") as zin:
            with zipfile.ZipFile(raw_apk, "w") as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    if item.filename == "classes2.dex":
                        with open(new_dex2, "rb") as df:
                            data = df.read()
                        print(f"[+] Replaced classes2.dex in APK ({len(data)} bytes)")
                    elif item.filename == "AndroidManifest.xml":
                        # Bump 640003207 (87ac2526) -> 640003210 (8aac2526)
                        if b"\x87\xac\x25\x26" in data:
                            data = data.replace(b"\x87\xac\x25\x26", b"\x8a\xac\x25\x26", 1)
                            print("[+] Bumped versionCode to 640003210 in AndroidManifest.xml")
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
            "--out", OUT_APK_V16,
            aligned_apk
        ], check=True)

        print("[*] Verifying output APK...")
        subprocess.run(["apksigner", "verify", "-v", OUT_APK_V16], check=True)
        print(f"[+] SUCCESS! Created {OUT_APK_V16}")

        # Also copy to repo proprietary location
        print(f"[*] Updating repo vendor APK: {REPO_APK}")
        shutil.copy2(OUT_APK_V16, REPO_APK)
        print(f"[+] Successfully copied to {REPO_APK}")

if __name__ == "__main__":
    main()
