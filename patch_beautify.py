import struct
import zlib
import hashlib
import zipfile

APK_PATH = "/home/wtf/Projects/hyperos_camera_breeze/proprietary/product/priv-app/MiuiCamera/MiuiCamera.apk"
OUTPUT_APK = "/tmp/MiuiCamera_beautify_test.apk"

with open(APK_PATH, "rb") as f:
    apk_data = bytearray(f.read())

# ==========================================
# 1. Patch classes.dex
# ==========================================
dex1_local_hdr = 13537629
dex1_data_off = 13537676
dex1_size = 9615444

dex1 = bytearray(apk_data[dex1_data_off:dex1_data_off+dex1_size])
assert len(dex1) == dex1_size
assert dex1[:4] == b"dex\n"

# Verify originals in classes.dex
assert dex1[0x5458dc:0x5458dc+4] == bytes.fromhex("1a018c13"), f"Mismatch at 0x5458dc: {dex1[0x5458dc:0x5458dc+4].hex()}"
assert dex1[0x546b12:0x546b12+4] == bytes.fromhex("380f4f00"), f"Mismatch at 0x546b12: {dex1[0x546b12:0x546b12+4].hex()}"
assert dex1[0x546b46:0x546b46+4] == bytes.fromhex("380f0e00"), f"Mismatch at 0x546b46: {dex1[0x546b46:0x546b46+4].hex()}"

print("Patching classes.dex...")
dex1[0x5458dc:0x5458dc+4] = bytes.fromhex("1a010714") # const-string v1, "2"
dex1[0x546b12:0x546b12+4] = bytes.fromhex("284f0000") # goto 04fc
dex1[0x546b46:0x546b46+4] = bytes.fromhex("280e0000") # goto 04d5

# Recalculate checksums for classes.dex
new1_sha1 = hashlib.sha1(dex1[32:]).digest()
dex1[12:32] = new1_sha1
new1_adler = zlib.adler32(dex1[12:]) & 0xffffffff
dex1[8:12] = struct.pack("<I", new1_adler)
new1_crc = zlib.crc32(dex1) & 0xffffffff
print(f"New classes.dex CRC32: 0x{new1_crc:08x}")

apk_data[dex1_data_off:dex1_data_off+dex1_size] = dex1
apk_data[dex1_local_hdr+14:dex1_local_hdr+18] = struct.pack("<I", new1_crc)
apk_data[184984080:184984084] = struct.pack("<I", new1_crc)

# ==========================================
# 2. Patch classes2.dex
# ==========================================
dex2_local_hdr = 23153120
dex2_data_off = 23153168
dex2_size = 10348448

dex2 = bytearray(apk_data[dex2_data_off:dex2_data_off+dex2_size])
assert len(dex2) == dex2_size
assert dex2[:4] == b"dex\n"

# Verify original in classes2.dex
assert dex2[0x37df04:0x37df04+4] == bytes.fromhex("380b0700"), f"Mismatch at 0x37df04: {dex2[0x37df04:0x37df04+4].hex()}"

print("Patching classes2.dex...")
dex2[0x37df04:0x37df04+4] = bytes.fromhex("28050000") # goto 01d1 (skip throw)

# Recalculate checksums for classes2.dex
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

print(f"Wrote {OUTPUT_APK} ({len(apk_data)} bytes)")

with zipfile.ZipFile(OUTPUT_APK, "r") as z:
    assert z.testzip() is None, "ZIP verification failed!"
print("ZIP VERIFIED SUCCESSFULLY!")

