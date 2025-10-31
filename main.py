#!/home/jesse/blynk_env/bin/python
import sys
import os
import time
sys.path.append('/home/jesse/blynk-library-python')

# --- ensure virtual environment for subprocesses ---
VENV_PYTHON = "/home/jesse/blynk_env/bin/python"

from BlynkLib import Blynk

BLYNK_AUTH = "wZ5IP73LpgMdLK1PDRnGEFBLHzDagQZq"
blynk = Blynk(BLYNK_AUTH)

# Connection confirmation
@blynk.on("connected")
def blynk_connected():
    print("/ Raspberry Pi Connected to Blynk")

# Local Flask server URLs
PHOTO_URL = "http://192.168.1.120:5000/photos"
VIDEO_URL = "http://192.168.1.120:5000/video"

# Flags to track status
photo_active = False
video_active = False

# ========== EVENT: Take Photo ==========
@blynk.on("V0")
def take_photo_handler(value):
    global photo_active
    val = int(value[0])
    if val == 1 and not photo_active:
        print("?? Photo server starting...")
        os.system("/home/jesse/Documents/FloodControl/captured_photos.py &")
        photo_active = True
    elif val == 0 and photo_active:
        print("?? Stopping photo server...")
        os.system("pkill -f captured_photos.py")
        os.system("pkill -f ngrok")
        photo_active = False

# ========== EVENT: Start Live Stream ==========
@blynk.on("V1")
def live_stream_handler(value):
    global video_active
    val = int(value[0])
    if val == 1 and not video_active:
        print("?? Video stream starting...")
        os.system("python3 /home/jesse/Documents/FloodControl/camera_live.py &")
        video_active = True
    elif val == 0 and video_active:
        print("?? Stopping live stream...")
        os.system("pkill -f camera_live.py")
        os.system("pkill -f ngrok")
        video_active = False

# ========== MAIN LOOP ==========
while True:
    blynk.run()
    time.sleep(0.1)