#!/usr/bin/env python3
"""
patch_security_checks.py: Patches MiuiCamera.apk to eliminate:
1. "permission are limited, please contact r and d" Toast:
   - In LA/t1;->run()V, MIVILutSaver checks if Test.txt can be written to
     /mnt/vendor/persist/camera/ or /data/vendor/camera/.
     On AOSP, this fails due to file permissions / SELinux, sending message 13 (0xd)
     to ActivityBase$c which displays string 0x7f140af2 ("权限受限，请联系研发" / "permission are limited, please contact r and d").
     Fix: Force LA/t1;->run()V to return-void immediately at offset 0x5129f6.
     Also neuter message 13 handler in ActivityBase$c at offset 0x80c05c.

2. "on APK version error, finish activity after 3 seconds" Dialog:
   - CameraOptManager.yqLgqUqPBVGfYvYhJ check failure sending message 11 (0xb).
     Fix: Neuter message 11 handler in ActivityBase$c at offset 0x80c0ae.
"""

import hashlib
import os
import struct
import zipfile
import zlib

APK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proprietary/product/priv-app/MiuiCamera/MiuiCamera.apk")

def main():
    print(f"[+] Loading {APK_PATH}...")
    with open(APK_PATH, "rb") as f:
        apk_data = bytearray(f.read())

    with zipfile.ZipFile(APK_PATH, "r") as z:
        info = z.getinfo("classes.dex")
        hdr_off = info.header_offset
        assert apk_data[hdr_off:hdr_off+4] == b"PK\x03\x04", "Local header signature mismatch!"
        fn_len = struct.unpack("<H", apk_data[hdr_off+26:hdr_off+28])[0]
        extra_len = struct.unpack("<H", apk_data[hdr_off+28:hdr_off+30])[0]
        data_off = hdr_off + 30 + fn_len + extra_len
        dex_size = info.file_size

    print(f"[+] Found classes.dex at local hdr 0x{hdr_off:x}, data 0x{data_off:x}, size {dex_size}")
    dex = bytearray(apk_data[data_off:data_off+dex_size])
    assert dex[:4] == b"dex\n", "DEX magic mismatch!"

    # 1. Patch LA/t1;->run()V: bypass MIVILutSaver persist test and CameraOptManager check
    orig_t1 = dex[0x5129f6:0x5129fa]
    if orig_t1 == bytes.fromhex("62043ba5"):
        print("[+] Patching LA/t1;->run()V -> return-void at 0x5129f6...")
        dex[0x5129f6:0x5129fa] = bytes.fromhex("0e000000")
    elif orig_t1 == bytes.fromhex("0e000000"):
        print("[*] LA/t1;->run()V already patched.")
    else:
        raise ValueError(f"Unexpected bytes at 0x5129f6: {orig_t1.hex()}")

    # 2. Patch ActivityBase$c Message 13 (0xd) handler: remove "permission are limited" toast
    orig_msg13 = dex[0x80c05c:0x80c060]
    if orig_msg13 == bytes.fromhex("140df20a"):
        print("[+] Patching ActivityBase$c message 13 handler -> return-void at 0x80c05c...")
        dex[0x80c05c:0x80c06a] = bytes.fromhex("0e00000000000000000000000e00")
    elif orig_msg13 == bytes.fromhex("0e000000"):
        print("[*] ActivityBase$c message 13 handler already patched.")
    else:
        raise ValueError(f"Unexpected bytes at 0x80c05c: {orig_msg13.hex()}")

    # 3. Patch ActivityBase$c Message 11 (0xb) handler: remove "on APK version error" dialog
    orig_msg11 = dex[0x80c0ae:0x80c0b2]
    if orig_msg11 == bytes.fromhex("220d9424"):
        print("[+] Patching ActivityBase$c message 11 handler -> return-void at 0x80c0ae...")
        dex[0x80c0ae:0x80c0b2] = bytes.fromhex("0e000000")
    elif orig_msg11 == bytes.fromhex("0e000000"):
        print("[*] ActivityBase$c message 11 handler already patched.")
    else:
        raise ValueError(f"Unexpected bytes at 0x80c0ae: {orig_msg11.hex()}")

    # Recalculate DEX checksums
    print("[+] Recalculating SHA1, Adler32, and CRC32 for classes.dex...")
    new_sha1 = hashlib.sha1(dex[32:]).digest()
    dex[12:32] = new_sha1
    new_adler = zlib.adler32(dex[12:]) & 0xffffffff
    dex[8:12] = struct.pack("<I", new_adler)
    new_crc = zlib.crc32(dex) & 0xffffffff
    print(f"[+] New classes.dex CRC32: 0x{new_crc:08x}")

    # Write patched DEX back into APK buffer
    apk_data[data_off:data_off+dex_size] = dex

    # Update local file header CRC32
    apk_data[hdr_off+14:hdr_off+18] = struct.pack("<I", new_crc)

    # Find and update central directory entry CRC32
    eocd_pos = apk_data.rfind(b"PK\x05\x06")
    assert eocd_pos != -1
    cd_size = struct.unpack("<I", apk_data[eocd_pos+12:eocd_pos+16])[0]
    cd_off = struct.unpack("<I", apk_data[eocd_pos+16:eocd_pos+20])[0]

    p = cd_off
    found_cd = False
    while p < cd_off + cd_size:
        assert apk_data[p:p+4] == b"PK\x01\x02"
        fn_l = struct.unpack("<H", apk_data[p+28:p+30])[0]
        ex_l = struct.unpack("<H", apk_data[p+30:p+32])[0]
        cm_l = struct.unpack("<H", apk_data[p+32:p+34])[0]
        fn = apk_data[p+46:p+46+fn_l].decode("ascii", errors="ignore")
        if fn == "classes.dex":
            apk_data[p+16:p+20] = struct.pack("<I", new_crc)
            found_cd = True
            print(f"[+] Updated central directory entry CRC32 at 0x{p+16:x}")
            break
        p += 46 + fn_l + ex_l + cm_l

    assert found_cd, "Failed to find classes.dex in central directory!"

    with open(APK_PATH, "wb") as f:
        f.write(apk_data)

    print(f"[+] Successfully wrote {len(apk_data)} bytes to {APK_PATH}.")

    # Verify zip integrity
    with zipfile.ZipFile(APK_PATH, "r") as z:
        bad_file = z.testzip()
        assert bad_file is None, f"ZIP verification failed on {bad_file}!"
    print("[+] ZIP verification passed cleanly! All CRC32 checksums match.")

if __name__ == "__main__":
    main()
