#!/usr/bin/env python3
"""
build_patched_apk.py
Applies all fixes to MiuiCamera.apk for breeze (Project Infinity-X):
1. Fix Leica Profile Mismatch: Reset default filterId from 66048 (0x10200) to 0 (FILTER_NONE) in classes.dex.
2. Fix AWB Drift on Capture: Lock AE and AWB during snapshot request in classes2.dex (Z5/g0.smali).
3. Fix EIS Toggle: Add EIS top bar builder in classes2.dex (P1/d.smali) and settings checkbox (CameraCamcorderPreferenceFragment.smali).
4. Remove Document Mode: Remove 0xba from L()[I and return 0 in P() in classes4.dex.
5. Fix Device Watermark: Return index 2 (Redmi 13 5G) or index 3 (POCO M6 Plus 5G) dynamically in classes4.dex (G7/b.smali).
"""

import os
import shutil
import subprocess
import sys
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = "/serverhive5/wandererdev/infinityx"
APK_PATH = os.path.join(BASE_DIR, "proprietary/product/priv-app/MiuiCamera/MiuiCamera.apk")
WORK_DIR = os.path.join(BASE_DIR, "apk_work_dir")

ZIPALIGN_BIN = os.path.join(REPO_ROOT, "out/host/linux-x86/bin/zipalign")
APKSIGNER_BIN = os.path.join(REPO_ROOT, "out/host/linux-x86/bin/apksigner")
DEXDUMP_BIN = os.path.join(REPO_ROOT, "out/host/linux-x86/bin/dexdump")
LIB64_PATH = os.path.join(REPO_ROOT, "out/host/linux-x86/lib64")
KEY_PATH = os.path.join(REPO_ROOT, "vendor/infinity-priv/keys/platform.pk8")
CERT_PATH = os.path.join(REPO_ROOT, "vendor/infinity-priv/keys/platform.x509.pem")

ENV = os.environ.copy()
ENV["LD_LIBRARY_PATH"] = f"{LIB64_PATH}:{ENV.get('LD_LIBRARY_PATH', '')}"

def run_cmd(cmd, check=True):
    print(f"[CMD] {' '.join(cmd)}")
    res = subprocess.run(cmd, env=ENV, capture_output=True, text=True)
    if check and res.returncode != 0:
        print(f"Error executing command: {' '.join(cmd)}")
        print(f"STDOUT: {res.stdout}")
        print(f"STDERR: {res.stderr}")
        sys.exit(1)
    return res

def patch_file(path, target, replacement):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if replacement in content:
        print(f"[*] {os.path.basename(path)} already patched.")
        return
    if target not in content:
        raise ValueError(f"Target pattern not found in {path}:\n{target[:100]}...")
    content = content.replace(target, replacement, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[+] Patched {os.path.basename(path)}")

def main():
    if os.path.exists(WORK_DIR):
        shutil.rmtree(WORK_DIR)
    os.makedirs(WORK_DIR, exist_ok=True)

    print(f"[1] Extracting DEX files from {APK_PATH}...")
    with zipfile.ZipFile(APK_PATH, "r") as z:
        z.extract("classes.dex", WORK_DIR)
        z.extract("classes2.dex", WORK_DIR)
        z.extract("classes4.dex", WORK_DIR)

    # -------------------------------------------------------------
    # Disassemble & Patch classes.dex
    # -------------------------------------------------------------
    print("[2] Disassembling classes.dex...")
    classes_out = os.path.join(WORK_DIR, "classes_out")
    run_cmd(["baksmali", "d", os.path.join(WORK_DIR, "classes.dex"), "-o", classes_out])

    # 1.1 Patch f0/J.smali: getDefaultValue -> always return "0"
    fj_path = os.path.join(classes_out, "f0/J.smali")
    target_fj = """.method public final getDefaultValue(I)Ljava/lang/String;
    .registers 2

    const/16 p0, 0xa2

    if-eq p1, p0, :cond_17

    const/16 p0, 0xa4

    if-eq p1, p0, :cond_17

    const/16 p0, 0xa9

    if-eq p1, p0, :cond_17

    const/16 p0, 0xb4

    if-eq p1, p0, :cond_17

    sget p0, LP0/c;->w:I

    invoke-static {p0}, Ljava/lang/String;->valueOf(I)Ljava/lang/String;

    move-result-object p0

    return-object p0

    :cond_17
    const/4 p0, 0x0

    invoke-static {p0}, Ljava/lang/String;->valueOf(I)Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method"""
    replace_fj = """.method public final getDefaultValue(I)Ljava/lang/String;
    .registers 2

    const/4 p0, 0x0

    invoke-static {p0}, Ljava/lang/String;->valueOf(I)Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method"""
    patch_file(fj_path, target_fj, replace_fj)

    # 1.2 Patch P0/c.smali: sput 0, LP0/c;->w:I
    pc_path = os.path.join(classes_out, "P0/c.smali")
    target_pc = """    const/4 v0, 0x1

    const/16 v2, 0x200

    invoke-static {v0, v2}, LP0/c;->b(II)I

    move-result v0

    sput v0, LP0/c;->w:I"""
    replace_pc = """    const/4 v0, 0x0

    sput v0, LP0/c;->w:I"""
    patch_file(pc_path, target_pc, replace_pc)

    print("[3] Reassembling classes.dex...")
    new_classes_dex = os.path.join(WORK_DIR, "new_classes.dex")
    run_cmd(["smali", "a", classes_out, "-o", new_classes_dex])
    run_cmd([DEXDUMP_BIN, "-c", new_classes_dex])
    print("[+] new_classes.dex verified cleanly!")

    # -------------------------------------------------------------
    # Disassemble & Patch classes2.dex
    # -------------------------------------------------------------
    print("[4] Disassembling classes2.dex...")
    classes2_out = os.path.join(WORK_DIR, "classes2_out")
    run_cmd(["baksmali", "d", os.path.join(WORK_DIR, "classes2.dex"), "-o", classes2_out])

    # 2.1 Patch Z5/g0.smali: Lock AE & AWB on capture request
    zg_path = os.path.join(classes2_out, "Z5/g0.smali")
    target_zg = """    move-result v10

    if-eqz v10, :cond_1c3

    sget-object v10, Ljava/lang/Boolean;->TRUE:Ljava/lang/Boolean;

    invoke-virtual {v10, v5}, Ljava/lang/Boolean;->equals(Ljava/lang/Object;)Z

    move-result v5

    if-eqz v5, :cond_1c3

    invoke-static {v1, v4}, LZ5/K;->a(Landroid/hardware/camera2/CaptureRequest$Builder;Z)V

    invoke-static {v1, v4}, LZ5/K;->f(Landroid/hardware/camera2/CaptureRequest$Builder;Z)V

    goto :goto_1c9

    :cond_1c3
    invoke-static {v1, v9}, LZ5/K;->a(Landroid/hardware/camera2/CaptureRequest$Builder;Z)V

    invoke-static {v1, v9}, LZ5/K;->f(Landroid/hardware/camera2/CaptureRequest$Builder;Z)V

    :cond_1c9
    :goto_1c9"""
    replace_zg = """    invoke-static {v1, v9}, LZ5/K;->a(Landroid/hardware/camera2/CaptureRequest$Builder;Z)V

    invoke-static {v1, v9}, LZ5/K;->f(Landroid/hardware/camera2/CaptureRequest$Builder;Z)V

    :cond_1c9"""
    patch_file(zg_path, target_zg, replace_zg)

    # 2.2 Patch P1/d.smali: Add EIS builder to Video Mode top bar
    pd_path = os.path.join(classes2_out, "P1/d.smali")
    target_pd = """    if-eqz p0, :cond_1ad

    sget-object p0, Lcom/android/camera2/compat/theme/custom/mm/top/TopConfigItemUtil;->INSTANCE:Lcom/android/camera2/compat/theme/custom/mm/top/TopConfigItemUtil;

    invoke-virtual {p0}, Lcom/android/camera2/compat/theme/custom/mm/top/TopConfigItemUtil;->getSettingItemBuilder()Lr2/e$a;

    move-result-object p0

    invoke-static {p0, p0, v0}, LA/K2;->i(Lr2/e$a;Lr2/e$a;Ljava/util/ArrayList;)V

    :cond_1ad
    return-object v0"""
    replace_pd = """    if-eqz p0, :cond_1ad

    sget-object p0, Lcom/android/camera2/compat/theme/custom/mm/top/TopConfigItemUtil;->INSTANCE:Lcom/android/camera2/compat/theme/custom/mm/top/TopConfigItemUtil;

    invoke-virtual {p0}, Lcom/android/camera2/compat/theme/custom/mm/top/TopConfigItemUtil;->getSettingItemBuilder()Lr2/e$a;

    move-result-object p0

    invoke-static {p0, p0, v0}, LA/K2;->i(Lr2/e$a;Lr2/e$a;Ljava/util/ArrayList;)V

    :cond_1ad
    sget-object p0, LG7/b$b;->a:LG7/b;

    iget-object p0, p0, LG7/b;->e:Lᙊᙆᙄᘇᙄᙀᘇᙍᙌᙟᙀᙊᙌᘇᙊᙆᙄᙄᙆᙇᘇᙪᙆᙄᙄᙆᙇ;

    invoke-virtual {p0}, Lᙊᙆᙄᘇᙄᙀᘇᙍᙌᙟᙀᙊᙌᘇᙊᙆᙄᙄᙆᙇᘇᙪᙆᙄᙄᙆᙇ;->e6()Z

    move-result p0

    if-eqz p0, :cond_eis

    sget-object p0, Lcom/android/camera2/compat/theme/custom/mm/top/TopConfigItemUtil;->INSTANCE:Lcom/android/camera2/compat/theme/custom/mm/top/TopConfigItemUtil;

    invoke-virtual {p0}, Lcom/android/camera2/compat/theme/custom/mm/top/TopConfigItemUtil;->getEisItemBuilder()Lr2/e$a;

    move-result-object p0

    invoke-static {p0, p0, v0}, LA/K2;->i(Lr2/e$a;Lr2/e$a;Ljava/util/ArrayList;)V

    :cond_eis
    return-object v0"""
    patch_file(pd_path, target_pd, replace_pd)

    # 2.3 Patch CameraCamcorderPreferenceFragment.smali: Add Video Stabilization to Settings menu
    cc_path = os.path.join(classes2_out, "com/android/camera/fragment/settings/CameraCamcorderPreferenceFragment.smali")
    target_cc = """    :cond_8b
    iget-object v4, p0, Lcom/android/camera/fragment/settings/BasePreferenceFragment;->x:Lu2/e;"""
    replace_cc = """    :cond_8b
    sget-object v4, LG7/b$b;->a:LG7/b;

    iget-object v4, v4, LG7/b;->e:Lᙊᙆᙄᘇᙄᙀᘇᙍᙌᙟᙀᙊᙌᘇᙊᙆᙄᙄᙆᙇᘇᙪᙆᙄᙄᙆᙇ;

    invoke-virtual {v4}, Lᙊᙆᙄᘇᙄᙀᘇᙍᙌᙟᙀᙊᙌᘇᙊᙆᙄᙄᙆᙇᘇᙪᙆᙄᙄᙆᙇ;->e6()Z

    move-result v4

    if-eqz v4, :cond_eis_setting

    const-string v6, "pref_camera_movie_solid_key"

    const/4 v7, 0x0

    const v8, 0x7f140ca5

    const/4 v9, -0x1

    move-object v4, p0

    move-object v5, v2

    invoke-virtual/range {v4 .. v9}, Lcom/android/camera/fragment/settings/BasePreferenceFragment;->Nb(Landroidx/preference/PreferenceGroup;Ljava/lang/String;ZII)Landroidx/preference/CheckBoxPreference;

    :cond_eis_setting
    iget-object v4, p0, Lcom/android/camera/fragment/settings/BasePreferenceFragment;->x:Lu2/e;"""
    patch_file(cc_path, target_cc, replace_cc)

    print("[5] Reassembling classes2.dex...")
    new_classes2_dex = os.path.join(WORK_DIR, "new_classes2.dex")
    run_cmd(["smali", "a", classes2_out, "-o", new_classes2_dex])
    run_cmd([DEXDUMP_BIN, "-c", new_classes2_dex])
    print("[+] new_classes2.dex verified cleanly!")

    # -------------------------------------------------------------
    # Disassemble & Patch classes4.dex
    # -------------------------------------------------------------
    print("[6] Disassembling classes4.dex...")
    classes4_out = os.path.join(WORK_DIR, "classes4_out")
    run_cmd(["baksmali", "d", os.path.join(WORK_DIR, "classes4.dex"), "-o", classes4_out])

    # 3.1 Patch breeze feature class: Remove Document Mode
    breeze_feat_path = os.path.join(classes4_out, "礯礣礡祢礡礥祢礨礩示礥礯礩祢礎社礩礩礶礩.smali")
    target_l = """.method public final L()[I
    .registers 1

    const/16 p0, 0x8

    new-array p0, p0, [I

    fill-array-data p0, :array_8

    return-object p0

    :array_8
    .array-data 4
        0xaf
        0xa2
        0xa3
        0xab
        0xad
        0xa9
        0xba
        0xfe
    .end array-data
.end method"""
    replace_l = """.method public final L()[I
    .registers 1

    const/4 p0, 0x7

    new-array p0, p0, [I

    fill-array-data p0, :array_8

    return-object p0

    :array_8
    .array-data 4
        0xaf
        0xa2
        0xa3
        0xab
        0xad
        0xa9
        0xfe
    .end array-data
.end method"""
    patch_file(breeze_feat_path, target_l, replace_l)

    target_p = """.method public final P()I
    .registers 1

    const/4 p0, 0x1

    return p0
.end method"""
    replace_p = """.method public final P()I
    .registers 1

    const/4 p0, 0x0

    return p0
.end method"""
    patch_file(breeze_feat_path, target_p, replace_p)

    # 3.2 Patch G7/b.smali: Watermark logic for breeze
    gb_path = os.path.join(classes4_out, "G7/b.smali")
    target_gb = """    :cond_138
    move v7, v1

    goto :goto_145"""
    replace_gb = """    :cond_138
    sget-object v7, Landroid/os/Build;->MODEL:Ljava/lang/String;

    const-string v8, "POCO"

    invoke-virtual {v7, v8}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v7

    if-nez v7, :cond_poco

    sget-object v7, Landroid/os/Build;->MODEL:Ljava/lang/String;

    const-string v8, "24066"

    invoke-virtual {v7, v8}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v7

    if-nez v7, :cond_poco

    sget-object v7, Landroid/os/Build;->PRODUCT:Ljava/lang/String;

    const-string v8, "_p"

    invoke-virtual {v7, v8}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v7

    if-eqz v7, :cond_check_13r

    :cond_poco
    const/4 v7, 0x3

    invoke-virtual {v6, v7}, Landroid/util/SparseArray;->get(I)Ljava/lang/Object;

    move-result-object v7

    check-cast v7, [Ljava/lang/String;

    if-eqz v7, :cond_check_13r

    return-object v7

    :cond_check_13r
    sget-object v7, Landroid/os/Build;->MODEL:Ljava/lang/String;

    const-string v8, "2406ERN9CC"

    invoke-virtual {v7, v8}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v7

    if-eqz v7, :cond_redmi13

    const/4 v7, 0x0

    invoke-virtual {v6, v7}, Landroid/util/SparseArray;->get(I)Ljava/lang/Object;

    move-result-object v7

    check-cast v7, [Ljava/lang/String;

    if-eqz v7, :cond_redmi13

    return-object v7

    :cond_redmi13
    const/4 v7, 0x2

    invoke-virtual {v6, v7}, Landroid/util/SparseArray;->get(I)Ljava/lang/Object;

    move-result-object v7

    check-cast v7, [Ljava/lang/String;

    if-eqz v7, :cond_redmi_default

    return-object v7

    :cond_redmi_default
    const/4 v7, 0x0

    invoke-virtual {v6, v7}, Landroid/util/SparseArray;->get(I)Ljava/lang/Object;

    move-result-object v7

    check-cast v7, [Ljava/lang/String;

    return-object v7"""
    patch_file(gb_path, target_gb, replace_gb)

    print("[7] Reassembling classes4.dex...")
    new_classes4_dex = os.path.join(WORK_DIR, "new_classes4.dex")
    run_cmd(["smali", "a", classes4_out, "-o", new_classes4_dex])
    run_cmd([DEXDUMP_BIN, "-c", new_classes4_dex])
    print("[+] new_classes4.dex verified cleanly!")

    # -------------------------------------------------------------
    # Repack into APK, Zipalign, and Sign
    # -------------------------------------------------------------
    print("[8] Repacking APK with new DEX files...")
    repack_apk = os.path.join(WORK_DIR, "MiuiCamera_repack.apk")
    with zipfile.ZipFile(APK_PATH, "r") as zin, zipfile.ZipFile(repack_apk, "w") as zout:
        for item in zin.infolist():
            if item.filename == "classes.dex":
                zout.writestr(item.filename, open(new_classes_dex, "rb").read(), compress_type=zipfile.ZIP_STORED)
            elif item.filename == "classes2.dex":
                zout.writestr(item.filename, open(new_classes2_dex, "rb").read(), compress_type=zipfile.ZIP_STORED)
            elif item.filename == "classes4.dex":
                zout.writestr(item.filename, open(new_classes4_dex, "rb").read(), compress_type=zipfile.ZIP_STORED)
            else:
                zout.writestr(item, zin.read(item.filename))

    print("[9] Aligning APK with zipalign -p -f 4...")
    aligned_apk = os.path.join(WORK_DIR, "MiuiCamera_aligned.apk")
    run_cmd([ZIPALIGN_BIN, "-p", "-f", "4", repack_apk, aligned_apk])
    run_cmd([ZIPALIGN_BIN, "-c", "-v", "4", aligned_apk])
    print("[+] Alignment verified!")

    print("[10] Signing APK with platform certificate...")
    signed_apk = os.path.join(WORK_DIR, "MiuiCamera_signed.apk")
    run_cmd([
        APKSIGNER_BIN, "sign",
        "--key", KEY_PATH,
        "--cert", CERT_PATH,
        "--out", signed_apk,
        aligned_apk
    ])
    run_cmd([APKSIGNER_BIN, "verify", signed_apk])
    print("[+] APK signature verified!")

    # Overwrite destination
    print(f"[11] Overwriting {APK_PATH}...")
    shutil.copy2(signed_apk, APK_PATH)
    print(f"[+] Successfully deployed new MiuiCamera.apk ({os.path.getsize(APK_PATH)} bytes)!")

    # Clean up workdir
    shutil.rmtree(WORK_DIR)
    print("[+] All patches applied and verified successfully!")

if __name__ == "__main__":
    main()
