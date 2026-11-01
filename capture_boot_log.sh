#!/usr/bin/env bash
set -e
LOG_FILE="/home/wtf/Downloads/boot_2min.log"
echo "==> Triggering adb reboot..."
adb reboot
echo "==> Waiting for device to attach..."
adb wait-for-device
echo "==> Device attached at $(date). Recording logcat for 120 seconds into $LOG_FILE..."
timeout 120s adb logcat -b all -v threadtime > "$LOG_FILE" || true
echo "==> 2-minute logcat recording complete at $(date)."
echo "==> Captured $(wc -l < "$LOG_FILE") lines."
ls -lh "$LOG_FILE"
