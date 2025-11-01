import threading
import time
from flask import Flask, render_template_string, send_from_directory, request
import os

PHOTO_DIR = "/home/jesse/Documents/photos"
VIDEO_DIR = "/home/jesse/Documents/video"
app = Flask("combined_server")
server_thread = None
picam2 = None
recorder_running = False

@app.after_request
def add_cors_headers(response):
    # Allow Blynk widget/HLS.js/Video.js to access segments from any origin
    response.headers['Access-Control-Allow-Origin'] = '*'
    # Set correct Content-Type for .ts/.m3u8 files if not present
    if request.path.endswith('.m3u8'):
        response.headers['Content-Type'] = 'application/vnd.apple.mpegurl'
    elif request.path.endswith('.ts'):
        response.headers['Content-Type'] = 'video/mp2t'
    return response


@app.route('/photos')
def photo_index():
    files = sorted(os.listdir(PHOTO_DIR), reverse=True)
    if not files:
        return "<h3 style='text-align:center;'>No photos yet.</h3>"
    html = """
    <html>
    <head>
      <title>Captured Photos</title>
      <!-- Font Awesome for icons -->
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
      <style>
        body { text-align: center; font-family: Arial, sans-serif; background-color: #111; color: #eee; }
        img { width: 90%%; max-width: 640px; height: auto; border-radius: 10px; box-shadow: 0 0 15px #333; }
        .controls { margin-top: 20px; }
        button { padding: 10px 20px; font-size: 18px; border: none; border-radius: 8px; background: #28a745; color: white; margin: 0 10px; cursor: pointer; }
        button:hover { background: #218838; }
        h2 { color: #0dcaf0; }
        #counter { margin-top: 10px; color: #bbb; }
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
        function next() {
          idx = (idx + 1) % images.length;
          show();
        }
        function prev() {
          idx = (idx - 1 + images.length) % images.length;
          show();
        }
      </script>
    </body>
    </html>
    """
    return render_template_string(html, files=files)

@app.route('/photo/<path:filename>')
def serve_photo(filename):
    return send_from_directory(PHOTO_DIR, filename)

@app.route('/video/<path:filename>')
def serve_video(filename):
    # Segments (.ts) and playlist (.m3u8)
    return send_from_directory(VIDEO_DIR, filename)

def run_flask(camera_for_photos):
    app.run(host='0.0.0.0', port=80, debug=False, threaded=True)

def start_flask_server(input_camera):
    global server_thread
    if not server_thread or not server_thread.is_alive():
        server_thread = threading.Thread(target=run_flask, args=(input_camera,))
        server_thread.daemon = True
        server_thread.start()
    else:
        print("Flask server already running.")

def start_hls_stream():
    global picam2, recorder_running
    if recorder_running:
        print("HLS streaming already running.")
        return
    os.makedirs(VIDEO_DIR, exist_ok=True)
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder
    from picamera2.outputs import FfmpegOutput

    picam2 = Picamera2()
    video_config = picam2.create_video_configuration(main={"size": (640, 480)})
    picam2.configure(video_config)
    encoder = H264Encoder(bitrate=1000000)
    output = FfmpegOutput(
        "-f hls -hls_time 1 -hls_list_size 3 -hls_flags delete_segments " +
        os.path.join(VIDEO_DIR, "index.m3u8")
    )
    picam2.start_recording(encoder, output)
    recorder_running = True
    print("Started Picamera2 for HLS streaming.")

def stop_hls_stream():
    global picam2, recorder_running
    if picam2 and recorder_running:
        picam2.stop_recording()
        picam2 = None
        recorder_running = False
        print("Stopped Picamera2 HLS streaming.")