import os
import cv2
import time

PHOTO_DIR = "/home/jesse/Documents/photos"
def handle_take_photo(blynk, camera):
    os.makedirs(PHOTO_DIR, exist_ok=True)
    frame = camera.capture_array()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    filename = f"photo_{time.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
    path = os.path.join(PHOTO_DIR, filename)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, timestamp, (15, 460), font, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imwrite(path, frame)
    print(f"Saved photo: {path}")
    time.sleep(1)
    blynk.virtual_write(0, 0)
