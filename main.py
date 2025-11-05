# main.py - Flood Control
import sys
import time
import requests
import subprocess
import signal
import os
sys.path.append('/home/jesse/blynk-library-python')
from BlynkLib import Blynk
from captured_photos import handle_take_photo

BLYNK_AUTH = "wZ5IP73LpgMdLK1PDRnGEFBLHzDagQZq"
blynk = Blynk(BLYNK_AUTH)

gunicorn_process = None

def start_gunicorn():
    global gunicorn_process
    if gunicorn_process is None or gunicorn_process.poll() is not None:
        # Path to your project folder
        work_dir = "/home/jesse/Documents/FloodControl"
        gunicorn_process = subprocess.Popen(
            [
                "gunicorn", "-w", "1", "--threads", "4", "-b", "0.0.0.0:8000",
                "--timeout", "3600", "--worker-class", "gthread", "combined_server:app"
            ],
            cwd=work_dir
        )
        print(f"Started Gunicorn with PID: {gunicorn_process.pid}")

def stop_gunicorn():
    global gunicorn_process
    if gunicorn_process and gunicorn_process.poll() is None:
        gunicorn_process.terminate()
        try:
            gunicorn_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("Force killing Gunicorn process.")
            gunicorn_process.kill()
        print("Stopped Gunicorn.")
        gunicorn_process = None
    else:
        print("Gunicorn not running.")
        
def start_camera_stream():
    try:
        r = requests.post('http://127.0.0.1:8000/control_camera', json={'action': 'start'})
        print(r.text)
    except Exception as e:
        print(f"Error starting camera stream: {e}")

def stop_camera_stream():
    try:
        r = requests.post('http://127.0.0.1:8000/control_camera', json={'action': 'stop'})
        print(r.text)
    except Exception as e:
        print(f"Error stopping camera stream: {e}")        

camera = None
streaming_active = False  # This should track V1 state changes
stream_thread = None

@blynk.on("connected")
def blynk_connected(*args, **kwargs):   # Accepts any arguments
    print("/ Raspberry Pi Connected to Blynk")
    blynk.set_property(1, "url", "https://pi.ustfloodcontrol.site/video/index.m3u8")

@blynk.on("V0")
def on_v0(value):
    global camera, streaming_active
    val = int(value[0])
    if val == 1:
        if streaming_active:
            stop_hls_stream()
            stop_flask_server()
            streaming_active = False
            blynk.virtual_write(1, 0)
        from picamera2 import Picamera2
        camera = Picamera2()
        camera.configure(camera.create_preview_configuration(main={"size": (840, 560), "format": "RGB888"}))
        camera.start()
        handle_take_photo(blynk, camera)
        camera.stop()
        camera.close()
        camera = None
    else:
        if camera:
            camera.stop()
            camera.close()
            camera = None
            
# Then in your V1 handler:
@blynk.on("V1")
def on_v1(value):
    val = int(value[0])
    if val == 1:
        start_gunicorn()                  # This starts the Flask/Gunicorn process
        time.sleep(2)                     # Wait a little for Gunicorn to be live (optional but helps)
        start_camera_stream()             # This tells Flask to create/start the camera
        print("Live stream started.")
    else:
        stop_camera_stream()              # This tells Flask to stop & release the camera
        stop_gunicorn()                   # This kills the Gunicorn server
        print("Live stream stopped.")

try:
    while True:
        blynk.run()
except KeyboardInterrupt:
    if camera:
        camera.stop()
    print("Exiting cleanly.")
