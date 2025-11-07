# captured_photos.py
import os
import cv2
import time

PHOTO_DIR = "/home/jesse/Documents/photos"

def handle_take_photo(blynk, camera):
    os.makedirs(PHOTO_DIR, exist_ok=True)
    frame = camera.capture_array()
    timestamp = time.strftime("%m/%d/%Y %I:%M %p")
    filename = f"photo_{time.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
    path = os.path.join(PHOTO_DIR, filename)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, timestamp, (15, 460), font, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imwrite(path, frame)
    print(f"Saved photo: {path}")
    time.sleep(1)
    blynk.virtual_write(0, 0)

def capture_warning_photo(warning_level):
    """Capture photo for warning level (yellow=1, orange=2, red=3)."""
    from picamera2 import Picamera2
    
    # Map warning level to folder name
    level_names = {1: "yellow", 2: "orange", 3: "red"}
    if warning_level not in level_names:
        return
    
    folder_name = level_names[warning_level]
    photo_dir = f"/home/jesse/Documents/photos/{folder_name}"
    os.makedirs(photo_dir, exist_ok=True)
    
    # Initialize camera
    camera = Picamera2()
    camera.configure(camera.create_preview_configuration(main={"size": (840, 560), "format": "RGB888"}))
    camera.start()
    time.sleep(0.5)  # Let camera warm up
    
    # Capture frame
    frame = camera.capture_array()
    timestamp = time.strftime("%m/%d/%Y %I:%M %p")
    filename = f"{folder_name}_warning_{time.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
    path = os.path.join(photo_dir, filename)
    
    # Add timestamp overlay
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, timestamp, (15, 460), font, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imwrite(path, frame)
    
    # Clean up
    camera.stop()
    camera.close()
    
    print(f"Warning photo saved: {path}")
