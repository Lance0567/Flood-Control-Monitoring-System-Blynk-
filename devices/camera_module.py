# camera_module.py
import os
import time
from picamera2 import Picamera2
import cv2

class PiCameraModule:
    def __init__(self, width=840, height=480):
        self.width = width
        self.height = height
        self.picam2 = Picamera2()
        self._configure_camera()
        self.picam2.start()
        print(" PiCameraModule initialized and started.")

    def _configure_camera(self):
        """Configure camera for RGB streaming."""
        config = self.picam2.create_preview_configuration(
            main={"size": (self.width, self.height), "format": "RGB888"}
        )
        self.picam2.configure(config)

    def start(self):
        # Camera is started during __init__, so this is a no-op
        print("PiCameraModule: start() called (already started)")

    def capture_frame(self):
        """Capture a single frame as a NumPy array."""
        return self.picam2.capture_array()

    def save_photo(self, folder='captured_images'):
        """Capture and save a single photo."""
        if not os.path.exists(folder):
            os.makedirs(folder)
        frame = self.capture_frame()
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        photo_path = os.path.join(folder, f"photo_{timestamp}.jpg")
        cv2.imwrite(photo_path, frame)
        return os.path.abspath(photo_path)

    def stop(self):
        """Stop the camera."""
        self.picam2.stop()
        print("Camera stopped.")
