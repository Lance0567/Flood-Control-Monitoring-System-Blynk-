from picamera2 import Picamera2, Preview
import time

picam2 = Picamera2()

# Start a GPU-accelerated preview window (same as rpicam-hello)
picam2.start_preview(Preview.QTGL)
picam2.start()

print("📷 Camera running... Press Ctrl+C to stop.")

try:
    while True:
        time.sleep(1)  # Keeps the script alive without using much CPU
except KeyboardInterrupt:
    print("\n🛑 Stopping camera...")
    picam2.stop_preview()
    picam2.close()
