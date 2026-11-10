#!/usr/bin/env python3
"""
patch_breeze_native.py:
Applies targeted Smali fixes to OUR native MiuiCamera.apk for breeze:
1. Photo Mode:
   - Camera2Module.isParallel() (private) -> false (bypasses offline MIVI queue hang & 4-take freeze).
   - Camera2Module.enablePreviewAsThumbnail() -> false (prevents black/glitched thumbnails).
   - Note: public isParallelSessionEnable() is kept INTACT to preserve camera session lifecycle and prevent crashes!
2. Portrait Mode:
   - Camera2Module.updatePortraitBokehRole() -> role 0x3f (role 63, single-sensor bokeh) while preserving zoom manager, aperture, and LZ5/H;->s2 state.
   - Z5/Z.smali -> bypass DepthReader (DEPTH16 / 0x20363159) stream addition in both W1 and Y1 to prevent Qualcomm CamX rejecting the stream and throwing 'couldn't connect to camera'.
   - Z5/L0.smali -> null checks on ImageReader p (depth) and d (bokeh) to avoid NullPointerException on capture request target setup.
   - H3/f.smali (Portrait ShotTypeHandler) -> shotType 0 (normal still capture) to save photos immediately without hanging.
3. Night Mode:
   - NightModule.getRawCallbackType() -> 0 (prevents unsupported RAW burst stream crash).
   - NightModule.getGraphDescriptorBean() -> standard session operating mode (super.getGraphDescriptorBean()).
   - NightModule.isParallelSessionEnable() -> false.
   - H3/i.smali (Night ShotTypeHandler) -> shotType 0 (clean night capture without HAL error 4 crash).
4. Watermark & Saving:
   - Fixes NullPointerException in D5/c.smali when CaptureResult is null with watermark active.
   - Caller null check on ICustomCaptureResult before toTotalCaptureResult conversion.
5. Documents:
   - DocModuleEntry.support() -> false (keeps Document mode disabled).
6. Ultra HD (108MP):
   - Preserved tripartite downscale bypass and PixelModule parallel bypass.
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
OUT_APK_V15 = "/serverhive5/wandererdev/MiuiCamera_breeze_fixed_v15_640003209.apk"

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
        # 1. Camera2Module: Photo mode parallel bypass & Portrait role 63
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

        old_bokeh_role = """    :cond_69
    const/16 v1, 0x3d

    :goto_6b"""
        new_bokeh_role = """    :cond_69
    const/16 v1, 0x3f

    :goto_6b"""
        patch_file(c2m_smali, old_bokeh_role, new_bokeh_role, "Camera2Module.updatePortraitBokehRole -> role 0x3f (63)")

        # ---------------------------------------------------------------------
        # 2. Z5/Z.smali: Portrait DepthReader (DEPTH16) bypass (W1 and Y1)
        # ---------------------------------------------------------------------
        z_smali = os.path.join(smali_dir, "Z5/Z.smali")
        # Block 1 in W1
        old_b1 = """    invoke-static {v10, v2}, Lcom/android/camera/log/LogK;->i(Ljava/lang/String;Ljava/lang/String;)V

    :cond_337
    iget-object v2, v0, LZ5/Z;->F:LZ5/G;"""
        new_b1 = """    invoke-static {v10, v2}, Lcom/android/camera/log/LogK;->i(Ljava/lang/String;Ljava/lang/String;)V

    :cond_337
    goto :cond_37e

    iget-object v2, v0, LZ5/Z;->F:LZ5/G;"""
        patch_file(z_smali, old_b1, new_b1, "Z5/Z.smali Block 1 (DepthReader cond_337 -> cond_37e)")

        # Block 2 in Y1
        old_b2 = """    :cond_4f
    iget-object v0, p0, LZ5/Z;->F:LZ5/G;

    iget-object v0, v0, LZ5/G;->a:LZ5/H;

    iget v1, v0, LZ5/H;->V0:I

    const/4 v5, 0x2

    if-eq v1, v5, :cond_5b

    const/4 v6, -0x3

    if-ne v1, v6, :cond_fd

    :cond_5b"""
        new_b2 = """    :cond_4f
    goto :cond_fd

    iget-object v0, p0, LZ5/Z;->F:LZ5/G;

    iget-object v0, v0, LZ5/G;->a:LZ5/H;

    iget v1, v0, LZ5/H;->V0:I

    const/4 v5, 0x2

    if-eq v1, v5, :cond_5b

    const/4 v6, -0x3

    if-ne v1, v6, :cond_fd

    :cond_5b"""
        patch_file(z_smali, old_b2, new_b2, "Z5/Z.smali Block 2 (DepthReader cond_4f -> cond_fd)")

        # ---------------------------------------------------------------------
        # 3. Z5/L0.smali: Null checks on ImageReader p and d
        # ---------------------------------------------------------------------
        l0_smali = os.path.join(smali_dir, "Z5/L0.smali")
        with open(l0_smali) as f:
            l0_lines = f.readlines()
        target_p = "".join(l0_lines[59:83])
        repl_p = """    iget-object v3, v2, LZ5/G0;->p:Landroid/media/ImageReader;

    if-eqz v3, :cond_skip_p

    invoke-virtual {v3}, Landroid/media/ImageReader;->getSurface()Landroid/view/Surface;

    move-result-object v3

    invoke-virtual {v1, v3}, Landroid/hardware/camera2/CaptureRequest$Builder;->addTarget(Landroid/view/Surface;)V

    new-instance v6, Ljava/lang/StringBuilder;

    invoke-direct {v6, v5}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    invoke-static {v3}, Ljc/J;->a(Landroid/view/Surface;)Ljava/lang/String;

    move-result-object v3

    invoke-virtual {v6, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v6}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v3

    invoke-static {v4, v3}, Lcom/android/camera/log/LogK;->d(Ljava/lang/String;Ljava/lang/String;)V

    :cond_skip_p
"""
        patch_file(l0_smali, target_p, repl_p, "Z5/L0.smali null check on ImageReader p")

        target_d = "".join(l0_lines[83:107])
        repl_d = """    iget-object v3, v2, LZ5/G0;->d:Landroid/media/ImageReader;

    if-eqz v3, :cond_skip_d

    invoke-virtual {v3}, Landroid/media/ImageReader;->getSurface()Landroid/view/Surface;

    move-result-object v3

    invoke-virtual {v1, v3}, Landroid/hardware/camera2/CaptureRequest$Builder;->addTarget(Landroid/view/Surface;)V

    new-instance v6, Ljava/lang/StringBuilder;

    invoke-direct {v6, v5}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    invoke-static {v3}, Ljc/J;->a(Landroid/view/Surface;)Ljava/lang/String;

    move-result-object v3

    invoke-virtual {v6, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v6}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v3

    invoke-static {v4, v3}, Lcom/android/camera/log/LogK;->d(Ljava/lang/String;Ljava/lang/String;)V

    :cond_skip_d
"""
        patch_file(l0_smali, target_d, repl_d, "Z5/L0.smali null check on ImageReader d")

        # ---------------------------------------------------------------------
        # 4. H3/f.smali: Portrait ShotTypeHandler -> shotType 0
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
        # 5. H3/i.smali: Night ShotTypeHandler -> shotType 0
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
        # 6. NightModule.smali: raw callback, graph descriptor, parallel bypass
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

    const/4 v0, 0x0

    return v0
.end method""",
            "NightModule.isParallelSessionEnable -> false"
        )

        # ---------------------------------------------------------------------
        # 7. D5/c.smali: Watermark NPE Fix
        # ---------------------------------------------------------------------
        d5c_smali = os.path.join(smali_dir, "D5/c.smali")
        with open(d5c_smali) as f:
            d5c_content = f.read()

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
        # 8. DocModuleEntry.smali: Disable Document mode
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
        # 9. Reassemble classes2.dex
        # ---------------------------------------------------------------------
        new_dex2 = os.path.join(td, "classes2_new.dex")
        print("[*] Reassembling classes2.dex with smali...")
        subprocess.run(["smali", "a", smali_dir, "-o", new_dex2], check=True)

        # ---------------------------------------------------------------------
        # 10. Pack into APK, bump versionCode 640003207 -> 640003209
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
                        # Bump 640003207 (87ac2526) -> 640003209 (89ac2526)
                        if b"\x87\xac\x25\x26" in data:
                            data = data.replace(b"\x87\xac\x25\x26", b"\x89\xac\x25\x26", 1)
                            print("[+] Bumped versionCode to 640003209 in AndroidManifest.xml")
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
            "--out", OUT_APK_V15,
            aligned_apk
        ], check=True)

        print("[*] Verifying output APK...")
        subprocess.run(["apksigner", "verify", "-v", OUT_APK_V15], check=True)
        print(f"[+] SUCCESS! Created {OUT_APK_V15}")

        # Also copy to repo proprietary location
        print(f"[*] Updating repo vendor APK: {REPO_APK}")
        shutil.copy2(OUT_APK_V15, REPO_APK)
        print(f"[+] Successfully copied to {REPO_APK}")

if __name__ == "__main__":
    main()
