#!/usr/bin/env python3
import struct
import zlib
import hashlib
import sys
import os
import re

APK_PATH = "/home/wtf/Projects/hyperos_camera_breeze/proprietary/product/priv-app/MiuiCamera/MiuiCamera.apk"
OUTPUT_APK = "/tmp/MiuiCamera_patched_final.apk"

def patch():
    print(f"Reading original APK: {APK_PATH}")
    with open(APK_PATH, "rb") as f:
        apk_data = bytearray(f.read())

    # ==========================================
    # Patch classes2.dex
    # ==========================================
    dex2_local_hdr = 23153120
    assert apk_data[dex2_local_hdr:dex2_local_hdr+4] == b"PK\x03\x04"
    dex2_data_off = 23153168
    dex2_size = 10348448

    dex2 = bytearray(apk_data[dex2_data_off:dex2_data_off+dex2_size])
    assert len(dex2) == dex2_size
    assert dex2[:4] == b"dex\n"

    print("Checking original instructions in classes2.dex...")
    assert dex2[0x4710a0:0x4710a2] == bytes.fromhex("3808")
    assert dex2[0x6a715a:0x6a715c] == bytes.fromhex("3806")
    assert dex2[0x6a5f82:0x6a5f86] == bytes.fromhex("db020202")
    assert dex2[0x6a5f8e:0x6a5f92] == bytes.fromhex("db050502")

    print("Applying patches to classes2.dex...")
    # 1. Replace all calls to LA/v3;->c (0x017f) with LA/v3;->f (0x0182)
    c_calls = [m.start() for m in re.finditer(b"\x71\x20[\x7f][\x01]", dex2)]
    print(f"Found {len(c_calls)} calls to LA/v3;->c, redirecting to LA/v3;->f (full size)...")
    for m in c_calls:
        dex2[m+2:m+4] = struct.pack("<H", 0x0182)

    # 2. Bypass tripartite downscale in Camera2Module
    dex2[0x4710a0:0x4710a2] = bytes.fromhex("2900")

    # 3. Bypass div-float in Lv3/m;->p
    dex2[0x6a715a:0x6a715c] = bytes.fromhex("2900")

    # 4. Bypass shr-int in Lv3/l;->m
    dex2[0x6a5f82:0x6a5f86] = bytes.fromhex("00000000")
    dex2[0x6a5f8e:0x6a5f92] = bytes.fromhex("00000000")

    print("Recalculating classes2.dex checksums...")
    new2_sha1 = hashlib.sha1(dex2[32:]).digest()
    dex2[12:32] = new2_sha1
    new2_adler = zlib.adler32(dex2[12:]) & 0xffffffff
    dex2[8:12] = struct.pack("<I", new2_adler)

    new2_crc = zlib.crc32(dex2) & 0xffffffff
    print(f"New classes2.dex CRC32: 0x{new2_crc:08x}")

    apk_data[dex2_data_off:dex2_data_off+dex2_size] = dex2
    apk_data[dex2_local_hdr+14:dex2_local_hdr+18] = struct.pack("<I", new2_crc)
    apk_data[184984143:184984147] = struct.pack("<I", new2_crc)

    with open(OUTPUT_APK, "wb") as f:
        f.write(apk_data)

    print(f"Wrote {OUTPUT_APK} successfully ({len(apk_data)} bytes).")

    import zipfile
    with zipfile.ZipFile(OUTPUT_APK, "r") as z:
        assert z.testzip() is None, "ZIP verification failed!"
    print("ALL CHECKS PASSED!")

if __name__ == "__main__":
    patch()
