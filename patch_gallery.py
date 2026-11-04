#!/usr/bin/env python3
"""
patch_gallery.py: Applies third-party gallery support to MiuiCamera.apk for breeze.
Ported from WibuRachSapphireTree/device_xiaomi_miuicamera-sapphire patch 0001:
- A/Y2.smali: Remove hardcoded 'setPackage("com.miui.gallery")' on REVIEW intent
- com/android/camera/Camera.smali: Route empty/direct gallery launch via APP_GALLERY category + FLAG_ACTIVITY_NEW_TASK
"""

import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APK_PATH = os.path.join(SCRIPT_DIR, "proprietary/product/priv-app/MiuiCamera/MiuiCamera.apk")

def main():
    if not os.path.isfile(APK_PATH):
        print(f"Error: {APK_PATH} not found!")
        sys.exit(1)

    print(f"[+] Applying gallery patch to {APK_PATH}...")
    with tempfile.TemporaryDirectory() as tmpdir:
        classes_dex = os.path.join(tmpdir, "classes.dex")
        out_smali = os.path.join(tmpdir, "smali")
        patched_dex = os.path.join(tmpdir, "classes_patched.dex")
        repacked_apk = os.path.join(tmpdir, "repacked.apk")
        aligned_apk = os.path.join(tmpdir, "aligned.apk")

        # 1. Extract classes.dex
        with zipfile.ZipFile(APK_PATH, "r") as z:
            z.extract("classes.dex", tmpdir)

        # 2. Baksmali classes.dex
        print("[+] Disassembling classes.dex...")
        subprocess.run(["baksmali", "d", classes_dex, "-o", out_smali], check=True)

        # 3. Patch A/Y2.smali
        y2_file = os.path.join(out_smali, "A/Y2.smali")
        with open(y2_file, "r") as f:
            y2_content = f.read()

        target_y2 = """    :goto_45
    const-string p2, "com.miui.gallery"

    invoke-virtual {v1, p2}, Landroid/content/Intent;->setPackage(Ljava/lang/String;)Landroid/content/Intent;

    const-string p2, "from_MiuiCamera" """

        replace_y2 = """    :goto_45
    const-string p2, "from_MiuiCamera" """

        if target_y2.strip() in y2_content:
            y2_content = y2_content.replace(target_y2.strip(), replace_y2.strip())
            with open(y2_file, "w") as f:
                f.write(y2_content)
            print("[+] Patched A/Y2.smali: removed setPackage(com.miui.gallery)")
        else:
            print("[*] A/Y2.smali already patched or pattern not found.")

        # 4. Patch Camera.smali
        camera_file = os.path.join(out_smali, "com/android/camera/Camera.smali")
        with open(camera_file, "r") as f:
            cam_content = f.read()

        target_cam = """    :try_start_2f4
    new-instance p0, Landroid/content/Intent;

    const-string v0, "android.intent.action.MAIN"

    invoke-direct {p0, v0}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V

    invoke-virtual {p0, v2}, Landroid/content/Intent;->setPackage(Ljava/lang/String;)Landroid/content/Intent;

    invoke-virtual {v4, p0}, Landroid/app/Activity;->startActivity(Landroid/content/Intent;)V"""

        replace_cam = """    :try_start_2f4
    new-instance p0, Landroid/content/Intent;

    const-string v0, "android.intent.action.MAIN"

    invoke-direct {p0, v0}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V

    const-string v2, "android.intent.category.APP_GALLERY"

    invoke-virtual {p0, v2}, Landroid/content/Intent;->addCategory(Ljava/lang/String;)Landroid/content/Intent;

    const/high16 v2, 0x10000000

    invoke-virtual {p0, v2}, Landroid/content/Intent;->addFlags(I)Landroid/content/Intent;

    invoke-virtual {v4, p0}, Landroid/app/Activity;->startActivity(Landroid/content/Intent;)V"""

        if target_cam in cam_content:
            cam_content = cam_content.replace(target_cam, replace_cam)
            with open(camera_file, "w") as f:
                f.write(cam_content)
            print("[+] Patched Camera.smali: added APP_GALLERY and FLAG_ACTIVITY_NEW_TASK")
        else:
            print("[*] Camera.smali already patched or pattern not found.")

        # 5. Assemble classes_patched.dex
        print("[+] Assembling classes_patched.dex...")
        subprocess.run(["smali", "a", out_smali, "-o", patched_dex], check=True)

        # 6. Repack into APK
        print("[+] Repacking APK with patched classes.dex...")
        with zipfile.ZipFile(APK_PATH, "r") as zin, zipfile.ZipFile(repacked_apk, "w") as zout:
            for item in zin.infolist():
                if item.filename == "classes.dex":
                    with open(patched_dex, "rb") as f:
                        dex_bytes = f.read()
                    zout.writestr(item.filename, dex_bytes, compress_type=zipfile.ZIP_STORED)
                else:
                    zout.writestr(item, zin.read(item.filename))

        # 7. Zipalign
        print("[+] Aligning APK with zipalign -p -f 4...")
        subprocess.run(["zipalign", "-p", "-f", "4", repacked_apk, aligned_apk], check=True)
        subprocess.run(["zipalign", "-c", "-v", "4", aligned_apk], check=True, stdout=subprocess.DEVNULL)

        # 8. Overwrite APK
        shutil.copy2(aligned_apk, APK_PATH)
        print(f"[+] Successfully wrote and aligned {APK_PATH} ({os.path.getsize(APK_PATH)} bytes).")

    # Verify zip integrity
    with zipfile.ZipFile(APK_PATH, "r") as z:
        bad = z.testzip()
        assert bad is None, f"Zip integrity check failed: {bad}"
    print("[+] All verification checks passed cleanly!")

if __name__ == "__main__":
    main()
