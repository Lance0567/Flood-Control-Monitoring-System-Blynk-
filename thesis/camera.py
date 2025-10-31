from picamera2 import Picamera2, Preview
import time

# Create camera object
picam2 = Picamera2()

# Start a GPU-accelerated preview window (same as rpicam-hello)
picam2.start_preview(Preview.QTGL)

# Start the camera
picam2.start()

# Keep preview open for 5 seconds
time.sleep(5)

# Stop and close
picam2.stop_preview()
picam2.close()