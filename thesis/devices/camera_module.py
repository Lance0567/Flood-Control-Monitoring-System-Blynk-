# camera_module.py
from picamera2 import Picamera2

class PiCameraModule:
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.picam2 = Picamera2()
        self._configure_camera()
        print("? PiCameraModule initialized.")

    def _configure_camera(self):
        config = self.picam2.create_preview_configuration(
            main={"size": (self.width, self.height), "format": "RGB888"}
        )
        self.picam2.configure(config)

    def start(self):
        """Start the camera."""
        self.picam2.start()
        print("?? Camera started.")

    def capture_frame(self):
        """Capture a single frame as a NumPy array."""
        return self.picam2.capture_array()

    def stop(self):
        """Stop the camera."""
        self.picam2.stop()
        print("?? Camera stopped.")