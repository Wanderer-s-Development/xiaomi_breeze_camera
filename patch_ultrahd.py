#!/usr/bin/env python3
"""
patch_ultrahd.py: Patches MiuiCamera.apk to eliminate Ultra HD (Mode 175) crashes on AOSP ROMs (Project Infinity-X / breeze).

Root Causes Fixed:
1. Qualcomm CamX HAL stream rejection:
   CamX HAL strictly validates streams against the sensor driver table.
   Tripartite downscaling in Camera2Module calculated an unsupported 2000x1500 YUV stream,
   triggering 'camxhaldevice.cpp:1860 CheckValidStreamConfig() Invalid streamStype: 0, format: 35 (2000 x 1500)'
   and crashing cameraserver.
   Fix: Skip the tripartite downscaling branch (goto/16 +0x008e at 0x4710a0 in classes2.dex)
   so the module directly requests valid native streams (4000x3000 / 12000x9000).

2. Offline MIVI parallel queue hang / crash:
   Xiaomi's MIVI parallel processing daemon is not running on AOSP.
   Mode 175 uses Qualcomm ISP hardware remosaic and in-process memcpy (superhdsnapshot.json),
   not the offline MIVI queue.
   Fix: Force PixelModule.isParallelSessionEnable() -> false at 0x360144 in classes2.dex.
"""

import struct
import zlib
import hashlib
import zipfile
import sys
import os

APK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proprietary/product/priv-app/MiuiCamera/MiuiCamera.apk")

def main():
    print(f"[+] Loading {APK_PATH}...")
    with open(APK_PATH, "rb") as f:
        apk_data = bytearray(f.read())

    # Locate classes2.dex within uncompressed / stored zip
    dex2_local_hdr = 23153120
    assert apk_data[dex2_local_hdr:dex2_local_hdr+4] == b"PK\x03\x04", "Local header signature mismatch!"
    dex2_data_off = 23153168
    dex2_size = 10348448

    dex2 = bytearray(apk_data[dex2_data_off:dex2_data_off+dex2_size])
    assert len(dex2) == dex2_size, f"Size mismatch: {len(dex2)} != {dex2_size}"
    assert dex2[:4] == b"dex\n", "DEX magic mismatch!"

    # 1. Patch PixelModule.isParallelSessionEnable -> return false
    # Original: 71 00 44 11 00 00 0a 00 (invoke-super {p0}, BaseModule;->isParallelSessionEnable()Z; move-result v0; return v0)
    # Patched:  12 00 0f 00 00 00 00 00 (const/4 v0, 0; return v0; nop; nop)
    orig_parallel = dex2[0x360144:0x360144+8]
    if orig_parallel == bytes.fromhex("7100441100000a00"):
        print("[+] Patching PixelModule.isParallelSessionEnable -> return false...")
        dex2[0x360144:0x360144+8] = bytes.fromhex("12000f0000000000")
    elif orig_parallel == bytes.fromhex("12000f0000000000"):
        print("[*] PixelModule.isParallelSessionEnable is already patched.")
    else:
        raise ValueError(f"Unexpected bytes at 0x360144: {orig_parallel.hex()}")

    # 2. Patch Camera2Module.updatePictureAndPreviewSize -> goto/16 +0x008e
    # Original: 38 08 8e 00 (if-eqz v8, +0x008e)
    # Patched:  29 00 8e 00 (goto/16 +0x008e)
    orig_downscale = dex2[0x4710a0:0x4710a0+4]
    if orig_downscale == bytes.fromhex("38088e00"):
        print("[+] Patching Camera2Module.updatePictureAndPreviewSize -> goto/16 +0x008e...")
        dex2[0x4710a0:0x4710a0+4] = bytes.fromhex("29008e00")
    elif orig_downscale == bytes.fromhex("29008e00"):
        print("[*] Camera2Module tripartite downscale bypass is already patched.")
    else:
        raise ValueError(f"Unexpected bytes at 0x4710a0: {orig_downscale.hex()}")

    # Recalculate checksums for classes2.dex
    print("[+] Recalculating SHA1, Adler32, and CRC32 checksums...")
    new2_sha1 = hashlib.sha1(dex2[32:]).digest()
    dex2[12:32] = new2_sha1
    new2_adler = zlib.adler32(dex2[12:]) & 0xffffffff
    dex2[8:12] = struct.pack("<I", new2_adler)
    new2_crc = zlib.crc32(dex2) & 0xffffffff
    print(f"[+] New classes2.dex CRC32: 0x{new2_crc:08x}")

    # Write patched DEX back into APK buffer
    apk_data[dex2_data_off:dex2_data_off+dex2_size] = dex2
    # Update local file header CRC32
    apk_data[dex2_local_hdr+14:dex2_local_hdr+18] = struct.pack("<I", new2_crc)
    # Update central directory CRC32
    apk_data[184984143:184984147] = struct.pack("<I", new2_crc)

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
