# main.py - Flood Control
import sys
import time
import requests
import subprocess
import signal
import os
import serial
import threading
from datetime import date
sys.path.append('/home/jesse/blynk-library-python')
from BlynkLib import Blynk
from captured_photos import handle_take_photo

BLYNK_AUTH = "wZ5IP73LpgMdLK1PDRnGEFBLHzDagQZq"
blynk = Blynk(BLYNK_AUTH)

gunicorn_process = None
camera = None
streaming_active = False  # This should track V1 state changes
stream_thread = None

# --- Ultrasonic sensor thread module ---

# Set up the UART serial port for A02YYUW
ser = serial.Serial('/dev/serial0', 9600, timeout=1)

def read_distance():
    while True:
        header = ser.read(9)
        if header and header[0] == 255:
            rest = ser.read(3)
            if len(rest) == 3:
                dist = (rest[0] << 8) + rest[1]
                # Optionally sanity-check within your min/max
                if 0 <= dist <= 100:
                    return dist
                else:
                    # Print warning if value is out-of-bounds for your gauge
                    print(f"Warning: measured distance {dist} mm is outside gauge range!")
                    return dist

# Gauge widget
def map_distance_to_flood_level(distance):
    """Map water distance in mm to a flood warning level for Blynk."""
    if distance is None:
        return None
    if 150 <= distance <= 200:
        return 0  # No warning
    elif 90 <= distance <= 140:
        return 1  # Yellow warning
    elif 40 <= distance <= 80:
        return 2  # Orange warning
    elif 0 <= distance <= 30:
        return 3  # Red warning
    else:
        return 0  # Optional: treat out-of-bounds as 'No warning'
    
# Status widget    
def map_distance_to_warning_image(distance, current_warning):
    """Map water distance to warning image with hysteresis to prevent flickering."""
    if distance is None:
        return current_warning  # Keep current state if no reading
    
    # When moving to higher warning (water rising - distance decreasing)
    if distance <= 25:  # Enter Red (was 0-30)
        return 3
    elif distance <= 35 and current_warning == 3:  # Stay in Red until 35mm
        return 3
    elif distance <= 75:  # Enter Orange (was 40-80)
        return 2
    elif distance <= 85 and current_warning == 2:  # Stay in Orange until 85mm
        return 2
    elif distance <= 135:  # Enter Yellow (was 90-140)
        return 1
    elif distance <= 145 and current_warning == 1:  # Stay in Yellow until 145mm
        return 1
    else:  # Safe zone (150-200)
        return 0

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
            gunicorn_process.wait(timeout=3)
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

@blynk.on("connected")
def blynk_connected(*args, **kwargs):   # Accepts any arguments
    print("/ Raspberry Pi Connected to Blynk")
    blynk.set_property(1, "url", "https://pi.ustfloodcontrol.site/livecam")

# Take photo with conflict detection and auto-retry
@blynk.on("V0")
def on_v0(value):
    global camera, streaming_active
    val = int(value[0])
    
    if val == 1:
        print("V0: Take photo request received")
        
        # Check if V1 (live stream) is active
        if streaming_active or gunicorn_process is not None:
            print("V0: Camera/stream is active (V1). Stopping stream first...")
            
            # Stop the live stream
            stop_camera_stream()
            time.sleep(1)  # Wait for camera to release
            stop_gunicorn()
            streaming_active = False
            
            # Turn off V1 in Blynk app
            blynk.virtual_write(1, 0)
            print("V0: Stream stopped. Waiting for camera to be ready...")
            time.sleep(2)  # Give camera time to fully release
        
        # Now take the photo
        try:
            from picamera2 import Picamera2
            camera = Picamera2()
            camera.configure(camera.create_preview_configuration(main={"size": (840, 560), "format": "RGB888"}))
            camera.start()
            print("V0: Camera started, taking photo...")
            
            handle_take_photo(blynk, camera)
            
            camera.stop()
            camera.close()
            camera = None
            print("V0: Photo taken successfully")
            
        except Exception as e:
            print(f"V0: Error taking photo: {e}")
            if camera:
                try:
                    camera.stop()
                    camera.close()
                except:
                    pass
                camera = None
        
        # Auto-reset V0 button
        time.sleep(0.5)
        blynk.virtual_write(0, 0)
        
    else:
        # V0 turned off manually
        if camera:
            camera.stop()
            camera.close()
            camera = None
            print("V0: Camera released")
            
# Live cam and web server            
@blynk.on("V1")
def on_v1(value):
    global streaming_active
    val = int(value[0])
    
    if val == 1:
        print("V1: Live stream request received")
        streaming_active = True
        start_gunicorn()                  # This starts the Flask/Gunicorn process
        time.sleep(2)                     # Wait a little for Gunicorn to be live
        start_camera_stream()             # This tells Flask to create/start the camera
        print("V1: Live stream started.")
    else:
        print("V1: Stop stream request received")
        streaming_active = False
        stop_camera_stream()              # This tells Flask to stop & release the camera
        stop_gunicorn()                   # This kills the Gunicorn server
        print("V1: Live stream stopped.")
               
# Water level sensor        
def update_water_level_sensor(blynk):
    last_inverted = None
    last_warning = 0  # Start with safe state
    
    # Track last photo date for each warning level
    last_photo_dates = {
        1: None,  # Yellow
        2: None,  # Orange
        3: None   # Red
    }
    
    while True:
        dist = read_distance()
        if dist is not None:
            # Invert for gauge
            inverted_value = 200 - dist
            inverted_value = max(0, min(200, inverted_value))
            
            # Get warning with hysteresis (pass current state)
            warning_img = map_distance_to_warning_image(dist, last_warning)
            
            # Only send when values change
            if inverted_value != last_inverted:
                blynk.virtual_write(3, inverted_value)
                last_inverted = inverted_value
                print(f"Gauge updated: {inverted_value}")
                
            if warning_img != last_warning:
                blynk.virtual_write(4, warning_img)
                last_warning = warning_img
                print(f"Warning updated: {warning_img}")
                
                # Take photo when entering yellow, orange, or red warning
                if warning_img in [1, 2, 3]:  # Yellow, Orange, or Red
                    today = date.today()
                    # Only take photo if we haven't taken one today for this level
                    if last_photo_dates[warning_img] != today:
                        print(f"Taking photo for warning level {warning_img}...")
                        try:
                            from captured_photos import capture_warning_photo
                            capture_warning_photo(warning_img)
                            last_photo_dates[warning_img] = today
                        except Exception as e:
                            print(f"Error capturing warning photo: {e}")
                
            print(f"Distance: {dist} mm ? Gauge: {inverted_value} | Warning: {warning_img}")
        else:
            print("No valid sensor data received.")
        time.sleep(0.2)  # Changed from 0.2 to 1 second to reduce message usage
        
threading.Thread(target=update_water_level_sensor, args=(blynk,), daemon=True).start()        

try:
    while True:
        blynk.run()
except KeyboardInterrupt:
    if camera:
        camera.stop()
    print("Exiting cleanly.")
