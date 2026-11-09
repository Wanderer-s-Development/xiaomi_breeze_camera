#!/usr/bin/env python3
"""
patch_uv_swap.py: Fixes the inverted color / blue filter defect in Photo (Mode 163),
Portrait (Mode 171), and Night (Mode 173) on Project Infinity-X (Android 17 / breeze).

Root Cause:
In AOSP's ImageReader implementation for Qualcomm NV21_ZSL / YCrCb_420_SP:
- plane[0] = Y (starts at offset +0)
- plane[1] = U / Cb (starts at offset +1)
- plane[2] = V / Cr (starts at offset +0)

Xiaomi's JNI helper FrameDataUtil::getMiImageList hardcoded fetching plane[1] (mov w2, #0x1)
as the chroma plane pointer (pAddr[1]). Because plane[1] points to U instead of the NV21 buffer base (V),
Xiaomi's post-processing plugins (morphohdr, mibokeh, superlowlight via libmialgoengine)
read every chroma byte offset by 1, inverting U <-> V (swapping Red and Blue).
This causes red/warm skin tones to turn bright cyan/blue and blue objects to turn orange.

Fix:
Change `mov w2, #0x1` (0x52800022) -> `mov w2, #0x2` (0x52800042) to fetch plane[2] (Cr at offset +0) in:
- libcamera_mianode_jni.xiaomi.so at offset 0xf3c8
- libcamera_algoup_jni.xiaomi.so at offset 0xc218
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGETS = [
    (os.path.join(BASE_DIR, "proprietary/system_ext/lib64/libcamera_mianode_jni.xiaomi.so"), 0xf3c8),
    (os.path.join(BASE_DIR, "proprietary/system_ext/lib64/libcamera_algoup_jni.xiaomi.so"), 0xc218),
]

OP_ORIG = bytes.fromhex("22008052")  # mov w2, #1
OP_FIX  = bytes.fromhex("42008052")  # mov w2, #2

def main():
    for path, off in TARGETS:
        if not os.path.exists(path):
            print(f"Error: {path} not found!")
            sys.exit(1)
        with open(path, "rb") as f:
            data = bytearray(f.read())
        curr = data[off:off+4]
        if curr == OP_ORIG:
            data[off:off+4] = OP_FIX
            with open(path, "wb") as f:
                f.write(data)
            print(f"[+] Successfully patched {os.path.basename(path)} at 0x{off:x}: mov w2, #1 -> mov w2, #2")
        elif curr == OP_FIX:
            print(f"[*] {os.path.basename(path)} at 0x{off:x} is already patched (mov w2, #2).")
        else:
            raise ValueError(f"Unexpected bytes at 0x{off:x} in {path}: {curr.hex()}")

if __name__ == "__main__":
    main()
