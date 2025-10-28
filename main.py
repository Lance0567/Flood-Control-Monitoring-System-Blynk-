import os
import cv2
import time
import threading
import sys
sys.path.append('/home/jesse/blynk-library-python')
from flask import Flask, Response, render_template_string, send_from_directory
from picamera2 import Picamera2
from BlynkLib import Blynk

BLYNK_AUTH = "wZ5IP73LpgMdLK1PDRnGEFBLHzDagQZq"
blynk = Blynk(BLYNK_AUTH)

# Initialize camera
camera = Picamera2()
camera.configure(camera.create_preview_configuration(main={"size": (840, 560), "format": "RGB888"}))
camera.start()

# Folder for photos
PHOTO_DIR = "/home/jesse/Documents/photos"
os.makedirs(PHOTO_DIR, exist_ok=True)

# Global state
photo_server = None
live_server = None
server_thread = None
stop_event = threading.Event()

# --- Flask app for photo slider ---
photo_app = Flask("photo_server")

@photo_app.route('/')
def photo_index():
    files = sorted(os.listdir(PHOTO_DIR), reverse=True)  # newest first
    if not files:
        return "<h3 style='text-align:center;'>No photos yet.</h3>"
    
    html = """
    <html>
    <head>
        <title>Captured Photos</title>
        <!-- Font Awesome for icons -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
        <style>
            body {
                text-align: center;
                font-family: Arial, sans-serif;
                background-color: #111;
                color: #eee;
            }
            img {
                width: 90%%;
                max-width: 640px;
                height: auto;
                border-radius: 10px;
                box-shadow: 0 0 15px #333;
            }
            .controls {
                margin-top: 20px;
            }
            button {
                padding: 10px 20px;
                font-size: 18px;
                border: none;
                border-radius: 8px;
                background: #28a745;
                color: white;
                margin: 0 10px;
                cursor: pointer;
            }
            button:hover {
                background: #218838;
            }
            h2 {
                color: #0dcaf0;
            }
            #counter {
                margin-top: 10px;
                color: #bbb;
            }
        </style>
    </head>
    <body>
        <h2><i class="fa-solid fa-camera"></i> Photo Viewer</h2>
        <img id="photo" src="/photo/{{ files[0] }}">
        <div class="controls">
            <button onclick="prev()"><i class="fa-solid fa-arrow-left"></i> Prev</button>
            <button onclick="next()">Next <i class="fa-solid fa-arrow-right"></i></button>
        </div>
        <p id="counter">1 / {{ files|length }}</p>

        <script>
            let images = {{ files|safe }};
            let idx = 0;
            function show() {
                document.getElementById('photo').src = '/photo/' + images[idx];
                document.getElementById('counter').innerText = (idx + 1) + " / " + images.length;
            }
            function next() { idx = (idx + 1) % images.length; show(); }
            function prev() { idx = (idx - 1 + images.length) % images.length; show(); }
        </script>
    </body>
    </html>
    """
    return render_template_string(html, files=files)

@photo_app.route('/photo/<path:filename>')
def serve_photo(filename):
    return send_from_directory(PHOTO_DIR, filename)

# --- Flask app for live streaming ---
live_app = Flask("live_server")

@live_app.route('/video')
def video_feed():
    def generate():
        while not stop_event.is_set():
            frame = camera.capture_array()
            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

def run_flask(app, port):
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

# --- BLYNK HANDLERS ---

@blynk.on("V0")
def handle_take_photo(value):
    global photo_server, server_thread
    val = int(value[0])
    if val == 1:
        # Capture photo
        frame = camera.capture_array()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        filename = f"photo_{time.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
        path = os.path.join(PHOTO_DIR, filename)

        # Add timestamp overlay
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, timestamp, (15, 460), font, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.imwrite(path, frame)
        print(f"?? Saved photo: {path}")

        # Start photo server
        if photo_server is None:
            print("?? Starting photo server on port 8080...")
            photo_server = photo_app
            server_thread = threading.Thread(target=run_flask, args=(photo_server, 8080))
            server_thread.daemon = True
            server_thread.start()
    else:
        print("?? V0 OFF - photo server still available for viewing.")

@blynk.on("V1")
def handle_live_stream(value):
    global live_server, server_thread, stop_event
    val = int(value[0])
    if val == 1:
        print("?? Starting live stream on port 8000...")
        stop_event.clear()
        live_server = live_app
        server_thread = threading.Thread(target=run_flask, args=(live_server, 8000))
        server_thread.daemon = True
        server_thread.start()
    else:
        print("?? Stopping live stream...")
        stop_event.set()

# --- MAIN LOOP ---
try:
    print("?? Blynk Camera Control Started")
    while True:
        blynk.run()
        time.sleep(0.1)
except KeyboardInterrupt:
    camera.stop()
    print("?? Exiting cleanly.")