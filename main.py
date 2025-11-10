# main.py - Flood Control
import sys
import time
import requests
import subprocess
import signal
import os
import serial
import threading
import logging
from datetime import date, datetime
sys.path.append('/home/jesse/blynk-library-python')
from BlynkLib import Blynk
from captured_photos import handle_take_photo

BLYNK_AUTH = "wZ5IP73LpgMdLK1PDRnGEFBLHzDagQZq"

# --- Logging Configuration ---
LOG_DIR = "/home/jesse/Documents/FloodControl/logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Create logger
logger = logging.getLogger('FloodControl')
logger.setLevel(logging.INFO)

# File handler - logs to file with rotation
log_filename = os.path.join(LOG_DIR, f"flood_control_{datetime.now().strftime('%Y%m%d')}.log")
file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.INFO)

# Console handler - also print to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info("=" * 60)
logger.info("Flood Control System Starting")
logger.info("=" * 60)

# Initialize Blynk after logger
blynk = Blynk(BLYNK_AUTH)

# --- Global Variables ---
gunicorn_process = None
camera = None
streaming_active = False  # This should track V1 state changes
stream_thread = None

# --- Ultrasonic sensor thread module ---

# Set up the UART serial port for A02YYUW
try:
    ser = serial.Serial('/dev/serial0', 9600, timeout=1)
    logger.info("UART serial port initialized successfully on /dev/serial0")
except Exception as e:
    logger.error(f"Failed to initialize UART serial port: {e}")
    ser = None

def read_distance():
    while True:
        if ser is None:
            time.sleep(1)
            continue
        try:
            header = ser.read(9)
            if header and header[0] == 255:
                rest = ser.read(3)
                if len(rest) == 3:
                    dist = (rest[0] << 8) + rest[1]
                    return dist
        except Exception as e:
            logger.error(f"Error reading distance from sensor: {e}")
            print(f"Warning: measured distance {dist} mm is outside gauge range!")
            time.sleep(1)                

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
        work_dir = "/home/jesse/Documents/FloodControl"
        try:
            gunicorn_process = subprocess.Popen(
                [
                    "gunicorn", "-w", "1", "--threads", "4", "-b", "0.0.0.0:8000",
                    "--timeout", "3600", "--worker-class", "gthread", "combined_server:app"
                ],
                cwd=work_dir
            )
            logger.info(f"Gunicorn server started with PID: {gunicorn_process.pid}")
            print(f"Started Gunicorn with PID: {gunicorn_process.pid}")
        except Exception as e:
            logger.error(f"Failed to start Gunicorn: {e}")

def stop_gunicorn():
    global gunicorn_process
    if gunicorn_process and gunicorn_process.poll() is None:
        try:
            gunicorn_process.terminate()
            gunicorn_process.wait(timeout=3)
            logger.info("Gunicorn server stopped successfully")
            print("Stopped Gunicorn.")
        except subprocess.TimeoutExpired:
            logger.warning("Gunicorn did not stop gracefully, force killing")
            print("Force killing Gunicorn process.")
            gunicorn_process.kill()
        gunicorn_process = None
    else:
        logger.debug("Gunicorn was not running")
        print("Gunicorn not running.")
        
def start_camera_stream():
    try:
        r = requests.post('http://127.0.0.1:8000/control_camera', json={'action': 'start'}, timeout=2)
        logger.info(f"Camera stream start request: {r.text}")
        print(r.text)
    except Exception as e:
        logger.error(f"Error starting camera stream: {e}")
        print(f"Error starting camera stream: {e}")

def stop_camera_stream():
    try:
        r = requests.post('http://127.0.0.1:8000/control_camera', json={'action': 'stop'}, timeout=2)
        logger.info(f"Camera stream stop request: {r.text}")
        print(r.text)
    except Exception as e:
        logger.error(f"Error stopping camera stream: {e}")
        print(f"Error stopping camera stream: {e}")

@blynk.on("connected")
def blynk_connected(*args, **kwargs):   # Accepts any arguments
    logger.info("Raspberry Pi connected to Blynk cloud successfully")
    print("/ Raspberry Pi Connected to Blynk")
    blynk.virtual_write(0, 0)
    blynk.virtual_write(1, 0)
    blynk.virtual_write(5, 0)

# Take photo with conflict detection and auto-retry
@blynk.on("V0")
def on_v0(value):
    global camera, streaming_active
    val = int(value[0])
    
    if val == 1:
        print("V0: Take photo request received")
        
        # Check if V1 (live stream) is active
        if streaming_active or gunicorn_process is not None:
            logger.warning("V0: Camera conflict detected - live stream is active")
            logger.info("V0: Stopping live stream to free camera...")
            print("V0: Camera/stream is active (V1). Stopping stream first...")
            
            # Stop the live stream
            stop_camera_stream()
            time.sleep(1)  # Wait for camera to release
            stop_gunicorn()
            streaming_active = False
            
            # Turn off V1 in Blynk app
            blynk.virtual_write(1, 0)
            logger.info("V0: Live stream stopped, V1 reset to OFF")
            print("V0: Stream stopped. Waiting for camera to be ready...")
            time.sleep(2)  # Give camera time to fully release
        
        # Now take the photo
        try:
            from picamera2 import Picamera2
            camera = Picamera2()
            camera.configure(camera.create_preview_configuration(main={"size": (840, 560), "format": "RGB888"}))
            camera.start()
            logger.info("V0: Camera initialized and started")
            print("V0: Camera started, taking photo...")
            
            handle_take_photo(blynk, camera)
            logger.info("V0: Photo captured successfully")
            
            camera.stop()
            camera.close()
            camera = None
            print("V0: Photo taken successfully")
            
        except Exception as e:
            logger.error(f"V0: Error taking photo: {e}", exc_info=True)
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
        logger.info("V0: Button auto-reset to OFF")
        
    else:
        # V0 turned off manually
        if camera:
            camera.stop()
            camera.close()
            camera = None
            logger.info("V0: Camera manually released")
            print("V0: Camera released")
            
# Live cam and web server            
@blynk.on("V1")
def on_v1(value):
    global streaming_active
    val = int(value[0])
    
    if val == 1:
        logger.info("V1: Live stream button pressed (ON)")
        print("V1: Live stream request received")
        blynk.virtual_write(5, 0)
        streaming_active = True
        start_gunicorn()                  # This starts the Flask/Gunicorn process
        time.sleep(2)                     # Wait a little for Gunicorn to be live
        start_camera_stream()             # This tells Flask to create/start the camera
        blynk.set_property(1, "url", "https://pi.ustfloodcontrol.site/livecam")
        blynk.virtual_write(5, 1)
        logger.info("V1: Live stream started successfully")
        print("V1: Live stream started.")
    else:
        logger.info("V1: Live stream button pressed (OFF)")
        print("V1: Stop stream request received")
        streaming_active = False
        blynk.virtual_write(5, 0)
        stop_camera_stream()              # This tells Flask to stop & release the camera
        stop_gunicorn()                   # This kills the Gunicorn server
        logger.info("V1: Live stream stopped successfully")
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
    
     # Smoothing buffer for chart
    distance_buffer = []
    BUFFER_SIZE = 5  # Average last 5 readings
    
    warning_names = {0: "Safe", 1: "Yellow", 2: "Orange", 3: "Red"}
    event_codes = {
        1: "caution",
        2: "serious_situation", 
        3: "critical_level"
    }
    
    logger.info("Water level sensor monitoring thread started")
    
    while True:
        dist = read_distance()
        if dist is not None:
            # Buffer for smoothing
            distance_buffer.append(dist)
            if len(distance_buffer) > BUFFER_SIZE:
                distance_buffer.pop(0)
            
            # Use average for smoother chart
            smoothed_dist = sum(distance_buffer) // len(distance_buffer)
            
            inverted_value = 200 - smoothed_dist
            inverted_value = max(0, min(200, inverted_value))
            
            warning_img = map_distance_to_warning_image(smoothed_dist, last_warning)
            
            # Only send when values change
            if inverted_value != last_inverted:
                blynk.virtual_write(3, inverted_value)
                last_inverted = inverted_value
                logger.info(f"V3 (Gauge): Water level updated to {inverted_value} (distance: {dist}mm)")
                print(f"Gauge updated: {inverted_value}")
                
            if warning_img != last_warning:
                blynk.virtual_write(4, warning_img)
                logger.warning(f"V4 (Warning): Alert level changed from {warning_names[last_warning]} to {warning_names[warning_img]} (distance: {dist}mm)")
                last_warning = warning_img
                print(f"Warning updated: {warning_img}")
                
                # Send notification when entering yellow, orange, or red warning
                if warning_img in [1, 2, 3]:  # Yellow, Orange, or Red
                    try:
                        event_code = event_codes[warning_img]
                        warning_level = warning_names[warning_img]
                        message = f"Yawa Bridge is under {warning_level}"
                        
                        blynk.log_event(event_code, message)
                        logger.warning(f"Notification sent: {event_code} - {message}")
                        print(f"Notification sent: {warning_level}")
                    except Exception as e:
                        logger.error(f"Failed to send notification for warning level {warning_img}: {e}")
                        print(f"Error sending notification: {e}")
                
                # Take photo when entering yellow, orange, or red warning
                if warning_img in [1, 2, 3]:  # Yellow, Orange, or Red
                    today = date.today()
                    # Only take photo if we haven't taken one today for this level
                    if last_photo_dates[warning_img] != today:
                        logger.info(f"Auto-capture triggered for {warning_names[warning_img]} warning level")
                        print(f"Taking photo for warning level {warning_img}...")
                        try:
                            from captured_photos import capture_warning_photo
                            capture_warning_photo(warning_img)
                            last_photo_dates[warning_img] = today
                            logger.info(f"Warning photo captured successfully for {warning_names[warning_img]} level")
                        except Exception as e:
                            logger.error(f"Error capturing warning photo: {e}", exc_info=True)
                            print(f"Error capturing warning photo: {e}")
                
            print(f"Distance: {dist} mm ? Gauge: {inverted_value} | Warning: {warning_img}")
        else:
            logger.warning("No valid sensor data received from ultrasonic sensor")
            print("No valid sensor data received.")
        time.sleep(0.2)  # Changed from 0.2 to 1 second to reduce message usage
        
threading.Thread(target=update_water_level_sensor, args=(blynk,), daemon=True).start()
logger.info("Water level monitoring thread initialized")

try:
    logger.info("Entering main Blynk event loop")
    while True:
        blynk.run()
except KeyboardInterrupt:
    logger.info("Keyboard interrupt received, shutting down gracefully")
    if camera:
        camera.stop()
    if streaming_active:
        stop_camera_stream()
        stop_gunicorn()
    logger.info("Flood Control System stopped")
    print("Exiting cleanly.")
except Exception as e:
    logger.critical(f"Unexpected error in main loop: {e}", exc_info=True)
finally:
    logger.info("=" * 60)
    logger.info("Flood Control System Shutdown Complete")
    logger.info("=" * 60)